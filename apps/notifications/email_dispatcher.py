import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)


def _html_body(title: str, message: str, recipient_name: str) -> str:
    nombre = recipient_name or "Cliente"
    parrafos = "".join(f"<p>{p.strip()}</p>" for p in message.split("\n") if p.strip())
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">
        <!-- Header -->
        <tr>
          <td style="background:#003049;padding:24px 32px;">
            <span style="color:#ffffff;font-size:18px;font-weight:700;letter-spacing:1px;">CHECKAR CDA</span>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 16px;font-size:16px;color:#1a202c;">Hola, <strong>{nombre}</strong></p>
            <h2 style="margin:0 0 20px;font-size:18px;color:#1a202c;line-height:1.4;">{title}</h2>
            <div style="font-size:15px;color:#4a5568;line-height:1.7;">{parrafos}</div>
          </td>
        </tr>
        <!-- CTA -->
        <tr>
          <td style="padding:0 32px 32px;">
            <a href="http://localhost:5173/cliente"
               style="display:inline-block;background:#003049;color:#ffffff;text-decoration:none;
                      padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;">
              Ver mis revisiones
            </a>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px;border-top:1px solid #e2e8f0;">
            <p style="margin:0;font-size:12px;color:#718096;">
              Este correo fue enviado automáticamente por Checkar CDA.
              Si no deseas recibir estos avisos, comunícate con nosotros.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def dispatch_pending_emails(batch_size: int = 50) -> tuple[int, int]:
    """
    Lee Notification(channel='email', status='pending') y envía cada una.
    Devuelve (enviadas, fallidas).
    """
    from apps.notifications.models import Notification

    pending = (
        Notification.objects
        .filter(channel="email", status="pending")
        .select_related("user")[:batch_size]
    )

    sent = 0
    failed = 0

    for notif in pending:
        recipient_email = notif.user.email
        if not recipient_email:
            notif.status = "failed"
            notif.save(update_fields=["status", "updated_at"])
            failed += 1
            continue

        recipient_name = f"{notif.user.first_name} {notif.user.last_name}".strip()
        plain_text = notif.message
        html_content = _html_body(notif.title, plain_text, recipient_name)

        try:
            email = EmailMultiAlternatives(
                subject=notif.title,
                body=plain_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            notif.status = "sent"
            notif.save(update_fields=["status", "updated_at"])
            sent += 1

        except Exception as exc:
            logger.error("Fallo al enviar email para notificacion %s: %s", notif.id, exc)
            notif.status = "failed"
            notif.save(update_fields=["status", "updated_at"])
            failed += 1

    return sent, failed
