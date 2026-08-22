"""
Módulo: routers/users.py
Descripción: Endpoints de usuario — perfil del usuario autenticado y preferencias.
¿Para qué? Proveer endpoints para que el usuario autenticado consulte y gestione su perfil
           y preferencias de la aplicación (idioma, etc.).
¿Impacto? Sin este router, el frontend no podría mostrar los datos del usuario logueado
          (nombre, email, fecha de registro, etc.) ni persistir preferencias como el idioma.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UpdateLocaleRequest, UserResponse
from app.services.auth_service import update_user_locale

# ¿Qué? Router de FastAPI para endpoints de usuario.
# ¿Para qué? Agrupar endpoints relacionados con el perfil del usuario bajo /api/v1/users.
# ¿Impacto? Separar los endpoints de usuario de los de auth mantiene el código organizado
#           y facilita agregar más endpoints de usuario en el futuro (ej: update profile).
router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario actual",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retorna los datos del perfil del usuario autenticado.

    ¿Qué? Endpoint que retorna los datos del usuario que está haciendo el request.
    ¿Para qué? El frontend lo usa para mostrar el nombre, email y datos del usuario
              en el dashboard, navbar, perfil, etc.
    ¿Impacto? Depends(get_current_user) hace que este endpoint sea PROTEGIDO:
              solo funciona con un access_token válido. Si el token es inválido o expiró,
              FastAPI retorna 401 automáticamente (gracias a la dependencia).

    Args:
        current_user: Usuario autenticado (inyectado automáticamente por FastAPI).

    Returns:
        Datos del perfil del usuario (sin contraseña).
    """
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me/locale",
    response_model=UserResponse,
    summary="Actualizar idioma preferido del usuario (i18n)",
)
def update_locale(
    locale_data: UpdateLocaleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Actualiza el locale (idioma preferido) del usuario autenticado.

    ¿Qué? Endpoint que persiste la preferencia de idioma del usuario en la BD.
    ¿Para qué? Cuando el usuario cambia el idioma en la interfaz, este endpoint
              sincroniza la preferencia con la BD para restaurarla en otros dispositivos.
              Es parte del sistema de internacionalización (i18n) del proyecto.
    ¿Impacto? Al iniciar sesión, el response incluye `locale` → el frontend aplica
              el idioma guardado automáticamente. Sin este endpoint, la preferencia
              solo estaría en localStorage del navegador actual.

    Concepto i18n pedagógico:
        El flujo completo es:
        1. Usuario cambia idioma en UI → `i18n.changeLanguage("en")`
        2. Frontend guarda en localStorage["i18nextLng"] = "en"
        3. Frontend llama PATCH /api/v1/users/me/locale con {"locale": "en"}
        4. Backend actualiza users.locale = "en" en PostgreSQL
        5. Al login desde otro dispositivo: response.locale = "en" → UI en inglés

    Args:
        locale_data: Datos validados con el nuevo locale ("es" o "en").
        current_user: Usuario autenticado (inyectado por FastAPI).
        db: Sesión de base de datos (inyectada por FastAPI).

    Returns:
        Datos del perfil del usuario con el locale actualizado.

    Raises:
        401: Si no hay access_token válido.
        422: Si el locale enviado no es "es" ni "en" (validado por Pydantic).
    """
    # ¿Qué? Delegar la lógica al servicio — el router solo orquesta.
    # ¿Para qué? Mantener el Separation of Concerns: router → recibe y retorna HTTP,
    #            service → contiene la lógica de negocio.
    # ¿Impacto? Facilita testear la lógica de negocio sin levantar el servidor HTTP.
    updated_user = update_user_locale(db=db, user=current_user, locale=locale_data.locale)
    return UserResponse.model_validate(updated_user)
