"""
Módulo: utils/email.py
Descripción: Utilidades para el envío de emails transaccionales (verificación + recuperación).
¿Para qué? Proveer funciones reutilizables para:
           1. Verificación de email al registrarse (nuevo usuario).
           2. Recuperación de contraseña (enlace de reset).
¿Impacto? Sin este módulo, los flujos de verificación y recuperación no pueden notificar
          al usuario.

Backend de email — orden de prioridad:
  1. SMTP_HOST configurado → usa smtplib (stdlib) — ideal para Mailpit en desarrollo.
  2. RESEND_API_KEY configurado → usa la API de Resend.
  3. Ninguno → simula en logs (el enlace aparece en consola para testing manual).

Mailpit — probar emails localmente sin cuenta ni dominio:
  Con Docker Compose: el servicio mailpit arranca automáticamente junto al backend.
  Web UI: http://localhost:8025 — todos los emails enviados aparecen ahí en tiempo real.
"""

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import resend

from app.config import settings

# ¿Qué? Logger para registrar eventos de envío (éxito, error, modo simulado).
# ¿Para qué? Depurar problemas de envío sin exponer el contenido del email en logs.
# ¿Impacto? En desarrollo, el enlace de verificación aparece aquí si no hay API key.
logger = logging.getLogger(__name__)


def _send_email_sync(params: resend.Emails.SendParams) -> None:
    """Ejecuta el envío de email de forma síncrona usando el SDK de Resend.

    ¿Qué? Función auxiliar que configura la API key y llama a resend.Emails.send().
    ¿Para qué? Centralizar la configuración de Resend y separar el envío real de la lógica.
              Se usa internamente desde las funciones async vía asyncio.to_thread().
    ¿Impacto? resend.Emails.send() es síncrono — correrlo directo en un async endpoint
              bloquearía el event loop. asyncio.to_thread() lo ejecuta en un thread pool.

    Args:
        params: Parámetros del email (from, to, subject, html).
    """
    # ¿Qué? Establece la API key de Resend antes de cada envío.
    # ¿Para qué? El SDK de Resend requiere que resend.api_key esté configurada.
    # ¿Impacto? Es seguro hacerlo aquí ya que settings.RESEND_API_KEY es inmutable en runtime.
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send(params)


