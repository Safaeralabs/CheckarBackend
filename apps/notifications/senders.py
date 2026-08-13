import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def resolve_recipients_queryset(channel, filters):
    """
    Devuelve el queryset de clientes que califican para una campaña,
    según el canal (necesitan email o teléfono) y filtros opcionales.
    """
    from apps.accounts.models import User

    qs = User.objects.filter(role="customer")

    city = (filters or {}).get("city")
    if city:
        qs = qs.filter(customer_profile__city__iexact=city)

    if channel == "email":
        qs = qs.exclude(email="")
    else:
        qs = qs.exclude(phone="")

    return qs


def build_campaign_recipients(campaign):
    """
    Genera (o regenera) la lista de destinatarios de la campaña a partir de
    sus filtros, como snapshot de CampaignRecipient.
    """
    from .models import CampaignRecipient

    qs = resolve_recipients_queryset(campaign.channel, campaign.filters)
    CampaignRecipient.objects.filter(campaign=campaign).delete()

    objs = [
        CampaignRecipient(campaign=campaign, user=u, email=u.email, phone=u.phone)
        for u in qs
    ]
    CampaignRecipient.objects.bulk_create(objs, ignore_conflicts=True)

    campaign.recipients_count = len(objs)
    campaign.save(update_fields=["recipients_count", "updated_at"])
    return campaign.recipients_count


def _campaign_html_body(subject: str, message: str) -> str:
    parrafos = "".join(f"<p>{p.strip()}</p>" for p in message.split("\n") if p.strip())
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">
        <tr>
          <td style="background:#003049;padding:24px 32px;">
            <span style="color:#ffffff;font-size:18px;font-weight:700;letter-spacing:1px;">CHECKAR CDA</span>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 16px;font-size:16px;color:#1a202c;">Hola, <strong>{{{{nombre}}}}</strong></p>
            <h2 style="margin:0 0 20px;font-size:18px;color:#1a202c;line-height:1.4;">{subject}</h2>
            <div style="font-size:15px;color:#4a5568;line-height:1.7;">{parrafos}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px;border-top:1px solid #e2e8f0;">
            <p style="margin:0;font-size:12px;color:#718096;">
              Este correo es una comunicación de Checkar CDA.
              Si no deseas recibir estos avisos, comunícate con nosotros.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_campaign_email(campaign, batch_size: int = 500):
    """
    Envía la campaña de email vía SendGrid Web API, en lotes de personalizations.
    Devuelve (enviados, fallidos).
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Content, Email, Mail, Personalization, Substitution, To

    from .models import CampaignRecipient

    recipients = list(campaign.campaign_recipients.filter(status="pending").exclude(email=""))
    if not recipients:
        return 0, 0

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    html_body = _campaign_html_body(campaign.subject, campaign.message)

    sent = 0
    failed = 0

    for i in range(0, len(recipients), batch_size):
        chunk = recipients[i:i + batch_size]

        message = Mail(from_email=Email(settings.SENDGRID_FROM_EMAIL))
        message.subject = campaign.subject
        message.add_content(Content("text/plain", campaign.message))
        message.add_content(Content("text/html", html_body))

        for r in chunk:
            nombre = (
                f"{r.user.first_name} {r.user.last_name}".strip() if r.user else ""
            ) or "Cliente"
            personalization = Personalization()
            personalization.add_to(To(r.email))
            personalization.add_substitution(Substitution("{{nombre}}", nombre))
            message.add_personalization(personalization)

        chunk_ids = [r.id for r in chunk]
        try:
            response = sg.client.mail.send.post(request_body=message.get())
            if response.status_code in (200, 202):
                CampaignRecipient.objects.filter(id__in=chunk_ids).update(
                    status="sent", sent_at=timezone.now()
                )
                sent += len(chunk)
            else:
                CampaignRecipient.objects.filter(id__in=chunk_ids).update(
                    status="failed", error_message=f"SendGrid HTTP {response.status_code}"
                )
                failed += len(chunk)
        except Exception as exc:
            logger.error("Fallo al enviar lote de campaña %s vía SendGrid: %s", campaign.id, exc)
            CampaignRecipient.objects.filter(id__in=chunk_ids).update(
                status="failed", error_message=str(exc)[:500]
            )
            failed += len(chunk)

    return sent, failed


def send_campaign_sms(campaign):
    """
    Envía la campaña de SMS vía Twilio, un mensaje por destinatario
    (Twilio no ofrece envío masivo en una sola llamada).
    Devuelve (enviados, fallidos).
    """
    from twilio.base.exceptions import TwilioException
    from twilio.rest import Client

    recipients = campaign.campaign_recipients.filter(status="pending").exclude(phone="")
    if not recipients.exists():
        return 0, 0

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    sent = 0
    failed = 0

    for r in recipients:
        try:
            twilio_msg = client.messages.create(
                body=campaign.message,
                from_=settings.TWILIO_FROM_NUMBER,
                to=r.phone,
            )
            r.status = "sent"
            r.provider_message_id = twilio_msg.sid
            r.sent_at = timezone.now()
            r.save(update_fields=["status", "provider_message_id", "sent_at", "updated_at"])
            sent += 1
        except TwilioException as exc:
            logger.error("Fallo al enviar SMS de campaña %s a %s: %s", campaign.id, r.phone, exc)
            r.status = "failed"
            r.error_message = str(exc)[:500]
            r.save(update_fields=["status", "error_message", "updated_at"])
            failed += 1

    return sent, failed


def send_campaign(campaign):
    """
    Punto de entrada único: construye destinatarios si hace falta y despacha
    la campaña según su canal.
    """
    if campaign.recipients_count == 0:
        build_campaign_recipients(campaign)

    campaign.status = "sending"
    campaign.save(update_fields=["status", "updated_at"])

    if campaign.channel == "email":
        sent, failed = send_campaign_email(campaign)
    else:
        sent, failed = send_campaign_sms(campaign)

    campaign.sent_count = sent
    campaign.failed_count = failed
    campaign.status = "sent" if sent > 0 else "failed"
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=["sent_count", "failed_count", "status", "sent_at", "updated_at"])

    return sent, failed
