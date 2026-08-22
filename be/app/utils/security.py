"""
Módulo: utils/security.py
Descripción: Utilidades de seguridad — hashing de contraseñas y manejo de tokens JWT.
¿Para qué? Proveer funciones reutilizables de seguridad que se usan en todo el sistema de auth:
           hashear contraseñas, verificar contraseñas, crear tokens JWT y decodificar tokens.
¿Impacto? Es la base de la seguridad del sistema. Un error aquí compromete toda la autenticación.
          Si el hashing falla, las contraseñas quedan en texto plano.
          Si los JWT se generan mal, cualquiera podría suplantar usuarios.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ¿Qué? Contexto de hashing de contraseñas usando bcrypt.
# ¿Para qué? Proveer una interfaz unificada para hashear y verificar contraseñas.
#            bcrypt es un algoritmo diseñado específicamente para contraseñas:
#            es deliberadamente LENTO para dificultar ataques de fuerza bruta.
# ¿Impacto? deprecated="auto" indica que si en el futuro se cambia el algoritmo,
#           los hashes antiguos seguirán siendo verificables (migración gradual).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ¿Qué? Hash bcrypt fijo (sin usuario real detrás), usado por login_user cuando
#       el email no existe, para comparar contra algo y no saltarse el costo de bcrypt.
# ¿Para qué? Igualar el tiempo de respuesta del login exista o no el usuario — el
#            mensaje de error ya es genérico, pero sin esto el timing sigue delatando
#            qué emails están registrados (OWASP A07).
DUMMY_PASSWORD_HASH = "$2b$12$PP42s5XkiNf/2WWHS19shOf.vg.RJnNq7zCJDTCAmQNCrYZdKV85S"


def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano usando bcrypt.

    ¿Qué? Toma una contraseña legible y la convierte en un hash irreversible.
    ¿Para qué? Almacenar la contraseña de forma segura en la base de datos.
              Incluso si la BD es comprometida, las contraseñas no se pueden recuperar.
    ¿Impacto? Si esta función no se usa al registrar/cambiar contraseña, la contraseña
              queda en texto plano = vulnerabilidad CRÍTICA.

    Args:
        password: Contraseña en texto plano ingresada por el usuario.

    Returns:
        Hash bcrypt de la contraseña (~60 caracteres).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con su hash.

    ¿Qué? Compara una contraseña ingresada contra el hash almacenado en la BD.
    ¿Para qué? Validar las credenciales del usuario durante el login y el cambio de contraseña.
    ¿Impacto? Es el mecanismo central de verificación — si falla, nadie puede autenticarse.
              bcrypt internamente aplica el mismo salt del hash original para comparar.

    Args:
        plain_password: Contraseña en texto plano ingresada por el usuario.
        hashed_password: Hash bcrypt almacenado en la base de datos.

    Returns:
        True si la contraseña coincide, False en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT de acceso (access token).

    ¿Qué? Genera un token JWT firmado con la clave secreta del servidor.
    ¿Para qué? El access token es la "credencial temporal" que el cliente envía
              en cada petición para identificarse (header Authorization: Bearer <token>).
    ¿Impacto? Duración corta (15 min por defecto) limita el daño si el token es robado.
              El token contiene el "sub" (subject = email del usuario) y "exp" (expiración).

    Args:
        data: Diccionario con los datos a incluir en el token (mínimo {"sub": email}).
        expires_delta: Tiempo de vida del token. Si no se especifica, usa el valor de config.

    Returns:
        Token JWT como string codificado.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    # ¿Qué? "exp" es un claim estándar de JWT que indica cuándo expira el token.
    # ¿Para qué? El servidor rechaza automáticamente tokens expirados al decodificar.
    # ¿Impacto? Sin expiración, un token robado sería válido para siempre.
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT de refresco (refresh token).

    ¿Qué? Genera un token JWT de larga duración para obtener nuevos access tokens.
    ¿Para qué? Permitir al usuario mantener su sesión sin re-ingresar credenciales.
              Cuando el access token expira, el cliente envía el refresh token para
              obtener uno nuevo sin pedir email/password de nuevo.
    ¿Impacto? Duración larga (7 días por defecto). Si es robado, el atacante puede
              generar access tokens válidos hasta que el refresh expire.
              Por eso es importante protegerlo (httpOnly cookies en producción).

    Args:
        data: Diccionario con los datos a incluir (mínimo {"sub": email}).
        expires_delta: Tiempo de vida. Si no se especifica, usa el valor de config.

    Returns:
        Token JWT de refresco como string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # ¿Qué? "type": "refresh" diferencia este token del access token.
    # ¿Para qué? Evitar que un refresh token sea usado como access token y viceversa.
    # ¿Impacto? Sin esta distinción, un refresh token podría usarse para acceder a endpoints
    #           protegidos, anulando el propósito de tener tokens de corta duración.
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Decodifica y verifica un token JWT.

    ¿Qué? Toma un token JWT string, verifica su firma y expiración, y retorna los datos.
    ¿Para qué? Extraer la identidad del usuario (email) de un token recibido en un request.
    ¿Impacto? Si la firma no coincide o el token expiró, retorna None.
              Esto previene el uso de tokens manipulados o caducados.

    Args:
        token: Token JWT como string.

    Returns:
        Diccionario con los datos del token (payload) si es válido, None si no lo es.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        # ¿Qué? JWTError captura tokens expirados, mal formados, o con firma inválida.
        # ¿Para qué? Manejar todos los errores de JWT en un solo lugar.
        # ¿Impacto? Retornar None en lugar de lanzar excepción permite al caller
        #           decidir cómo manejar el error (401, redirect a login, etc.).
        return None