def _send_email_smtp(to_email: str, subject: str, html: str) -> None:
    """Envía un email usando un servidor SMTP con la biblioteca estándar de Python.

    ¿Qué? Función síncrona auxiliar que construye y envía un mensaje MIME por SMTP.
    ¿Para qué? Proveer una alternativa a Resend que funcione sin cuenta ni dominio.
              En Docker, el host SMTP es "mailpit" — un servicio que captura emails localmente.
    ¿Impacto? No requiere dependencias nuevas — smtplib y email.mime son parte de Python stdlib.
              Se ejecuta en un thread separado (asyncio.to_thread) para no bloquear FastAPI.

    Args:
        to_email: Dirección de email del destinatario.
        subject: Asunto del email.
        html: Contenido HTML del cuerpo del email.
    """
    # ¿Qué? Construye el mensaje MIME multipart/alternative con contenido HTML.
    # ¿Para qué? El formato MIME es el estándar para emails con formato HTML.
    # ¿Impacto? Sin "alternative", algunos clientes de email podrían no renderizar el HTML.
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    # ¿Qué? Abre conexión al servidor SMTP y envía el mensaje.
    # ¿Para qué? SMTP es el protocolo universal de envío de correos — funciona con Mailpit,
    #            Gmail (STARTTLS, puerto 587), Mailtrap, SendGrid SMTP, etc.
    # ¿Impacto? El with-block cierra la conexión automáticamente (evita resource leaks).
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        # ¿Qué? Login opcional — Mailpit no requiere auth, Gmail sí.
        # ¿Para qué? Solo autenticar si hay credenciales configuradas.
        # ¿Impacto? Dejar SMTP_USERNAME vacío para Mailpit (no requiere autenticación).
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_verification_email(email: str, token: str) -> None:
    """Envía el email de verificación de cuenta al nuevo usuario.

    ¿Qué? Construye un email HTML con el enlace de activación y lo envía vía Resend.
    ¿Para qué? Confirmar que el correo proporcionado en el registro existe y le pertenece
              al usuario. Sin verificar, la cuenta queda bloqueada (is_email_verified=False).
    ¿Impacto? Si RESEND_API_KEY no está configurada, el enlace se imprime en los logs
              del servidor (modo desarrollo). El usuario igual se registra en la BD.
              El enlace expira en 24 horas.

    Args:
        email: Dirección de email del usuario recién registrado.
        token: Token único de verificación (UUID) generado al registrar.
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "NN Auth System — Verifica tu cuenta"
    html_content = f"""
    <html>
    <body style="font-family: system-ui, -apple-system, sans-serif;
                 max-width: 600px; margin: 0 auto; padding: 24px; color: #111827;">
        <h2 style="color: #1d4ed8; margin-bottom: 8px;">
            Verifica tu cuenta — NN Auth System
        </h2>
        <p style="color: #374151;">
            ¡Bienvenido! Para activar tu cuenta y poder iniciar sesión,
            haz clic en el botón de abajo.
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            El enlace es válido por <strong>24 horas</strong>.
        </p>
        <p style="margin: 32px 0;">
            <a href="{verification_url}"
               style="background-color: #1d4ed8; color: white; padding: 12px 28px;
                      text-decoration: none; border-radius: 6px; font-weight: 500;
                      font-size: 15px;">
                Verificar mi cuenta
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #6b7280; font-size: 13px;">
            Si no creaste esta cuenta, puedes ignorar este email sin problema.<br><br>
            Si el botón no funciona, copia este enlace en tu navegador:<br>
            <a href="{verification_url}" style="color: #1d4ed8;">{verification_url}</a>
        </p>
    </body>
    </html>
    """

    # ─── 1. SMTP disponible (Mailpit en desarrollo / SMTP real en producción) ───
    # ¿Qué? Si SMTP_HOST está configurado, enviar por SMTP con smtplib.
    # ¿Para qué? Mailpit captura el email en http://localhost:8025 sin enviarlo a internet.
    #            Ideal para aprendices — solo necesitan Docker Compose, sin cuentas externas.
    # ¿Impacto? Si SMTP falla, se loggea el enlace como fallback para no bloquear el registro.
    if settings.SMTP_HOST:
        try:
            await asyncio.to_thread(_send_email_smtp, email, subject, html_content)
            logger.info("✅ Email de verificación enviado vía SMTP a %s", email)
        except Exception as exc:
            logger.error("❌ Error enviando email de verificación vía SMTP a %s: %s", email, exc)
            logger.info(
                "\n%s\n"
                "📧 ENLACE DE VERIFICACIÓN (fallback — SMTP falló)\n"
                "   Para: %s\n"
                "   Enlace: %s\n"
                "%s",
                "=" * 60,
                email,
                verification_url,
                "=" * 60,
            )
        return

    # ─── 2. Resend configurado (requiere dominio verificado para enviar a cualquier email) ───
    # ¿Qué? Si no hay SMTP pero sí RESEND_API_KEY, usar la API de Resend.
    # ¿Para qué? Opción para producción o cuando se tiene un dominio verificado en Resend.
    # ¿Impacto? Sin dominio verificado en Resend, solo llegan emails al dueño de la cuenta.
    if not settings.RESEND_API_KEY:
        # ─── 3. Sin backend de email — solo logs ───
        # ¿Qué? Sin SMTP ni Resend, simular el envío mostrando el enlace en consola.
        # ¿Para qué? Permitir desarrollo básico sin ningún servicio de email configurado.
        # ¿Impacto? El desarrollador copia el enlace del log y lo abre manualmente en el navegador.
        logger.info(
            "\n%s\n"
            "📧 EMAIL DE VERIFICACIÓN (sin backend de email — copiar enlace del log)\n"
            "   Para: %s\n"
            "   Enlace: %s\n"
            "%s",
            "=" * 60,
            email,
            verification_url,
            "=" * 60,
        )
        return

    params: resend.Emails.SendParams = {
        "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
        "to": [email],
        "subject": subject,
        "html": html_content,
    }

    try:
        # ¿Qué? Ejecuta el envío síncrono de Resend en un thread separado.
        # ¿Para qué? No bloquear el event loop de FastAPI mientras se hace la llamada HTTP a Resend.
        # ¿Impacto? Sin to_thread(), un email lento congelaría la API para todas las peticiones.
        await asyncio.to_thread(_send_email_sync, params)
        logger.info("✅ Email de verificación enviado vía Resend a %s", email)
    except Exception as exc:
        # ¿Qué? Loggear el error pero no propagarlo — el registro ya fue exitoso en la BD.
        # ¿Para qué? Un fallo de Resend no debe impedir que el usuario se registre.
        # ¿Impacto? El usuario puede solicitar reenvío del email (funcionalidad futura).
        logger.error("❌ Error enviando email de verificación a %s: %s", email, exc)
        logger.info(
            "\n%s\n"
            "📧 ENLACE DE VERIFICACIÓN (fallback — Resend falló)\n"
            "   Para: %s\n"
            "   Enlace: %s\n"
            "%s",
            "=" * 60,
            email,
            verification_url,
            "=" * 60,
        )


async def send_password_reset_email(email: str, token: str) -> None:
    """Envía el email con el enlace de recuperación de contraseña.

    ¿Qué? Construye un email HTML con el enlace de reset y lo envía vía Resend.
    ¿Para qué? Permitir al usuario restablecer su contraseña cuando la ha olvidado.
    ¿Impacto? Si el email no se envía, el usuario no puede recuperar su cuenta.
              El enlace expira en 1 hora.

    Args:
        email: Dirección de email del usuario que solicitó el reset.
        token: Token único de recuperación (UUID) generado por el sistema.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "NN Auth System — Recuperación de contraseña"
    html_content = f"""
    <html>
    <body style="font-family: system-ui, -apple-system, sans-serif;
                 max-width: 600px; margin: 0 auto; padding: 24px; color: #111827;">
        <h2 style="color: #1d4ed8; margin-bottom: 8px;">
            Recuperación de contraseña — NN Auth System
        </h2>
        <p style="color: #374151;">
            Recibimos una solicitud para restablecer la contraseña de tu cuenta.
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            El enlace es válido por <strong>1 hora</strong>.
            Si no lo solicitaste, ignora este email.
        </p>
        <p style="margin: 32px 0;">
            <a href="{reset_url}"
               style="background-color: #1d4ed8; color: white; padding: 12px 28px;
                      text-decoration: none; border-radius: 6px; font-weight: 500;
                      font-size: 15px;">
                Restablecer contraseña
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #6b7280; font-size: 13px;">
            Si el botón no funciona, copia este enlace en tu navegador:<br>
            <a href="{reset_url}" style="color: #1d4ed8;">{reset_url}</a>
        </p>
    </body>
    </html>
    """

    # ─── 1. SMTP disponible (Mailpit en desarrollo / SMTP real en producción) ───
    if settings.SMTP_HOST:
        try:
            await asyncio.to_thread(_send_email_smtp, email, subject, html_content)
            logger.info("✅ Email de recuperación enviado vía SMTP a %s", email)
        except Exception as exc:
            logger.error("❌ Error enviando email de recuperación vía SMTP a %s: %s", email, exc)
            logger.info(
                "\n%s\n"
                "📧 ENLACE DE RECUPERACIÓN (fallback — SMTP falló)\n"
                "   Para: %s\n"
                "   Enlace: %s\n"
                "%s",
                "=" * 60,
                email,
                reset_url,
                "=" * 60,
            )
        return

    # ─── 2. Resend configurado ───
    if not settings.RESEND_API_KEY:
        # ─── 3. Sin backend de email — solo logs ───
        logger.info(
            "\n%s\n"
            "📧 EMAIL DE RECUPERACIÓN (sin backend de email — copiar enlace del log)\n"
            "   Para: %s\n"
            "   Enlace: %s\n"
            "%s",
            "=" * 60,
            email,
            reset_url,
            "=" * 60,
        )
        return

    params: resend.Emails.SendParams = {
        "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
        "to": [email],
        "subject": subject,
        "html": html_content,
    }

    try:
        await asyncio.to_thread(_send_email_sync, params)
        logger.info("✅ Email de recuperación enviado vía Resend a %s", email)
    except Exception as exc:
        logger.error("❌ Error enviando email de recuperación a %s: %s", email, exc)
        # ¿Qué? Fallback: mostrar el enlace en logs cuando Resend falla.
        # ¿Para qué? Permitir recuperación manual durante desarrollo sin dominio verificado.
        # ¿Impacto? El desarrollador puede copiar el enlace del log y usarlo manualmente.
        logger.info(
            "\n%s\n"
            "📧 ENLACE DE RECUPERACIÓN (fallback — Resend falló)\n"
            "   Para: %s\n"
            "   Enlace: %s\n"
            "%s",
            "=" * 60,
            email,
            reset_url,
            "=" * 60,
        )
