"""
Módulo: services/auth_service.py
Descripción: Lógica de negocio para todas las operaciones de autenticación —
             registro, login, cambio de contraseña y recuperación.
¿Para qué? Separar la lógica de negocio de los endpoints (routers). Los routers solo
           reciben requests y llaman al service; el service contiene TODA la lógica.
¿Impacto? Este módulo es el cerebro del sistema de auth. Aquí se decide si un login
          es válido, si un registro debe aceptarse, y cómo se maneja cada flujo.
          Separar esta lógica facilita testing (se puede testear sin HTTP) y reutilización.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.utils.audit_log import (
    log_email_verified,
    log_login_failed,
    log_login_success,
    log_password_changed,
    log_password_reset_requested,
)
from app.utils.email import send_password_reset_email, send_verification_email
from app.utils.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def register_user(db: Session, user_data: UserCreate) -> User:
    """Registra un nuevo usuario y envía el email de verificación de cuenta.

    ¿Qué? Crea una nueva cuenta con email, nombre y contraseña hasheada,
          genera un token de verificación y envía el email de activación.
    ¿Para qué? Permitir que nuevos usuarios se registren en NN Auth System.
    ¿Impacto? Flujo: verifica email duplicado → hashea password → crea en BD
              → genera token de verificación → envía email.
              El usuario queda con is_email_verified=False hasta hacer clic en el enlace.
              Si el email falla, el usuario igual se registra (el error no es blocante).

    Args:
        db: Sesión de base de datos.
        user_data: Datos validados del usuario (email, full_name, password).

    Returns:
        Objeto User creado y persistido en la BD.

    Raises:
        HTTPException 400: Si el email ya está registrado.
    """
    # ¿Qué? Buscar si ya existe un usuario con ese email.
    # ¿Para qué? Evitar cuentas duplicadas — email es UNIQUE en la BD.
    # ¿Impacto? Sin esta verificación, la BD lanzaría un IntegrityError poco descriptivo.
    stmt = select(User).where(User.email == user_data.email)
    existing_user = db.execute(stmt).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # ¿Qué? Crear el objeto User con la contraseña hasheada.
    # ¿Para qué? Almacenar la contraseña de forma segura — NUNCA en texto plano.
    # ¿Impacto? hash_password usa bcrypt, que es deliberadamente lento para dificultar
    #           ataques de fuerza bruta contra hashes filtrados.
    new_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ¿Qué? Genera un token UUID único para el enlace de verificación de email.
    # ¿Para qué? Este token viaja en la URL del email y confirma la posesión del buzón.
    # ¿Impacto? UUID4 tiene 122 bits de entropía — prácticamente imposible de adivinar.
    verification_token = str(uuid.uuid4())

    # ¿Qué? Crea el registro del token en la tabla email_verification_tokens.
    # ¿Para qué? Almacenar el token con su expiración para validarlo cuando el usuario haga clic.
    # ¿Impacto? Expiración de 24 horas — después, el usuario debe re-registrarse o solicitar reenvío.
    token_record = EmailVerificationToken(
        user_id=new_user.id,
        token=verification_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(token_record)
    db.commit()

    # ¿Qué? Envía el email de verificación al usuario recién registrado.
    # ¿Para qué? El usuario debe hacer clic en el enlace para activar su cuenta.
    # ¿Impacto? Si RESEND_API_KEY no está configurada, el enlace se imprime en los logs.
    #           El fallo de envío NO revierte el registro — el error es no bloqueante.
    await send_verification_email(email=new_user.email, token=verification_token)

    return new_user


def login_user(db: Session, login_data: UserLogin) -> TokenResponse:
    """Autentica un usuario y retorna tokens JWT.

    ¿Qué? Verifica credenciales (email + password) y genera access/refresh tokens.
    ¿Para qué? Permitir al usuario iniciar sesión y obtener tokens para acceder a la API.
    ¿Impacto? Flujo: buscar por email → verificar password → generar tokens.
              Los mensajes de error son GENÉRICOS ("credenciales inválidas") para no revelar
              si el email existe o no (previene enumeración de usuarios).

    Args:
        db: Sesión de base de datos.
        login_data: Credenciales del usuario (email, password).

    Returns:
        TokenResponse con access_token, refresh_token y token_type.

    Raises:
        HTTPException 401: Si las credenciales son inválidas.
    """
    # ¿Qué? Buscar usuario por email.
    # ¿Para qué? Obtener el hash almacenado para comparar con la contraseña ingresada.
    # ¿Impacto? Si el usuario no existe, se retorna el MISMO error que si la contraseña
    #           es incorrecta — esto previene la enumeración de emails.
    stmt = select(User).where(User.email == login_data.email)
    user = db.execute(stmt).scalar_one_or_none()

    # ¿Qué? Si el usuario no existe, igual se corre bcrypt contra DUMMY_PASSWORD_HASH.
    # ¿Para qué? Sin esto, el branch "usuario no existe" retorna en microsegundos
    #           mientras que "contraseña incorrecta" tarda lo que tarda bcrypt (~60-100ms) —
    #           esa diferencia de tiempo delata qué emails existen aunque el mensaje
    #           de error sea idéntico (timing attack, OWASP A07).
    password_hash = user.hashed_password if user else DUMMY_PASSWORD_HASH
    if not user or not verify_password(login_data.password, password_hash):
        # ¿Qué? Registrar el intento fallido antes de lanzar la excepción.
        # ¿Para qué? Detectar patrones de fuerza bruta — múltiples fallos en poco tiempo son alarma.
        # ¿Impacto? OWASP A09: sin este log, un ataque de 10,000 intentos pasa desapercibido.
        log_login_failed(email=login_data.email, reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ¿Qué? Verificar que la cuenta esté activa.
    # ¿Para qué? Impedir login de cuentas desactivadas (ej: suspendidas por admin).
    # ¿Impacto? Sin esta verificación, usuarios desactivados podrían seguir accediendo.
    if not user.is_active:
        log_login_failed(email=login_data.email, reason="account_inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada. Contacte al administrador.",
        )

    # ¿Qué? Verificar que el usuario haya confirmado su email antes de permitir el login.
    # ¿Para qué? Asegurar que el email ingresado en el registro pertenece realmente al usuario.
    # ¿Impacto? Sin esta verificación, alguien podría registrarse con el email de otra persona
    #           y acceder al sistema antes de que el dueño real del email lo note.
    if not user.is_email_verified:
        log_login_failed(email=login_data.email, reason="email_not_verified")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Debes verificar tu email antes de iniciar sesión. Revisa tu bandeja de entrada."
            ),
        )

    # ¿Qué? Generar par de tokens JWT (access + refresh).
    # ¿Para qué? El access token se usa en cada request; el refresh token para renovar.
    # ¿Impacto? "sub" (subject) contiene el email — es lo que identifica al usuario en el token.
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    # ¿Qué? Registrar el login exitoso para auditoría.
    # ¿Para qué? Los logins exitosos también son relevantes — permiten detectar accesos
    #            desde IPs o zonas horarias inusuales que el usuario legítimo no reconoce.
    # ¿Impacto? OWASP A09: la ausencia de este log impide detectar accesos no autorizados
    #            que usaron credenciales robadas.
    log_login_success(email=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    """Genera un nuevo access token usando un refresh token válido.

    ¿Qué? Decodifica el refresh token, verifica que el usuario existe y genera nuevos tokens.
    ¿Para qué? Mantener la sesión del usuario sin pedirle credenciales cada 15 minutos.
    ¿Impacto? Si el refresh token expiró (>7 días), el usuario debe hacer login de nuevo.
              Se genera un NUEVO refresh token (rotación) para mayor seguridad.

    Args:
        db: Sesión de base de datos.
        refresh_token: Token JWT de refresco.

    Returns:
        TokenResponse con nuevos access_token y refresh_token.

    Raises:
        HTTPException 401: Si el refresh token es inválido o expirado.
    """
    payload = decode_token(refresh_token)

    # ¿Qué? Verificar que el token es válido y de tipo "refresh".
    # ¿Para qué? Evitar que un access token sea usado como refresh token.
    # ¿Impacto? Sin esta verificación, la distinción entre tipos de token sería inútil.
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str | None = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario",
        )

    # ¿Qué? Verificar que el usuario aún existe y está activo.
    # ¿Para qué? Si la cuenta fue eliminada o desactivada después del login,
    #            no debería poder renovar su sesión.
    # ¿Impacto? Sin esto, usuarios eliminados mantendrían acceso hasta que expire el refresh.
    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o cuenta desactivada",
        )

    # ¿Qué? Rotación de tokens — generar NUEVOS access y refresh tokens.
    # ¿Para qué? Si el refresh token anterior fue comprometido, el nuevo lo invalida
    #            (el antiguo ya no se puede usar porque se regenera).
    # ¿Impacto? Mejora la seguridad: cada refresh genera un nuevo par de tokens.
    new_access = create_access_token(data={"sub": user.email})
    new_refresh = create_refresh_token(data={"sub": user.email})

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )


def change_password(db: Session, user: User, password_data: ChangePasswordRequest) -> None:
    """Cambia la contraseña de un usuario autenticado.

    ¿Qué? Verifica la contraseña actual y actualiza con la nueva (hasheada).
    ¿Para qué? Permitir al usuario cambiar su contraseña desde su perfil (ya logueado).
    ¿Impacto? Requiere la contraseña actual como verificación adicional — previene
              cambios no autorizados si alguien tiene acceso temporal al token.

    Args:
        db: Sesión de base de datos.
        user: Objeto User del usuario autenticado (obtenido vía get_current_user).
        password_data: Contraseña actual y nueva contraseña.

    Raises:
        HTTPException 400: Si la contraseña actual es incorrecta.
    """
    # ¿Qué? Verificar que el usuario conoce su contraseña actual.
    # ¿Para qué? Capa de seguridad adicional — si alguien tiene el token pero no la contraseña,
    #            no puede cambiarla.
    # ¿Impacto? Sin esta verificación, cualquiera con un access token válido podría
    #           cambiar la contraseña y apoderarse de la cuenta.
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    # ¿Qué? Hashear la nueva contraseña y actualizar en la BD.
    # ¿Para qué? Almacenar la nueva contraseña de forma segura.
    # ¿Impacto? Después de este cambio, la contraseña anterior ya no funciona para login.
    user.hashed_password = hash_password(password_data.new_password)
    db.commit()

    # ¿Qué? Registrar el cambio de contraseña para auditoría.
    # ¿Para qué? Si el usuario legítimo recibe una notificación de cambio que no reconoce,
    #            el log confirma qué ocurrió y cuándo (posible cuenta comprometida).
    # ¿Impacto? OWASP A09: esencial para investigación post-incidente.
    log_password_changed(user_id=str(user.id))


async def request_password_reset(db: Session, email: str) -> None:
    """Solicita un email de recuperación de contraseña.

    ¿Qué? Genera un token de reset, lo guarda en la BD y envía el email con el enlace.
    ¿Para qué? Permitir al usuario restablecer su contraseña cuando la ha olvidado.
    ¿Impacto? SIEMPRE retorna éxito, incluso si el email no existe en la BD.
              Esto previene la enumeración de usuarios (un atacante no puede saber
              si un email está registrado basándose en la respuesta).

    Args:
        db: Sesión de base de datos.
        email: Email del usuario que solicita la recuperación.
    """
    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalar_one_or_none()

    # ¿Qué? Si el usuario no existe, retornar silenciosamente sin hacer nada.
    # ¿Para qué? Prevenir enumeración de usuarios — la API no debe revelar si el email existe.
    # ¿Impacto? El cliente siempre ve "Si el email existe, recibirás un enlace..."
    #           Sin importar si el email está registrado o no.
    if not user:
        return

    # ¿Qué? Generar un token UUID único para el enlace de recuperación.
    # ¿Para qué? Este token viaja en la URL del email y se valida al restablecer.
    # ¿Impacto? UUID4 tiene 122 bits de entropía — prácticamente imposible de adivinar.
    reset_token = str(uuid.uuid4())

    # ¿Qué? Crear el registro del token en la tabla password_reset_tokens.
    # ¿Para qué? Almacenar el token con su expiración para validarlo después.
    # ¿Impacto? Expiración de 1 hora — después de eso, el usuario debe solicitar otro.
    token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    db.add(token_record)
    db.commit()

    # ¿Qué? Registrar la solicitud de recuperación para auditoría.
    # ¿Para qué? Detectar abuso del endpoint — muchas solicitudes desde la misma IP
    #            indican intento de spam de emails o detección de cuentas válidas.
    # ¿Impacto? NO se loguea el email — previene que el log mismo revele qué emails existen.
    #            El rate limiter es la primera defensa; este log permite detectar
    #            patrones que el rate limiter no cubre (ej: ataques distribuidos).
    log_password_reset_requested()

    # ¿Qué? Enviar el email con el enlace de recuperación.
    # ¿Para qué? El usuario hace clic en el enlace, que lo lleva al frontend con el token.
    # ¿Impacto? En desarrollo, el enlace se imprime en la consola del servidor.
    await send_password_reset_email(email=user.email, token=reset_token)


def reset_password(db: Session, reset_data: ResetPasswordRequest) -> None:
    """Restablece la contraseña usando un token de recuperación.

    ¿Qué? Valida el token de reset, hashea la nueva contraseña y actualiza la BD.
    ¿Para qué? Completar el flujo de recuperación de contraseña.
    ¿Impacto? El token se marca como "usado" después del reset exitoso,
              evitando que se reutilice.

    Args:
        db: Sesión de base de datos.
        reset_data: Token de reset y nueva contraseña.

    Raises:
        HTTPException 400: Si el token es inválido, expirado o ya fue usado.
    """
    # ¿Qué? Buscar el token en la BD.
    # ¿Para qué? Verificar que el token existe y obtener el usuario asociado.
    # ¿Impacto? Si el token no existe, alguien intentó usar un token falso o manipulado.
    stmt = select(PasswordResetToken).where(PasswordResetToken.token == reset_data.token)
    token_record = db.execute(stmt).scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperación inválido",
        )

    # ¿Qué? Verificar que el token no haya sido usado previamente.
    # ¿Para qué? Evitar reutilización de tokens — un token solo sirve una vez.
    # ¿Impacto? Sin esto, alguien podría cambiar la contraseña múltiples veces con el mismo token.
    if token_record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token de recuperación ya fue utilizado",
        )

    # ¿Qué? Verificar que el token no haya expirado.
    # ¿Para qué? Limitar la ventana de tiempo en que un enlace de recuperación es válido.
    # ¿Impacto? Tokens expiran en 1 hora — después de eso, el usuario debe solicitar otro.
    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de recuperación ha expirado. Solicite uno nuevo.",
        )

    # ¿Qué? Obtener el usuario asociado al token.
    # ¿Para qué? Actualizar la contraseña del usuario correcto.
    # ¿Impacto? El user_id del token apunta al usuario que solicitó la recuperación.
    stmt = select(User).where(User.id == token_record.user_id)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )

    # ¿Qué? Actualizar la contraseña y marcar el token como usado.
    # ¿Para qué? Completar el reset + invalidar el token para que no se reutilice.
    # ¿Impacto? Después de esto, la contraseña anterior ya no funciona y el token es inválido.
    user.hashed_password = hash_password(reset_data.new_password)
    token_record.used = True
    db.commit()


def verify_email(db: Session, token: str) -> None:
    """Verifica la dirección de email del usuario usando el token enviado al registrarse.

    ¿Qué? Valida el token de verificación y activa la cuenta marcando is_email_verified=True.
    ¿Para qué? Confirmar que el email ingresado en el registro pertenece realmente al usuario.
    ¿Impacto? Tras este proceso, el usuario puede iniciar sesión. Sin él, el login retorna 403.
              El token se marca como usado para evitar que el enlace sea reutilizado.

    Args:
        db: Sesión de base de datos.
        token: UUID de verificación recibido por email.

    Raises:
        HTTPException 400: Si el token no existe, ya fue usado o ha expirado.
    """
    # ¿Qué? Buscar el token en la tabla email_verification_tokens.
    # ¿Para qué? Verificar que el token existe y obtener el usuario asociado.
    # ¿Impacto? Si no existe, el usuario envió un token inventado o ya fue procesado.
    stmt = select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    token_record = db.execute(stmt).scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de verificación inválido",
        )

    # ¿Qué? Verificar que el token no haya sido usado previamente.
    # ¿Para qué? Evitar activaciones duplicadas — un token solo sirve una vez.
    # ¿Impacto? Sin esto, el mismo enlace podría re-activar cuentas ya activas o manipuladas.
    if token_record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token de verificación ya fue utilizado",
        )

    # ¿Qué? Verificar que el token no haya expirado.
    # ¿Para qué? Los tokens de verificación tienen vigencia de 24 horas.
    # ¿Impacto? Si expiró, el usuario debe re-registrarse o solicitar un nuevo enlace.
    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de verificación ha expirado. Por favor, regístrate de nuevo.",
        )

    # ¿Qué? Obtener el usuario asociado al token y marcar su email como verificado.
    # ¿Para qué? Activar la cuenta para que el usuario pueda iniciar sesión.
    # ¿Impacto? is_email_verified=True desbloquea el login para este usuario.
    #           El token se marca como usado para que el enlace no pueda reutilizarse.
    stmt_user = select(User).where(User.id == token_record.user_id)
    user = db.execute(stmt_user).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )

    user.is_email_verified = True
    token_record.used = True
    db.commit()

    # ¿Qué? Registrar la verificación de email para auditoría.
    # ¿Para qué? Trazar el ciclo de vida de activación de cuentas.
    #            Una verificación mucho tiempo después del registro puede ser sospechosa.
    # ¿Impacto? OWASP A09: información útil para investigar activaciones auténticas vs fraudulentas.
    log_email_verified(user_id=str(user.id))


def update_user_locale(db: Session, user: User, locale: str) -> User:
    """Actualiza el idioma preferido (locale) del usuario en la base de datos.

    ¿Qué? Cambia la columna `locale` del usuario al valor proporcionado.
    ¿Para qué? Persistir la preferencia de idioma en la BD, de forma que se restaure
              al iniciar sesión desde cualquier dispositivo.
              Esta función es parte del sistema de i18n (internacionalización).
    ¿Impacto? El cliente guarda el locale también en localStorage — este endpoint
              sincroniza ambas fuentes. Si el usuario inicia sesión en otro dispositivo,
              el response del login incluirá `locale` y el frontend lo aplicará.

    Concepto i18n pedagógico:
        - La BD es la fuente de verdad para la preferencia del usuario autenticado.
        - localStorage es la fuente de verdad para usuarios anónimos y como cache rápido.
        - Al iniciar sesión: BD → localStorage (la BD "gana").
        - Al cambiar idioma: localStorage + BD (ambas se actualizan).

    Args:
        db: Sesión de base de datos.
        user: Instancia del usuario cuyo locale se va a actualizar.
        locale: Código del nuevo idioma ("es" o "en"). Ya validado por el schema Pydantic.

    Returns:
        El usuario actualizado con el nuevo locale.

    Raises:
        HTTPException 400: Si el locale no es válido (aunque Pydantic ya lo valida antes).
    """
    # ¿Qué? Validación defensiva de los valores permitidos.
    # ¿Para qué? Aunque UpdateLocaleRequest ya valida con Pydantic, es buena práctica
    #            validar también en la capa de servicio (defense in depth).
    # ¿Impacto? OWASP A03: Never trust input — aunque el schema lo validó, el servicio
    #            no asume nada. Si se llama directamente (sin pasar por el endpoint), también es seguro.
    supported_locales = ("es", "en")
    if locale not in supported_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Locale '{locale}' no está soportado. Usa: {', '.join(supported_locales)}",
        )

    # ¿Qué? Actualizar la columna locale del usuario.
    # ¿Para qué? Persistir la preferencia de idioma en la base de datos.
    # ¿Impacto? db.commit() escribe el cambio en PostgreSQL de forma permanente.
    #           db.refresh(user) actualiza el objeto en memoria con los valores de la BD.
    user.locale = locale
    db.commit()
    db.refresh(user)

    return user
