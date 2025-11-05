from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Tuple

from django.db import transaction
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from jinja2 import TemplateError

from unicrm.models import Communication, CommunicationMessage, Contact
from unicrm.services.template_renderer import (
    render_template_for_contact,
    get_jinja_environment,
    unprotect_tinymce_markup,
)


@dataclass
class CommunicationPreparationResult:
    communication: Communication
    created: int
    updated: int
    skipped: int
    errors: list[str]


@dataclass
class DeliveryPreparationOutcome:
    delivery: CommunicationMessage
    created: bool
    updated: bool
    skipped: bool
    errors: list[str]


def _render_subject(subject_template: str, context: dict) -> Tuple[str, list[str]]:
    """
    Render the subject template with the provided context.
    """
    if not subject_template:
        return '', []
    template_string = unprotect_tinymce_markup(subject_template)
    env = get_jinja_environment()
    errors: list[str] = []
    try:
        template = env.from_string(template_string)
        subject = template.render(context)
    except TemplateError as exc:
        subject = subject_template
        errors.append(str(exc))
    return subject.strip(), errors


def _eligible_contacts(communication: Communication) -> Iterable[Contact]:
    """
    Returns contacts matching the segment; filtering for email happens downstream.
    """
    return communication.segment.apply()


def _append_error(metadata: dict, message: str) -> None:
    errors = metadata.setdefault('errors', [])
    if message not in errors:
        errors.append(message)


def _persist_delivery(delivery: CommunicationMessage, update_fields: Iterable[str] | None = None) -> None:
    """
    Save helper that handles newly created and existing deliveries consistently.
    """
    if delivery.pk is None:
        delivery.save()
        return

    if not update_fields:
        delivery.save()
        return

    fields = list(dict.fromkeys(list(update_fields) + ['updated_at']))
    delivery.save(update_fields=fields)


def _prepare_delivery_for_contact(
    communication: Communication,
    contact: Contact,
    *,
    send_at,
    existing: CommunicationMessage | None = None,
    allow_resend_sent: bool = False,
) -> DeliveryPreparationOutcome:
    """
    Creates or refreshes a CommunicationMessage for the given contact.
    """
    if not communication.channel:
        raise ValueError("Communication must define a channel before generating drafts.")

    subject_template = communication.subject_template or f"Communication {communication.pk}"
    errors: list[str] = []

    with transaction.atomic():
        if existing is not None:
            delivery = (
                CommunicationMessage.objects
                .select_for_update(skip_locked=True)
                .select_related('contact')
                .get(pk=existing.pk)
            )
            created_delivery = False
        else:
            try:
                delivery = (
                    CommunicationMessage.objects
                    .select_for_update(skip_locked=True)
                    .select_related('contact')
                    .get(communication=communication, contact=contact)
                )
                created_delivery = False
            except CommunicationMessage.DoesNotExist:
                delivery = CommunicationMessage(
                    communication=communication,
                    contact=contact,
                    metadata={},
                )
                created_delivery = True

        metadata = delivery.metadata or {}
        current_status = (delivery.status or str(metadata.get('status') or '')).lower()

        if current_status == 'sent' and not allow_resend_sent:
            return DeliveryPreparationOutcome(delivery, False, False, True, errors)

        if not contact.email:
            _append_error(metadata, 'No email address on contact.')
            metadata['status'] = 'skipped'
            delivery.metadata = metadata
            delivery.status = 'skipped'
            delivery.scheduled_at = send_at
            _persist_delivery(delivery, ['metadata', 'status', 'scheduled_at'])
            return DeliveryPreparationOutcome(delivery, created_delivery, False, True, errors)

        if getattr(contact, 'email_bounced', False):
            _append_error(metadata, 'Previous delivery bounced; contact suppressed.')
            metadata['status'] = 'bounced'
            delivery.metadata = metadata
            delivery.status = 'bounced'
            delivery.scheduled_at = send_at
            _persist_delivery(delivery, ['metadata', 'status', 'scheduled_at'])
            return DeliveryPreparationOutcome(delivery, created_delivery, False, True, errors)

        render_result = render_template_for_contact(
            communication.get_renderable_content(),
            contact=contact,
            communication=communication,
        )

        subject, subject_errors = _render_subject(subject_template, render_result.context)
        errors.extend(subject_errors)
        for err in render_result.errors:
            _append_error(metadata, err)
        errors.extend(render_result.errors)

        payload = {
            'to': [contact.email],
            'subject': subject or subject_template or f"Communication {communication.pk}",
            'html': render_result.html,
        }

        metadata['status'] = 'scheduled'
        metadata['send_at'] = send_at.isoformat()
        metadata['payload'] = payload
        metadata['variables'] = json.loads(json.dumps(render_result.variables, cls=DjangoJSONEncoder))
        metadata['context'] = json.loads(json.dumps(render_result.context, cls=DjangoJSONEncoder))

        delivery.metadata = metadata
        delivery.status = 'scheduled'
        delivery.scheduled_at = send_at
        _persist_delivery(delivery, ['metadata', 'status', 'scheduled_at'])

        return DeliveryPreparationOutcome(
            delivery=delivery,
            created=created_delivery,
            updated=not created_delivery,
            skipped=False,
            errors=errors,
        )


def ensure_delivery_for_contact(
    communication: Communication,
    contact: Contact,
    *,
    send_at=None,
) -> DeliveryPreparationOutcome:
    """
    Public helper to guarantee a single contact has an up-to-date draft.
    """
    actual_send_at = send_at or communication.scheduled_for or timezone.now()
    outcome = _prepare_delivery_for_contact(
        communication,
        contact,
        send_at=actual_send_at,
    )
    if communication.scheduled_for is None:
        communication.scheduled_for = actual_send_at
        communication.save(update_fields=['scheduled_for', 'updated_at'])
    communication.refresh_status_summary()
    return outcome


def refresh_delivery_for_sending(
    delivery: CommunicationMessage,
    *,
    send_at=None,
) -> DeliveryPreparationOutcome:
    """
    Refresh an existing delivery before attempting to send it.
    """
    communication = delivery.communication
    target_send_at = (
        send_at
        or delivery.scheduled_at
        or communication.scheduled_for
        or timezone.now()
    )
    return _prepare_delivery_for_contact(
        communication,
        delivery.contact,
        send_at=target_send_at,
        existing=delivery,
    )


def generate_drafts_for_communication(communication: Communication) -> CommunicationPreparationResult:
    """
    Prepares per-contact payloads for the provided communication.
    """
    if not communication.channel:
        raise ValueError("Communication must define a channel before generating drafts.")

    contacts_source = _eligible_contacts(communication)
    contacts = (
        contacts_source.iterator()
        if hasattr(contacts_source, 'iterator')
        else contacts_source
    )
    send_at = communication.scheduled_for or timezone.now()
    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for contact in contacts:
        outcome = _prepare_delivery_for_contact(
            communication,
            contact,
            send_at=send_at,
        )
        if outcome.created:
            created += 1
        elif outcome.updated and not outcome.skipped:
            updated += 1
        if outcome.skipped:
            skipped += 1
        errors.extend(outcome.errors)

    updates: list[str] = []
    if communication.scheduled_for != send_at:
        communication.scheduled_for = send_at
        updates.append('scheduled_for')
    if updates:
        communication.save(update_fields=updates + ['updated_at'])
    communication.refresh_status_summary()

    return CommunicationPreparationResult(
        communication=communication,
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )
