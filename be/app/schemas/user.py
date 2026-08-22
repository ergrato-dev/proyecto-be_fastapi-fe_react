"""
Módulo: schemas/user.py
Descripción: Schemas Pydantic para validación de datos de entrada (request) y salida (response)
             en los endpoints de autenticación y usuario.
¿Para qué? Definir la "forma" exacta de los datos que la API acepta y retorna.
           Pydantic valida automáticamente tipos, formatos y restricciones — si los datos
           no cumplen el schema, FastAPI retorna un 422 con detalles del error.
¿Impacto? Sin schemas, la API aceptaría cualquier dato sin validación, exponiendo el backend
          a datos malformados, inyecciones y errores silenciosos.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ¿Qué? Función auxiliar con las reglas de fortaleza de contraseña.
# ¿Para qué? Evitar duplicar el mismo bloque de validación en UserCreate,
#           ChangePasswordRequest y ResetPasswordRequest (principio DRY).
# ¿Impacto? Si las reglas cambian (ej: exigir símbolo especial), solo se
#           modifica este único lugar y todos los schemas quedan actualizados.
def _validate_password_strength(v: str) -> str:
    """Valida que la contraseña cumpla los requisitos mínimos de seguridad.

    ¿Qué? Verifica longitud mínima y presencia de mayúsculas, minúsculas y números.
    ¿Para qué? Centralizar las reglas de fortaleza para no repetir código.
    ¿Impacto? Usada en UserCreate, ChangePasswordRequest y ResetPasswordRequest.

    Args:
        v: Valor de la contraseña a validar.

    Returns:
        La contraseña si pasa todas las validaciones.

    Raises:
        ValueError: Si la contraseña no cumple los requisitos.
    """
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", v):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula")
    if not re.search(r"[a-z]", v):
        raise ValueError("La contraseña debe contener al menos una letra minúscula")
    if not re.search(r"\d", v):
        raise ValueError("La contraseña debe contener al menos un número")
    return v


# ════════════════════════════════════════
# 📥 Schemas de REQUEST (datos que envía el cliente)
# ════════════════════════════════════════


class UserCreate(BaseModel):
    """Schema para el registro de un nuevo usuario.

    ¿Qué? Define los campos requeridos para crear una cuenta: email, nombre y contraseña.
    ¿Para qué? Validar que el cliente envíe datos correctos antes de procesarlos.
    ¿Impacto? El validador de password garantiza fortaleza mínima — sin él, los usuarios
              podrían registrarse con contraseñas débiles como "123".
    """

    # ¿Qué? Email del usuario — Pydantic valida formato automáticamente con EmailStr.
    # ¿Para qué? Identificador único y medio de contacto para recuperación de contraseña.
    # ¿Impacto? EmailStr rechaza emails inválidos (sin @, sin dominio, etc.).
    email: EmailStr

    # ¿Qué? Nombres del usuario (primer nombre, nombres de pila).
    # ¿Para qué? Personalización de la experiencia — el frontend usa first_name para saludar.
    # ¿Impacto? Campo requerido — sin nombre, no se puede personalizar la interfaz.
    first_name: str

    # ¿Qué? Apellidos del usuario.
    # ¿Para qué? Complementar la identidad del usuario junto con first_name.
    # ¿Impacto? Campo requerido — permite mostrar el nombre completo cuando sea necesario.
    last_name: str

    # ¿Qué? Contraseña en texto plano (solo viaja en el request, NUNCA se almacena así).
    # ¿Para qué? El backend la hashea con bcrypt antes de guardarla en la BD.
    # ¿Impacto? El validador exige mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número.
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Valida que la contraseña cumpla requisitos mínimos de seguridad.

        ¿Qué? Delega en la función auxiliar _validate_password_strength.
        ¿Para qué? Mantener el validador declarativo en el schema sin duplicar lógica.
        ¿Impacto? Sin esta validación, un usuario podría registrarse con "a" como contraseña.
        """
        return _validate_password_strength(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        """Valida y normaliza los campos de nombre.

        ¿Qué? Aplica a first_name y last_name: strip de espacios, longitud mínima/máxima
              y conversión a MAYÚSCULAS.
        ¿Para qué? Garantizar consistencia en la BD — siempre se almacenan en uppercase,
                  sin importar cómo los ingrese el usuario (minúsculas, mixto, etc.).
        ¿Impacto? Sin la normalización, el mismo nombre "juan" y "Juan" y "JUAN" podrían
                  coexistir con formatos distintos, dificultando búsquedas y comparaciones.
        """
        v = v.strip().upper()
        if len(v) < 2:
            raise ValueError("El campo debe tener al menos 2 caracteres")
        if len(v) > 255:
            raise ValueError("El campo no puede exceder 255 caracteres")
        return v


class UserLogin(BaseModel):
    """Schema para el login de un usuario.

    ¿Qué? Define los campos necesarios para autenticarse: email y contraseña.
    ¿Para qué? Validar las credenciales antes de buscar en la BD.
    ¿Impacto? Estructura simple — la validación real (¿existe el email? ¿coincide la password?)
              se hace en el service, no aquí.
    """

    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    """Schema para cambiar la contraseña (usuario autenticado).

    ¿Qué? Requiere la contraseña actual y la nueva contraseña.
    ¿Para qué? Verificar que el usuario conoce su contraseña actual antes de cambiarla
              (previene cambios si alguien toma el dispositivo desbloqueado).
    ¿Impacto? Sin current_password, cualquier persona con acceso al token podría cambiar
              la contraseña sin conocer la original.
    """

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Valida la fortaleza de la nueva contraseña en el cambio de contraseña.

        ¿Qué? Delega en _validate_password_strength para verificar longitud y composición.
        ¿Para qué? Garantizar que el usuario no debilite su cuenta al cambiarla —
                   las mismas reglas del registro aplican aquí (≥8 chars, mayúscula,
                   minúscula, número). Principio DRY: una sola función con las reglas.
        ¿Impacto? Sin esta validación, un usuario podría cambiar su contraseña
                  segura por una débil como "abc" sin que el sistema lo impida.
        """
        return _validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitar recuperación de contraseña.

    ¿Qué? Solo requiere el email del usuario.
    ¿Para qué? Iniciar el flujo de recuperación: generar token + enviar email.
    ¿Impacto? La API siempre retorna el mismo mensaje (éxito), sin importar si el email
              existe o no — esto previene la enumeración de usuarios.
    """

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema para restablecer la contraseña con un token de recuperación.

    ¿Qué? Requiere el token de reset (recibido por email) y la nueva contraseña.
    ¿Para qué? Completar el flujo de recuperación: validar token + actualizar contraseña.
    ¿Impacto? El token se marca como usado después de un reset exitoso,
              evitando que se reutilice.
    """

    # ¿Qué? Token UUID de reset (recibido por email tras forgot-password).
    # ¿Para qué? El backend lo busca en password_reset_tokens para validar y actualizar.
    # ¿Impacto? min_length=1 rechaza strings vacíos con 422 antes de consultar la BD.
    token: str = Field(min_length=1)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Valida la fortaleza de la nueva contraseña en el restablecimiento.

        ¿Qué? Delega en _validate_password_strength para verificar longitud y composición.
        ¿Para qué? El flujo de reset-password no debe ser una vía para establecer
                   contraseñas débiles — las mismas reglas del registro aplican aquí.
                   Principio DRY: una sola función centraliza las reglas de fortaleza.
        ¿Impacto? Sin esta validación, alguien que recobre acceso a su cuenta podría
                  reemplazar su contraseña robusta por "123" — dejando la cuenta vulnerable.
        """
        return _validate_password_strength(v)


class RefreshTokenRequest(BaseModel):
    """Schema para renovar el access token usando el refresh token.

    ¿Qué? Contiene el refresh token que el cliente recibió durante el login.
    ¿Para qué? Obtener un nuevo access token sin re-ingresar credenciales.
    ¿Impacto? Es el mecanismo que mantiene la sesión del usuario viva sin pedirle
              email/password continuamente.
    """

    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Schema para verificar la dirección de email con el token enviado al usuario.

    ¿Qué? Contiene el token UUID que el usuario recibió en su email de verificación.
    ¿Para qué? Confirmar que el email ingresado en el registro es real y accesible.
    ¿Impacto? Sin verificar el email, is_email_verified permanece False y el usuario
              no puede iniciar sesión. Este schema es lo que el frontend envía al
              endpoint POST /api/v1/auth/verify-email al recibir el token de la URL.
    """

    # ¿Qué? Token UUID de verificación (viene como query param en la URL del email).
    # ¿Para qué? El backend lo busca en email_verification_tokens para validar y activar.
    # ¿Impacto? min_length=1 rechaza strings vacíos con 422 antes de consultar la BD.
    token: str = Field(min_length=1)


# ════════════════════════════════════════
# 📤 Schemas de RESPONSE (datos que retorna la API)
# ════════════════════════════════════════


class UserResponse(BaseModel):
    """Schema de respuesta con datos del usuario (sin password).

    ¿Qué? Define qué campos del usuario se retornan al cliente.
    ¿Para qué? Controlar exactamente qué datos se exponen — NUNCA incluir hashed_password.
    ¿Impacto? Sin response_model, FastAPI podría serializar el objeto User completo,
              exponiendo el hash de la contraseña. model_config from_attributes=True
              permite convertir directamente desde el modelo ORM.
    """

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    is_active: bool
    # ¿Qué? Campo que indica si el usuario verificó su email al registrarse.
    # ¿Para qué? El frontend puede mostrar un aviso "verifica tu email" en el dashboard.
    # ¿Impacto? False = el usuario no puede iniciar sesión hasta verificar.
    is_email_verified: bool
    # ¿Qué? Idioma preferido del usuario para la interfaz (locale).
    # ¿Para qué? El frontend lo lee al iniciar sesión para aplicar el idioma correcto
    #            sin que el usuario tenga que seleccionarlo de nuevo en cada dispositivo.
    # ¿Impacto? i18n — la preferencia del usuario viaja en el response del login/perfil.
    locale: str
    created_at: datetime
    updated_at: datetime

    # ¿Qué? Configuración que permite crear este schema desde un objeto SQLAlchemy.
    # ¿Para qué? Convertir User (ORM) → UserResponse (Pydantic) automáticamente.
    # ¿Impacto? Sin esto, habría que construir el dict manualmente campo por campo.
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema de respuesta con los tokens de autenticación.

    ¿Qué? Retorna access_token, refresh_token y el tipo de token ("bearer").
    ¿Para qué? El frontend almacena estos tokens para enviarlos en peticiones futuras.
    ¿Impacto? token_type="bearer" indica al cliente cómo enviar el token:
              header Authorization: Bearer <access_token>.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Schema de respuesta genérico con un mensaje.

    ¿Qué? Respuesta simple con un campo "message".
    ¿Para qué? Retornar confirmaciones de operaciones (cambio de contraseña,
              envío de email de recuperación, etc.).
    ¿Impacto? Estandariza las respuestas de la API — el frontend siempre
              puede esperar un campo "message" en operaciones sin datos de retorno.
    """

    message: str


class UpdateLocaleRequest(BaseModel):
    """Schema para actualizar el idioma preferido del usuario (i18n).

    ¿Qué? Contiene el nuevo locale que el usuario seleccionó en la interfaz.
    ¿Para qué? Persistir la preferencia de idioma en la base de datos,
              de forma que se restaure al iniciar sesión desde cualquier dispositivo.
    ¿Impacto? Sin este schema, el idioma solo se guardaría en localStorage
              del navegador actual — al cambiar de dispositivo se perdería la preferencia.

    Concepto i18n pedagógico:
        locale: código de idioma estándar (ISO 639-1). Soportamos:
          - "es" → Español (por defecto — contexto SENA/Colombia)
          - "en" → English (inglés general)
        Formato reducido: solo el base-language code, sin región (no "es-CO", no "en-US").
    """

    # ¿Qué? Código del idioma seleccionado por el usuario.
    # ¿Para qué? Identificar en qué idioma debe mostrarse la interfaz.
    # ¿Impacto? SOLO acepta "es" o "en". Cualquier otro valor retorna 422 Unprocessable Entity.
    locale: str

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        """Valida que el locale sea uno de los idiomas soportados.

        ¿Qué? Verifica que el valor sea "es" o "en".
        ¿Para qué? Evitar que el cliente envíe locales no soportados
                   como "fr", "pt" o "es-CO" que causan comportamientos indefinidos.
        ¿Impacto? OWASP A03 Injection: validar inputs en el servidor siempre,
                   aunque el frontend también valide. Nunca confiar solo en el cliente.

        Args:
            v: Valor del locale enviado por el cliente.

        Returns:
            El locale validado.

        Raises:
            ValueError: Si el locale no es "es" o "en".
        """
        supported_locales = ("es", "en")
        if v not in supported_locales:
            raise ValueError(
                f"Locale '{v}' no está soportado. Usa uno de: {', '.join(supported_locales)}"
            )
        return v
