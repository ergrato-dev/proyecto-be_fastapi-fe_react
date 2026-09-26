"""
Módulo: tests/conftest.py
Descripción: Fixtures compartidos para todos los tests del backend.
¿Para qué? Configurar una base de datos de testing aislada, un cliente HTTP de pruebas
           y datos de prueba reutilizables que se comparten entre todos los archivos de test.
¿Impacto? Sin estos fixtures, cada test tendría que configurar su propia BD y cliente,
          causando código repetido, tests lentos y riesgo de contaminar datos entre tests.
          La BD de testing se crea y destruye en cada sesión de pytest, garantizando
          que los tests NUNCA afecten la BD de desarrollo/producción.
"""

import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.dependencies import get_db
from app.main import app
from app.models.password_reset_token import PasswordResetToken
from app.models.email_verification_token import EmailVerificationToken
from app.models.user import User
from app.services import auth_service
from app.utils.security import create_access_token, hash_password

# ────────────────────────────
# 🗄️ Configuración de BD de testing
# ────────────────────────────

# ¿Qué? URL de la BD de testing, separada de la BD de desarrollo.
# ¿Para qué? Los tests crean y destruyen TODAS las tablas (drop_all). Sobre la BD de
#            desarrollo eso borraría los datos con los que trabajas.
# ¿Impacto? Sin TEST_DATABASE_URL, o si apunta a la misma BD que DATABASE_URL, los tests
#           se detienen antes de conectarse. Levanta la BD con:
#           docker compose up -d --wait db-test
if not settings.TEST_DATABASE_URL:
    raise RuntimeError(
        "Define TEST_DATABASE_URL (ver be/.env.example): los tests nunca usan la BD de desarrollo"
    )
if settings.TEST_DATABASE_URL == settings.DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL no puede ser la misma BD que DATABASE_URL")
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

# ¿Qué? Engine de SQLAlchemy exclusivo para tests.
# ¿Para qué? Crear conexiones independientes a la BD de testing.
# ¿Impacto? Separar el engine de testing del de la app evita interferencias.
test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

