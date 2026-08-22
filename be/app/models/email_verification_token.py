"""
Módulo: models/email_verification_token.py
Descripción: Modelo ORM que representa la tabla `email_verification_tokens` en PostgreSQL.
¿Para qué? Almacenar tokens temporales de un solo uso que confirman que el email
           proporcionado durante el registro pertenece realmente al nuevo usuario.
¿Impacto? Sin esta tabla, el flujo de verificación de cuenta no puede completarse —
          cualquier persona podría registrarse con el email de otra persona sin validación.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ¿Qué? Import condicional del modelo User solo para type hints.
# ¿Para qué? Romper la importación circular User ↔ EmailVerificationToken.
# ¿Impacto? Solo se importa durante análisis estático, no en runtime.
if TYPE_CHECKING:
    from app.models.user import User


class EmailVerificationToken(Base):
    """Modelo ORM para la tabla `email_verification_tokens`.

    ¿Qué? Clase Python que mapea a la tabla de tokens de verificación de email.
    ¿Para qué? Cada vez que un usuario se registra, se crea un registro aquí con
              un token único y una fecha de expiración. Al hacer clic en el enlace
              del email, el token se consume (marcado como used=True) y la cuenta
              queda activa (is_email_verified=True en la tabla users).
    ¿Impacto? Garantiza que solo usuarios con acceso real a su email pueden
              iniciar sesión en el sistema.
    """

    __tablename__ = "email_verification_tokens"

    # ────────────────────────────
    # 📌 Columnas
    # ────────────────────────────

    # ¿Qué? Identificador único del registro de token.
    # ¿Para qué? Clave primaria de la tabla.
    # ¿Impacto? UUID evita colisiones y no revela información secuencial.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ¿Qué? Referencia al usuario al que pertenece este token de verificación.
    # ¿Para qué? Vincular el token con el usuario correcto para activar su cuenta.
    # ¿Impacto? ondelete="CASCADE" borra los tokens automáticamente si se elimina el usuario.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ¿Qué? Token único que se envía en el email de verificación.
    # ¿Para qué? Actuar como "llave temporal" para confirmar la posesión del email.
    #            Solo quien tenga acceso al buzón de entrada puede completar la verificación.
    # ¿Impacto? UNIQUE + INDEX: cada token es irrepetible y las búsquedas son rápidas.
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # ¿Qué? Fecha y hora de expiración del token.
    # ¿Para qué? Limitar el tiempo de validez del enlace de verificación.
    # ¿Impacto? Tokens expiran en 24 horas. Si vence, el usuario debe re-registrarse
    #           o solicitar un reenvío (funcionalidad futura).
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ¿Qué? Indicador de si este token ya fue utilizado para verificar el email.
    # ¿Para qué? Evitar que el mismo enlace sea clickeado múltiples veces con efecto.
    # ¿Impacto? Un token marcado como used=True es rechazado aunque no haya expirado.
    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ¿Qué? Fecha y hora de creación del token.
    # ¿Para qué? Trazabilidad — saber cuándo se emitió el token de verificación.
    # ¿Impacto? Útil para auditorías y para mostrar "expira en X horas" al usuario.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ¿Qué? Relación ORM hacia el usuario propietario de este token de verificación.
    # ¿Para qué? Acceder directamente al usuario: token_record.user.email
    #            Sin esta relación habría que hacer query manual por user_id.
    # ¿Impacto? back_populates="email_verification_tokens" conecta este atributo
    #            con User.email_verification_tokens — SQLAlchemy mantiene ambos lados en sync.
    #            Reemplaza el estilo antiguo `backref=` por la forma explícita moderna
    #            (back_populates) recomendada en SQLAlchemy 2.0.
    user: Mapped[User] = relationship(
        "User",
        back_populates="email_verification_tokens",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Representación legible del token para debugging.

        ¿Qué? Retorna una cadena descriptiva al imprimir el objeto.
        ¿Para qué? Facilitar el debugging: ver user_id y estado de uso rápidamente.
        ¿Impacto? NUNCA incluir el token en __repr__ por seguridad.
        """
        return f"EmailVerificationToken(id={self.id}, user_id={self.user_id}, used={self.used})"
