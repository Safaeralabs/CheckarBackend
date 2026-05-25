from django.conf import settings
from django.core.mail import send_mail


FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:5173")


def send_welcome_email(user, initial_password: str):
    """
    Envía credenciales de acceso a un cliente recién creado por un operador (walk-in).
    """
    if not user.email:
        return

    name = f"{user.first_name} {user.last_name}".strip() or user.username
    subject = "Bienvenido a Checkar — Acceso a tu portal de inspecciones"
    message = f"""Hola {name},

El CDA Checkar ha creado tu cuenta para que puedas hacer seguimiento a la inspección de tu vehículo.

Tus credenciales de acceso son:
  Portal:     {FRONTEND_URL}/login
  Usuario:    {user.username}
  Contraseña: {initial_password}

Te recomendamos cambiar tu contraseña después de ingresar.

Si tienes alguna duda, comunícate con nosotros en el CDA.

— Equipo Checkar CDA
  Calle 15 No. 12B–44 · Riohacha, La Guajira
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_internal_user_credentials_email(user, temp_password: str):
    """
    Envía credenciales temporales a un usuario interno recién creado por el admin.
    """
    if not user.email:
        return

    name = f"{user.first_name} {user.last_name}".strip() or user.username
    subject = "Tu acceso a Checkar CDA — Credenciales temporales"
    message = f"""Hola {name},

El administrador de Checkar CDA ha creado tu cuenta con el siguiente rol: {user.role}.

Tus credenciales de acceso temporales son:
  Portal:     {FRONTEND_URL}/login
  Usuario:    {user.username}
  Contraseña: {temp_password}

Al ingresar por primera vez, el sistema te pedirá que cambies tu contraseña.

— Equipo Checkar CDA
  Calle 15 No. 12B–44 · Riohacha, La Guajira
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_signature_request_email(user, reception):
    """
    Notifica al cliente que el operador solicitó su firma para la recepción del vehículo.
    """
    if not user.email:
        return

    name = f"{user.first_name} {user.last_name}".strip() or user.username
    plate = reception.appointment.vehicle.plate.upper()
    sign_url = f"{FRONTEND_URL}/cliente/firmar/{reception.id}"

    subject = f"Firma requerida — Recepción de tu vehículo {plate} en Checkar CDA"
    message = f"""Hola {name},

El CDA Checkar ha preparado la recepción de tu vehículo {plate}.

Para que la inspección pueda comenzar, necesitamos tu firma digital autorizando el proceso.

Por favor ingresa al siguiente enlace para revisar los datos y firmar:
  {sign_url}

Si no tienes sesión activa, usa tus credenciales:
  Portal:   {FRONTEND_URL}/login
  Usuario:  {user.username}

— Equipo Checkar CDA
  Calle 15 No. 12B–44 · Riohacha, La Guajira
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