# ¿Qué? Fábrica de sesiones para tests.
# ¿Para qué? Cada test obtiene una sesión de BD limpia y aislada.
# ¿Impacto? autocommit=False y autoflush=False dan control total sobre las transacciones.
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# ────────────────────────────
# 📦 Fixtures de base de datos
# ────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Aplica las migraciones de Alembic a la BD de testing al inicio de la sesión.

    ¿Qué? Fixture que se ejecuta UNA vez por sesión de pytest: `alembic upgrade head`.
    ¿Para qué? Que la BD de testing tenga exactamente el esquema de producción, creado por
              las mismas migraciones. Si una migración está rota, falla aquí y no en el despliegue.
    ¿Impacto? No se borran tablas: cada test deshace sus cambios con rollback (fixture `db`).
              Así la misma BD sirve también a los tests E2E, que migran con el mismo comando.
    """
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Provee una sesión de BD aislada para cada test con rollback automático.

    ¿Qué? Fixture que crea una sesión de BD con transacción que se revierte al final del test.
    ¿Para qué? Cada test comienza con una BD "limpia" — los datos creados en un test
              NO afectan a otros tests (isolation).
    ¿Impacto? Sin rollback, los datos de un test contaminarían al siguiente,
              causando resultados inconsistentes y tests que fallan aleatoriamente.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    # ¿Qué? Configurar el savepoint para nested transactions.
    # ¿Para qué? Si el código de la app hace commit, el savepoint permite
    #            revertir igualmente al final del test.
    # ¿Impacto? Sin esto, un db.commit() en el service haría permanentes los datos
    #           y romperían el aislamiento entre tests.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session: Session, transaction_state: object) -> None:
        """Recrea el savepoint después de cada commit dentro del test."""
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ────────────────────────────
# 🌐 Fixture del cliente HTTP
# ────────────────────────────


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """Provee un cliente HTTP de testing que usa la sesión de BD aislada.

    ¿Qué? TestClient de FastAPI que envía peticiones HTTP sin necesidad de un servidor real.
    ¿Para qué? Simular peticiones HTTP (POST, GET, etc.) en los tests sin levantar uvicorn.
    ¿Impacto? La clave es el dependency_overrides: reemplaza get_db de la app
              por una función que retorna la sesión de testing. Así, los endpoints
              usan la BD de testing con rollback automático.
    """

    def override_get_db() -> Generator[Session, None, None]:
        """Reemplaza la dependencia get_db para usar la sesión de testing."""
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Generator[None, None, None]:
    """Resetea el almacenamiento del rate limiter entre tests.

    ¿Qué? Fixture autouse que limpia los contadores del rate limiter después de cada test.
    ¿Para qué? El TestClient usa siempre la misma IP (testclient). Sin reset, los hits de
               un test se acumulan y los tests posteriores que usen el mismo endpoint
               recibirían 429 Too Many Requests inesperadamente, rompiendo el aislamiento.
    ¿Impacto? OWASP A04 — Rate Limiting es crítico en producción para prevenir fuerza bruta.
               En tests, el reset garantiza que cada prueba sea independiente y reproducible
               sin importar el orden de ejecución.
    """
    yield
    # ¿Qué? Accede al storage interno del rate limiter y llama reset().
    # ¿Para qué? MemoryStorage.reset() borra todos los contadores acumulados.
    # ¿Impacto? Sin esto, el 6to test que llame a /login obtendría 429 porque el
    #           contador acumulado superaría el límite de 10/minute.
    try:
        app.state.limiter._storage.reset()
    except AttributeError:
        pass  # Si el storage no implementa reset(), los límites son suficientemente altos


# ────────────────────────────
# 📧 Doble del envío de emails
# ────────────────────────────


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    """Reemplaza el envío real de emails por un fake que solo los registra.

    ¿Qué? Fixture autouse que cambia send_verification_email y send_password_reset_email
          por funciones que guardan (tipo, email, token) en una lista.
    ¿Para qué? Que ningún test envíe correos reales, aunque el .env local tenga SMTP_HOST
               o RESEND_API_KEY configurados.
    ¿Impacto? Se reemplazan en app.services.auth_service, donde se USAN, no en
              app.utils.email, donde se definen: auth_service ya importó los nombres.
              Un test puede pedir este fixture para verificar qué correos se "enviaron".
    """
    sent: list[tuple[str, str, str]] = []

    async def fake_verification_email(email: str, token: str) -> None:
        sent.append(("verification", email, token))

    async def fake_password_reset_email(email: str, token: str) -> None:
        sent.append(("password_reset", email, token))

    monkeypatch.setattr(auth_service, "send_verification_email", fake_verification_email)
    monkeypatch.setattr(auth_service, "send_password_reset_email", fake_password_reset_email)
    return sent


# ────────────────────────────
# 👤 Fixtures de datos de prueba
# ────────────────────────────

# ¿Qué? Datos constantes para crear usuarios de prueba.
# ¿Para qué? Reutilizar los mismos datos en múltiples tests sin duplicación.
# ¿Impacto? Centralizar datos de prueba facilita cambiarlos si los requisitos cambian.
TEST_USER_EMAIL = "test@nn-company.com"
TEST_USER_FIRST_NAME = "TEST"
TEST_USER_LAST_NAME = "USER"
TEST_USER_PASSWORD = "TestPass123"
UNVERIFIED_USER_EMAIL = "unverified@nn-company.com"


@pytest.fixture()
def test_user(db: Session) -> User:
    """Crea un usuario de prueba en la BD y lo retorna.

    ¿Qué? Fixture que inserta un usuario con datos conocidos en la BD de testing.
    ¿Para qué? Muchos tests necesitan un usuario existente (login, change password, etc.).
              Este fixture evita repetir la lógica de creación en cada test.
    ¿Impacto? El usuario se crea con contraseña hasheada (como lo haría la app real).
              Se revierte automáticamente al final del test gracias al fixture `db`.
    """
    user = User(
        email=TEST_USER_EMAIL,
        first_name=TEST_USER_FIRST_NAME,
        last_name=TEST_USER_LAST_NAME,
        hashed_password=hash_password(TEST_USER_PASSWORD),
        # ¿Qué? El usuario de prueba se crea con email ya verificado.
        # ¿Para qué? Los tests de login, change-password, etc. asumen un usuario activo y verificado.
        # ¿Impacto? Sin esto, todos los tests de login fallarían con 403 "debes verificar tu email".
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def auth_headers(test_user: User) -> dict[str, str]:
    """Genera headers de autenticación con un access token válido.

    ¿Qué? Fixture que crea un token JWT para el usuario de prueba y lo formatea como header.
    ¿Para qué? Reutilizar en cualquier test que necesite autenticación.
    ¿Impacto? Sin esto, cada test protegido tendría que generar su propio token manualmente.
    """
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture()
def expired_reset_token(db: Session, test_user: User) -> str:
    """Crea un token de reset de contraseña ya expirado.

    ¿Qué? Fixture que inserta un token de reset con fecha de expiración en el pasado.
    ¿Para qué? Probar que el endpoint reset-password rechaza tokens expirados.
    ¿Impacto? Verifica una validación de seguridad crítica del sistema.
    """
    token = str(uuid.uuid4())
    token_record = PasswordResetToken(
        user_id=test_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(token_record)
    db.commit()
    return token


@pytest.fixture()
def used_reset_token(db: Session, test_user: User) -> str:
    """Crea un token de reset de contraseña ya utilizado.

    ¿Qué? Fixture que inserta un token de reset marcado como usado (used=True).
    ¿Para qué? Probar que el endpoint reset-password rechaza tokens ya utilizados.
    ¿Impacto? Verifica que un token no pueda reutilizarse para cambiar la contraseña múltiples veces.
    """
    token = str(uuid.uuid4())
    token_record = PasswordResetToken(
        user_id=test_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        used=True,
    )
    db.add(token_record)
    db.commit()
    return token


@pytest.fixture()
def valid_reset_token(db: Session, test_user: User) -> str:
    """Crea un token de reset de contraseña válido (no expirado, no usado).

    ¿Qué? Fixture que inserta un token de reset listo para ser consumido.
    ¿Para qué? Probar el flujo exitoso de reset-password.
    ¿Impacto? Simula el token que el usuario recibiría por email tras forgot-password.
    """
    token = str(uuid.uuid4())
    token_record = PasswordResetToken(
        user_id=test_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(token_record)
    db.commit()
    return token


# ────────────────────────────
# 📧 Fixtures de verificación de email
# ────────────────────────────


@pytest.fixture()
def unverified_user(db: Session) -> User:
    """Crea un usuario sin verificar email (is_email_verified=False).

    ¿Qué? Fixture que inserta un usuario que aún no hizo clic en el enlace de verificación.
    ¿Para qué? Probar que el login rechaza usuarios no verificados.
    ¿Impacto? Simula el estado inmediatamente después del registro, antes de verificar.
    """
    user = User(
        email=UNVERIFIED_USER_EMAIL,
        first_name="Unverified",
        last_name="User",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        is_email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def valid_verification_token(db: Session, unverified_user: User) -> str:
    """Crea un token de verificación de email válido para el usuario no verificado.

    ¿Qué? Fixture que inserta un EmailVerificationToken activo (no expirado, no usado).
    ¿Para qué? Probar el flujo exitoso de verify-email.
    ¿Impacto? Simula el token que se envía al email al registrarse.
    """
    token = str(uuid.uuid4())
    token_record = EmailVerificationToken(
        user_id=unverified_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(token_record)
    db.commit()
    return token


@pytest.fixture()
def expired_verification_token(db: Session, unverified_user: User) -> str:
    """Crea un token de verificación de email ya expirado.

    ¿Qué? Fixture que inserta un EmailVerificationToken con expiración en el pasado.
    ¿Para qué? Probar que el endpoint verify-email rechaza tokens expirados.
    ¿Impacto? Verifica la seguridad: enlaces viejos no pueden activar cuentas.
    """
    token = str(uuid.uuid4())
    token_record = EmailVerificationToken(
        user_id=unverified_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(token_record)
    db.commit()
    return token


@pytest.fixture()
def used_verification_token(db: Session, unverified_user: User) -> str:
    """Crea un token de verificación de email ya utilizado.

    ¿Qué? Fixture que inserta un EmailVerificationToken marcado como used=True.
    ¿Para qué? Probar que el endpoint verify-email rechaza tokens ya consumidos.
    ¿Impacto? Verifica que un enlace no puede reutilizarse para activar la cuenta dos veces.
    """
    token = str(uuid.uuid4())
    token_record = EmailVerificationToken(
        user_id=unverified_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        used=True,
    )
    db.add(token_record)
    db.commit()
    return token
