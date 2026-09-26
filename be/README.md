# 🐍 Backend — NN Auth System

<!--
  ¿Qué? Guía pedagógica paso a paso para construir el backend del NN Auth System.
  ¿Para qué? Permitir que cualquier aprendiz pueda reproducir la construcción del backend
             sin necesitar ver los videos, entendiendo el "por qué" de cada decisión.
  ¿Impacto? Una guía bien estructurada evita errores de configuración y consolida el aprendizaje.
-->

> Este documento es tu guía completa para entender y reproducir el backend del proyecto.
> Cada sección explica **qué se hace**, **por qué se hace así** y **qué pasaría si no se hiciera**.
> Puedes seguir esta guía de forma independiente a los videos.

---

## Índice

| #   | Sección                                                                                     | Qué aprenderás               |
| --- | ------------------------------------------------------------------------------------------- | ---------------------------- |
| 1   | [Prerrequisitos](#1-prerrequisitos)                                                         | Herramientas necesarias      |
| 2   | [Estructura del backend](#2-estructura-del-backend)                                         | Cómo se organiza el código   |
| 3   | [Entorno virtual Python](#3-entorno-virtual-python-venv)                                    | Aislamiento de dependencias  |
| 4   | [Dependencias (`pyproject.toml`)](#4-dependencias-pyprojecttoml)                        | Cada librería y su rol       |
| 5   | [Variables de entorno](#5-variables-de-entorno)                                             | Configuración segura         |
| 6   | [Configuración (`config.py`)](#6-configuración-configpy)                                    | Pydantic Settings            |
| 7   | [Base de datos (`database.py`)](#7-base-de-datos-databasepy)                                | SQLAlchemy engine y sesión   |
| 8   | [Modelos ORM (`models/`)](#8-modelos-orm-models)                                            | Tablas en Python             |
| 9   | [Migraciones con Alembic](#9-migraciones-con-alembic)                                       | Alterar la BD versionado     |
| 10  | [Schemas Pydantic (`schemas/`)](#10-schemas-pydantic-schemas)                               | Validación de datos          |
| 11  | [Seguridad (`utils/security.py`)](#11-seguridad-utilssecuritypy)                            | Hashing y JWT                |
| 12  | [Dependencias inyectables (`dependencies.py`)](#12-dependencias-inyectables-dependenciespy) | get_db y get_current_user    |
| 13  | [Servicios (`services/`)](#13-servicios-services)                                           | Lógica de negocio            |
| 14  | [Routers y endpoints (`routers/`)](#14-routers-y-endpoints-routers)                         | La API REST                  |
| 15  | [Utilidades adicionales (`utils/`)](#15-utilidades-adicionales-utils)                       | Email, rate limiting, logs   |
| 16  | [Punto de entrada (`main.py`)](#16-punto-de-entrada-mainpy)                                 | FastAPI + middleware         |
| 17  | [Tests con pytest](#17-tests-con-pytest)                                                    | Verificar que todo funciona  |
| 18  | [Ejecutar el servidor](#18-ejecutar-el-servidor)                                            | Comandos del día a día       |
| 19  | [Ejecutar sin Docker](#19-ejecutar-sin-docker)                                              | Alternativa sin contenedores |

---

## 1. Prerrequisitos

Antes de empezar, verifica que tienes instalado:

```bash
# Python 3.12 o superior
python3 --version
# Esperado: Python 3.12.x

# Docker y Docker Compose (para la base de datos)
docker --version
docker compose version
```

> 🖥️ **Usuarios de Windows — leer antes de continuar**
> Todos los comandos de este documento usan sintaxis Bash (`source`, `export`, rutas con `/`, etc.).
> Debes usar **Git Bash** como terminal — viene incluido al instalar
> [Git para Windows](https://git-scm.com/download/win).
> **No uses CMD ni PowerShell** — los comandos de activación del `venv` y demás no
> funcionarán igual. En Git Bash, `source .venv/bin/activate` funciona directamente.

También necesitas tener la base de datos PostgreSQL corriendo. Desde la **raíz del monorepo**:

```bash
# Levanta PostgreSQL 17 en un contenedor Docker
docker compose up -d

# Verifica que está corriendo
docker compose ps
```

> **¿Por qué Docker para la BD?**
> Usar Docker para la base de datos en desarrollo permite que todos los miembros del equipo
> tengan exactamente la misma configuración, sin instalar PostgreSQL directamente en el sistema.
> Un solo comando y la BD está lista.

---

## 2. Estructura del backend

```
be/
├── .env                    # Variables de entorno — NO versionado en git
├── .env.example            # Plantilla de variables — SÍ versionado en git
├── pyproject.toml / uv.lock      # Dependencias Python (uv)
├── alembic.ini             # Configuración de Alembic (migraciones)
├── alembic/
│   ├── env.py              # Conecta Alembic con la BD y los modelos
│   └── versions/           # Archivos de migración (uno por cambio en el esquema)
└── app/                    # Todo el código fuente de la aplicación
    ├── main.py             # Punto de entrada — crea y configura la app FastAPI
    ├── config.py           # Configuración centralizada desde variables de entorno
    ├── database.py         # Engine y sesión de SQLAlchemy
    ├── dependencies.py     # Dependencias inyectables (get_db, get_current_user)
    ├── models/             # Modelos ORM — representan las tablas de la BD
    │   ├── user.py
    │   ├── password_reset_token.py
    │   └── email_verification_token.py
    ├── schemas/            # Schemas Pydantic — validan datos de entrada y salida
    │   └── user.py
    ├── routers/            # Endpoints agrupados por dominio
    │   ├── auth.py         # /api/v1/auth/...
    │   └── users.py        # /api/v1/users/...
    ├── services/           # Lógica de negocio (separada de los endpoints)
    │   └── auth_service.py
    ├── utils/              # Utilidades reutilizables
    │   ├── security.py     # Hashing de contraseñas y tokens JWT
    │   ├── email.py        # Envío de emails
    │   ├── limiter.py      # Rate limiting (instancia global)
    │   └── audit_log.py    # Registro estructurado de eventos de seguridad
    └── tests/
        ├── conftest.py     # Fixtures compartidos entre tests
        ├── test_auth.py    # 43 tests de los endpoints de autenticación
        └── test_security.py # 5 tests unitarios de hashing y JWT
```

> **El patrón de capas**
> El código está organizado en capas con responsabilidades bien separadas:
>
> - **Routers**: reciben la petición HTTP y la delegan al servicio correcto.
> - **Services**: ejecutan la lógica de negocio (consultar BD, hashear, generar tokens).
> - **Models**: representan las tablas de la BD como clases Python.
> - **Schemas**: validan los datos que entran y los que salen.
> - **Utils**: herramientas que usan varias capas (seguridad, email, logs).
>
> Esto se llama **Separation of Concerns** — cada pieza tiene una sola responsabilidad.
> Si el día de mañana cambias de PostgreSQL a MySQL, solo tocas `database.py` y los modelos.

---

## 3. Entorno virtual Python (`venv`)

> **Regla de oro:** NUNCA instalar paquetes en el Python del sistema.
> Siempre usar un entorno virtual aislado por proyecto.

```bash
# Entrar a la carpeta del backend
cd be

# Crear el entorno virtual (se crea la carpeta .venv/ dentro de be/)
python3 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate
# ← Este comando funciona en Linux, macOS y Windows con Git Bash.
#   Si usas Windows, abre Git Bash (no CMD ni PowerShell) y ejecuta el mismo comando.
# Después de activar, el prompt cambia a algo como: (.venv) $

# Verificar que Python apunta al del entorno (no al del sistema)
which python3
# Debe mostrar: .../be/.venv/bin/python3

# Instalar todas las dependencias
uv sync
```

> **¿Por qué `venv`?**
> Imagina que tienes dos proyectos: uno usa `fastapi==0.100` y otro necesita `fastapi==0.115`.
> Sin entornos virtuales, instalar uno rompe el otro. Con `venv`, cada proyecto tiene su propio
> "universo" de paquetes totalmente aislado del sistema y de otros proyectos.

**Para desactivar el entorno** (cuando terminas de trabajar):

```bash
deactivate
```

**La próxima vez que abras una terminal**, vuelves a activarlo:

```bash
cd be && source .venv/bin/activate
```

---

## 4. Dependencias (`pyproject.toml`)

Las dependencias se gestionan con [uv](https://docs.astral.sh/uv/), un gestor de paquetes
ultrarrápido escrito en Rust. El archivo `pyproject.toml` declara todas las dependencias
con versiones exactas, y `uv.lock` garantiza instalaciones 100% reproducibles.

```
# Framework y servidor
fastapi==0.135.1            # El framework web — maneja rutas, requests, responses
uvicorn[standard]==0.42.0   # Servidor ASGI que ejecuta FastAPI
python-multipart==0.0.22    # Necesario para leer form data (como el login)

# ORM y base de datos
sqlalchemy==2.0.48          # ORM — permite manejar la BD con clases Python
alembic==1.18.4             # Migraciones versionadas de la BD
psycopg2-binary==2.9.11     # Driver que conecta Python con PostgreSQL

# Validación y configuración
pydantic==2.12.5            # Validación de datos con tipos Python
pydantic-settings==2.13.1   # Leer y validar variables de entorno
email-validator==2.3.0      # Validar formato de emails (lo usa Pydantic)

# Seguridad
python-jose[cryptography]==3.5.0  # Crear y verificar tokens JWT
passlib[bcrypt]==1.7.4            # Hashear contraseñas con bcrypt
bcrypt==4.0.1                     # Motor de bcrypt (versión fijada por compatibilidad)

# Email
resend==2.25.0              # SDK del servicio de envío de emails Resend

# Testing
pytest==9.0.2               # Framework de testing
pytest-asyncio==1.3.0       # Soporte para funciones async en tests
httpx==0.28.1               # Cliente HTTP para llamar a la API en los tests
pytest-cov==7.0.0           # Medir cobertura de código

# Linting
ruff==0.15.7                # Linter y formateador ultrarrápido
slowapi==0.1.9              # Rate limiting — limita peticiones por IP (seguridad OWASP A04)
```

> **¿Por qué separar testing y linting de producción?**
> En un proyecto de producción, se usarían [dependency groups](https://docs.astral.sh/uv/concepts/dependencies/)
> de uv para separar dev de prod (`uv sync --no-dev`). Aquí los mantenemos
> juntos por simplicidad pedagógica.

> **Comandos útiles con uv:**
> ```bash
> uv sync              # Instalar/actualizar dependencias según uv.lock
> uv add paquete       # Añadir una nueva dependencia
> uv lock              # Regenerar uv.lock después de cambios en pyproject.toml
> uv tree              # Ver el árbol de dependencias
> ```

---

## 5. Variables de entorno

Las variables de entorno almacenan configuración sensible (contraseñas, claves, URLs)
fuera del código fuente. **Nunca** van en el código ni en git.

**Paso 1:** Copia el archivo de ejemplo:

```bash
# Desde be/
cp .env.example .env
```

**Paso 2:** Edita `.env` con tus valores reales:

```bash
# be/.env

# Cadena de conexión a PostgreSQL
# Formato: postgresql://usuario:contraseña@host:puerto/nombre_bd
DATABASE_URL=postgresql://nn_user:nn_password@localhost:5432/nn_auth_db

# Clave secreta para firmar los tokens JWT
# IMPORTANTE: debe tener mínimo 32 caracteres y ser aleatoria
# Genera una con: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=cambia-esto-por-una-clave-aleatoria-de-al-menos-32-chars

# Algoritmo para firmar JWT (HS256 es el estándar para la mayoría de casos)
ALGORITHM=HS256

# Duración del access token en minutos (15 min es el estándar OWASP)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Duración del refresh token en días
REFRESH_TOKEN_EXPIRE_DAYS=7

# API key de Resend para enviar emails
# Si está vacía, los emails se simulan imprimiendo el enlace en la terminal
RESEND_API_KEY=

# Email remitente (visible para el destinatario)
RESEND_FROM_EMAIL=onboarding@resend.dev
RESEND_FROM_NAME=NN Auth System

# ── Email — SMTP (alternativa a Resend, sin cuenta ni dominio) ──
# Con Docker Compose (automático): SMTP_HOST=mailpit ya está en docker-compose.yml
# Sin Docker — Mailpit binario standalone: SMTP_HOST=localhost, SMTP_PORT=1025
#   → Mailpit captura emails localmente, no los envía a internet
#   → Ver todos los emails capturados en http://localhost:8025
# Sin nada — solo logs: dejar SMTP_HOST vacío → enlace aparece en logs de uvicorn
SMTP_HOST=
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=

# URL del frontend (se usa para construir los enlaces en los emails)
FRONTEND_URL=http://localhost:5173

# Entorno de ejecución
# En "production", Swagger UI (/docs) queda desactivado por seguridad
ENVIRONMENT=development
```

> **¿Por qué `.env.example` sí va en git y `.env` no?**
> El `.env.example` muestra QUÉ variables existen (sin valores reales) para que cualquier
> desarrollador nuevo sepa qué configurar. El `.env` tiene las credenciales reales — si
> lo subes a GitHub, cualquiera con acceso al repositorio podría robar tus contraseñas.
> Por eso está en `.gitignore`.

---

## 6. Configuración (`config.py`)

```
app/config.py
```

Este archivo define una clase `Settings` que **lee y valida** todas las variables de entorno
al momento de importarse. Si falta alguna variable obligatoria, la aplicación falla inmediatamente
con un mensaje claro — en lugar de fallar silenciosamente más tarde.

```python
# Fragmento simplificado para entender la estructura
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str                       # obligatorio — falla si no existe
    SECRET_KEY: str                         # obligatorio — validado: min 32 caracteres
    ALGORITHM: str = "HS256"               # opcional — tiene valor por defecto
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # opcional — con default
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # opcional — con default
    RESEND_API_KEY: str = ""               # opcional — si vacío, simula emails
    ENVIRONMENT: str = "development"       # opcional — afecta visibilidad de /docs

    model_config = SettingsConfigDict(
        env_file=".env",            # lee desde el archivo .env
        env_file_encoding="utf-8",
        case_sensitive=True         # DATABASE_URL ≠ database_url
    )

settings = Settings()  # singleton — se valida UNA SOLA VEZ al importar
```

**El patrón singleton:** `settings = Settings()` se ejecuta cuando Python importa el módulo.
Todos los archivos que hagan `from app.config import settings` obtienen la **misma instancia**,
por lo que la validación ocurre una sola vez al arrancar.

> **¿Por qué Pydantic Settings y no `os.getenv()`?**
> Con `os.getenv("SECRET_KEY")` obtienes un string (o `None` si no existe) sin ninguna
> validación. Con Pydantic Settings obtienes tipado, valores por defecto, validadores
> personalizados, y un error claro si algo falta. Es más seguro y más mantenible.

---

## 7. Base de datos (`database.py`)

```
app/database.py
```

Este archivo configura la conexión con PostgreSQL usando SQLAlchemy.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# Engine: objeto que gestiona el pool de conexiones con PostgreSQL
# pool_pre_ping=True → verifica que las conexiones del pool siguen vivas
# echo=False → no imprime cada SQL en la terminal (usar True solo para debug)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)

# SessionLocal: fábrica de sesiones de base de datos
# autocommit=False → los cambios solo se guardan con db.commit() explícito
# autoflush=False  → no sincroniza automáticamente con BD antes de cada query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: clase padre de todos los modelos ORM
# Al heredar de Base, SQLAlchemy sabe que esa clase es una tabla
class Base(DeclarativeBase):
    pass
```

**Tres conceptos clave:**

| Concepto    | Qué es                              | Analogía                              |
| ----------- | ----------------------------------- | ------------------------------------- |
| **Engine**  | Administra las conexiones con la BD | El "gerente" de la conexión           |
| **Session** | Una transacción activa con la BD    | Una "conversación" abierta            |
| **Base**    | Clase padre de los modelos          | El "molde" del que heredan las tablas |

> **¿Por qué `autocommit=False`?**
> Con `autocommit=False`, los cambios en la BD solo se aplican cuando llamas `db.commit()`
> de forma explícita. Esto es fundamental para la **atomicidad**: si un proceso tiene
> 3 pasos y el 2do falla, puedes hacer `db.rollback()` y ningún cambio queda a medias.

---

## 8. Modelos ORM (`models/`)

Los modelos ORM son clases Python que representan tablas en la base de datos.
SQLAlchemy traduce operaciones sobre esas clases a SQL automáticamente.

### 8.1 Tabla `users`

```python
# Fragmento pedagógico — app/models/user.py
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
        # unique=True  → no pueden existir dos usuarios con el mismo email
        # index=True   → búsquedas por email son O(log n) en vez de O(n)
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # ↑ NUNCA almacenamos la contraseña real, solo su hash bcrypt

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        # onupdate=func.now() → se actualiza automáticamente al modificar el registro
    )

    # Relaciones — SQLAlchemy entiende el FK y hace los JOINs automáticamente
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
        # cascade="all, delete-orphan" → eliminar usuario elimina sus tokens también
        # lazy="selectin" → carga los tokens con una query separada pero automática
    )
```

### 8.2 Tabla `password_reset_tokens`

```python
# Fragmento pedagógico — app/models/password_reset_token.py
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),  # si se elimina el usuario, se elimina el token
        nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # used=True → token de un solo uso, no puede volver a usarse
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="password_reset_tokens", lazy="selectin")
```

### 8.3 Tabla `email_verification_tokens`

Estructura idéntica a `password_reset_tokens` pero con `expires_at` de **24 horas** en lugar de 1 hora,
y ligada al campo `is_email_verified` del usuario.

> **¿Por qué usar UUID como primary key en lugar de INTEGER autoincremental?**
> Los UUIDs son globalmente únicos — puedes crear registros en múltiples servidores sin
> que los IDs colisionen. Además, son impredecibles: un atacante no puede adivinar que
> el usuario con `id=5` existe simplemente porque ve que existe `id=4` en la URL.

---

## 9. Migraciones con Alembic

Alembic gestiona los cambios en el esquema de la base de datos de forma **versionada**.
En lugar de ejecutar SQL directamente (que nadie sabe cuándo ni quién lo hizo), cada
cambio es un archivo Python con fecha y descripción.

### 9.1 Inicializar Alembic (ya hecho — solo para referencia)

```bash
# Este comando ya fue ejecutado al crear el proyecto
alembic init alembic
```

### 9.2 El archivo `alembic/env.py`

El archivo más importante de Alembic. Conecta el sistema de migraciones con los modelos
ORM y con la base de datos:

```python
# Fragmento pedagógico del env.py real
from app.database import Base
from app.models import User, PasswordResetToken, EmailVerificationToken  # ← importa modelos
from app.config import settings

# Sobreescribe la URL de BD con el valor del .env (nunca hardcodeada)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata: Alembic compara el estado actual de la BD contra estos modelos
# para saber qué cambios hay que aplicar
target_metadata = Base.metadata
```

> **¿Por qué importar los modelos en `env.py` si no los usamos directamente?**
> Los imports hacen que Python registre esas clases en `Base.metadata`. Sin esos imports,
> Alembic no "sabe" que esas tablas existen y no las incluiría en el auto-detect de cambios.

### 9.3 Crear una migración

```bash
# Asegúrate de estar en be/ con el .venv activado
source .venv/bin/activate

# Auto-generar una migración basada en los modelos actuales
# Alembic compara los modelos ORM con el estado real de la BD y genera el diff
alembic revision --autogenerate -m "create users and password reset tokens"
# Se crea: alembic/versions/xxxx_create_users_and_password_reset_tokens.py
```

### 9.4 Aplicar migraciones

```bash
# Aplicar todas las migraciones pendientes (actualiza la BD al estado más reciente)
alembic upgrade head

# Ver el historial de migraciones aplicadas
alembic history --verbose

# Revertir la última migración (útil para pruebas)
alembic downgrade -1
```

> **Regla fundamental:** NUNCA modificar las tablas directamente con SQL en producción.
> Siempre crear una migración Alembic. Así el historial queda documentado y cualquier
> desarrollador puede reproducir exactamente el mismo estado de la BD ejecutando
> `alembic upgrade head`.

---

## 10. Schemas Pydantic (`schemas/`)

Los schemas definen la "forma" de los datos que entran y salen de la API.
Pydantic valida automáticamente cada campo y retorna errores HTTP 422 si algo no cumple.

### 10.1 Separación REQUEST / RESPONSE

```
Datos que ENTRAN (REQUEST)   →  schemas de entrada  →  validan y limpian datos del cliente
Datos que SALEN  (RESPONSE)  →  schemas de salida   →  controlan qué campos se devuelven
```

Esta separación es crucial por seguridad: aunque el modelo `User` tiene `hashed_password`,
el schema `UserResponse` NO incluye ese campo, por lo que nunca se expone en ninguna respuesta.

### 10.2 Ejemplo comentado

```python
# app/schemas/user.py — Fragmento pedagógico

# Función auxiliar reutilizable para validar fortaleza de contraseña (DRY)
def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in v):
        raise ValueError("La contraseña debe tener al menos una mayúscula")
    if not any(c.islower() for c in v):
        raise ValueError("La contraseña debe tener al menos una minúscula")
    if not any(c.isdigit() for c in v):
        raise ValueError("La contraseña debe tener al menos un número")
    return v

class UserCreate(BaseModel):
    """Schema de REQUEST para registrar un usuario nuevo."""
    email: EmailStr         # Pydantic valida el formato de email automáticamente
    full_name: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()  # elimina espacios al inicio y al final
        if len(v) < 2:
            raise ValueError("El nombre completo debe tener al menos 2 caracteres")
        return v

class UserResponse(BaseModel):
    """Schema de RESPONSE — define qué campos se devuelven al cliente."""
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    # ← hashed_password NO aparece aquí → nunca se expone

    model_config = ConfigDict(from_attributes=True)
    # from_attributes=True → permite crear este schema desde un objeto SQLAlchemy
```

### 10.3 Todos los schemas del proyecto

| Schema                  | Tipo     | Campos principales                                                         |
| ----------------------- | -------- | -------------------------------------------------------------------------- |
| `UserCreate`            | Request  | email, full_name, password                                                 |
| `UserLogin`             | Request  | email, password                                                            |
| `ChangePasswordRequest` | Request  | current_password, new_password                                             |
| `ForgotPasswordRequest` | Request  | email                                                                      |
| `ResetPasswordRequest`  | Request  | token, new_password                                                        |
| `RefreshTokenRequest`   | Request  | refresh_token                                                              |
| `VerifyEmailRequest`    | Request  | token                                                                      |
| `UserResponse`          | Response | id, email, full_name, is_active, is_email_verified, created_at, updated_at |
| `TokenResponse`         | Response | access_token, refresh_token, token_type                                    |
| `MessageResponse`       | Response | message                                                                    |

---

## 11. Seguridad (`utils/security.py`)

Este módulo concentra toda la lógica criptográfica del sistema.

### 11.1 Hashing de contraseñas

```python
from passlib.context import CryptContext

# CryptContext configura el algoritmo de hashing
# bcrypt es lento por diseño: eso dificulta los ataques de fuerza bruta
# Un atacante que robe la BD tardaría años en romper contraseñas bien hasheadas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)
    # Resultado: "$2b$12$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    # El hash incluye: algoritmo + factor de trabajo + salt + hash → todo en una cadena

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña plana coincide con su hash."""
    return pwd_context.verify(plain_password, hashed_password)
    # bcrypt extrae el salt del hash y re-hashea la contraseña plana para comparar
```

> **¿Por qué bcrypt y no SHA-256 o MD5?**
> MD5 y SHA son algoritmos _rápidos_ — diseñados para verificar integridad de archivos.
> bcrypt es deliberadamente _lento_ (configurable), lo que hace inviable el ataque
> de diccionario. Un hash MD5 se puede romper en microsegundos; un hash bcrypt, en años.

### 11.2 Tokens JWT

Un **JWT (JSON Web Token)** es un string firmado que contiene información (claims).
La firma garantiza que nadie puede alterar el contenido sin que lo detectemos.

```
Estructura de un JWT:
eyJhbGciOiJIUzI1NiJ9  .  eyJzdWIiOiJ1c2VyQGV4LmNvbSIsImV4cCI6MTcwMH0  .  firma
      HEADER                              PAYLOAD                          SIGNATURE
(algoritmo)                    (email, expiración, tipo)             (verifica integridad)
```

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un JWT de corta duración (15 min) para autenticar peticiones."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un JWT de larga duración (7 días) para renovar el access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict | None:
    """Verifica y decodifica un JWT. Retorna None si es inválido o expirado."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None  # no lanza excepción — el que llama esta función decide qué hacer
```

**¿Por qué dos tipos de tokens?**

| Token             | Duración   | Para qué se usa                                        |
| ----------------- | ---------- | ------------------------------------------------------ |
| **Access Token**  | 15 minutos | Autenticar cada petición a la API                      |
| **Refresh Token** | 7 días     | Obtener un nuevo access token sin volver a hacer login |

Si un access token es robado, el atacante solo tiene 15 minutos para usarlo.
Si un refresh token es robado, el sistema puede invalidarlo en la BD.

---

## 12. Dependencias inyectables (`dependencies.py`)

FastAPI tiene un sistema de **inyección de dependencias** que permite reutilizar lógica
(como obtener la sesión de BD o verificar el token JWT) en múltiples endpoints sin copiar código.

```python
# app/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.security import decode_token
from app.models.user import User

def get_db():
    """
    Generador que provee una sesión de BD y garantiza su cierre.
    El patrón try/finally asegura que la sesión se cierre aunque ocurra una excepción.
    """
    db = SessionLocal()
    try:
        yield db        # FastAPI inyecta esto en el parámetro del endpoint
    finally:
        db.close()      # siempre se ejecuta, incluso si hay una excepción

# OAuth2PasswordBearer extrae el token del header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),  # extrae el token del header
    db: Session = Depends(get_db)         # inyecta la sesión de BD
) -> User:
    """
    Verifica el token JWT y retorna el usuario autenticado.
    Se usa como dependencia en endpoints que requieren autenticación.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Las credenciales no son válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Verificar que es un access token (no un refresh token)
    if payload.get("type") != "access":
        raise credentials_exception

    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    return user  # este objeto User llega directo al endpoint como parámetro
```

**Cómo se usa en un endpoint:**

```python
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    # FastAPI ejecuta get_current_user() automáticamente antes de llamar esta función
    # Si el token es inválido, FastAPI retorna 401 sin siquiera entrar aquí
    return current_user
```

> **¿Por qué "inyección de dependencias" y no simplemente llamar la función?**
> Porque FastAPI maneja el ciclo de vida automáticamente. Si un endpoint anidado usa
> `Depends(get_db)` y otro también, FastAPI reutiliza la misma sesión dentro de la
> misma petición, y la cierra al terminar — sin que el desarrollador tenga que pensarlo.

---

## 13. Servicios (`services/`)

El archivo `auth_service.py` contiene **toda la lógica de negocio** del sistema de autenticación.
Los routers solo reciben la petición y delegan al servicio — nunca contienen lógica directamente.

### 13.1 ¿Por qué separar servicios de routers?

```
❌ SIN separación (anti-patrón):
router.py → valida JWT + consulta BD + hashea contraseña + envía email + retorna respuesta

✅ CON separación (patrón correcto):
router.py    → recibe petición → llama auth_service.register_user() → retorna respuesta
auth_service.py → consulta BD + hashea contraseña + envía email
```

La separación permite **testear la lógica de negocio** independientemente de HTTP,
reutilizar funciones entre endpoints, y cambiar el framework web sin tocar la lógica.

### 13.2 Flujo de registro

```python
async def register_user(db: Session, user_data: UserCreate) -> User:
    # Paso 1: Verificar email duplicado
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(400, "El email ya está registrado")

    # Paso 2: Crear usuario con contraseña hasheada
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password)  # ← NUNCA texto plano
    )
    db.add(user)
    db.flush()  # asigna el id sin hacer commit (aún dentro de la transacción)

    # Paso 3: Generar token de verificación de email
    verification_token = EmailVerificationToken(
        user_id=user.id,
        token=str(uuid.uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(verification_token)
    db.commit()

    # Paso 4: Enviar email de verificación (no bloqueante — si falla, el usuario igual se crea)
    await send_verification_email(user.email, verification_token.token)

    return user
```

### 13.3 Flujo de login

```python
def login_user(db: Session, login_data: UserLogin) -> TokenResponse:
    # Busca el usuario por email
    user = db.query(User).filter(User.email == login_data.email).first()

    # SEGURIDAD: mensaje genérico — no revela si el email existe o no (anti-enumeración)
    if not user or not verify_password(login_data.password, user.hashed_password):
        log_login_failed(login_data.email, "invalid_credentials")
        raise HTTPException(401, "Las credenciales no son correctas")

    if not user.is_active:
        log_login_failed(login_data.email, "account_inactive")
        raise HTTPException(403, "Cuenta desactivada")

    if not user.is_email_verified:
        raise HTTPException(403, "Debes verificar tu email antes de iniciar sesión")

    log_login_success(user.email)

    return TokenResponse(
        access_token=create_access_token({"sub": user.email}),
        refresh_token=create_refresh_token({"sub": user.email}),
        token_type="bearer"
    )
```

### 13.4 Flujo de recuperación de contraseña

```python
# PASO 1 — Solicitar recuperación
async def request_password_reset(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()

    # SEGURIDAD: retorna silenciosamente aunque el email no exista
    # Así el atacante no puede saber qué emails están registrados en el sistema
    if not user:
        return

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=str(uuid.uuid4()),              # 122 bits de entropía — imposible de adivinar
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db.add(reset_token)
    db.commit()
    await send_password_reset_email(user.email, reset_token.token)

# PASO 2 — Restablecer contraseña con el token
def reset_password(db: Session, reset_data: ResetPasswordRequest) -> None:
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token
    ).first()

    if not token_record:
        raise HTTPException(400, "Token inválido o no encontrado")
    if token_record.used:
        raise HTTPException(400, "Este token ya fue utilizado")
    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "El token ha expirado")

    # Actualizar contraseña y marcar token como usado
    token_record.user.hashed_password = hash_password(reset_data.new_password)
    token_record.used = True
    db.commit()
```

---

## 14. Routers y endpoints (`routers/`)

Los routers agrupan los endpoints por dominio. Cada endpoint es una función que:

1. Recibe la petición HTTP (con datos ya validados por Pydantic)
2. Delega al servicio correspondiente
3. Retorna la respuesta

### 14.1 `auth.py` — Endpoints de autenticación

```python
# app/routers/auth.py — Fragmento pedagógico

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")  # máximo 5 registros por minuto por IP
async def register(
    request: Request,              # necesario para el rate limiter
    user_data: UserCreate,         # Pydantic valida automáticamente (422 si inválido)
    db: Session = Depends(get_db)  # sesión de BD inyectada
):
    """Registra un nuevo usuario. Envía email de verificación."""
    return await auth_service.register_user(db, user_data)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # más permisivo — el login es más frecuente
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    """Autentica al usuario y retorna access + refresh tokens."""
    return auth_service.login_user(db, login_data)

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← requiere JWT válido
):
    """Cambia la contraseña (usuario debe estar autenticado)."""
    auth_service.change_password(db, current_user, password_data)
    return {"message": "Contraseña actualizada correctamente"}
```

### 14.2 Tabla completa de endpoints

| Método | Ruta                           | Auth | Rate Limit | Descripción                    |
| ------ | ------------------------------ | ---- | ---------- | ------------------------------ |
| POST   | `/api/v1/auth/register`        | No   | 5/min      | Registrar nuevo usuario        |
| POST   | `/api/v1/auth/login`           | No   | 10/min     | Iniciar sesión                 |
| POST   | `/api/v1/auth/refresh`         | No\* | —          | Renovar access token           |
| POST   | `/api/v1/auth/change-password` | Sí   | —          | Cambiar contraseña             |
| POST   | `/api/v1/auth/forgot-password` | No   | 5/min      | Solicitar recuperación         |
| POST   | `/api/v1/auth/reset-password`  | No\* | —          | Restablecer contraseña         |
| POST   | `/api/v1/auth/verify-email`    | No\* | —          | Verificar email                |
| GET    | `/api/v1/users/me`             | Sí   | —          | Ver perfil propio              |
| GET    | `/api/v1/health`               | No   | —          | Verificar que la API está viva |

(\*) Requieren un token especial (refresh o verificación), pero no el access token estándar.

---

## 15. Utilidades adicionales (`utils/`)

### 15.1 `email.py` — Envío de emails

```python
# app/utils/email.py — Fragmento pedagógico
# Backend de email — orden de prioridad:
#   1. SMTP_HOST configurado  → smtplib stdlib (ideal para Mailpit local)
#   2. RESEND_API_KEY          → SDK de Resend (requiere dominio verificado)
#   3. Ninguno                 → imprime el enlace en los logs de uvicorn

import asyncio, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import resend
from app.config import settings

def _send_email_smtp(to_email: str, subject: str, html: str) -> None:
    """Envía email via smtplib — funciona con Mailpit y cualquier servidor SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USERNAME:             # Mailpit no requiere auth → se omite
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)

async def send_verification_email(email: str, token: str) -> None:
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "NN Auth System — Verifica tu cuenta"
    html = f'<a href="{verification_url}">Verificar mi cuenta</a>'

    # 1. SMTP disponible (Mailpit en Docker o binario standalone)
    if settings.SMTP_HOST:
        await asyncio.to_thread(_send_email_smtp, email, subject, html)
        return

    # 2. Resend configurado (requiere dominio verificado)
    if settings.RESEND_API_KEY:
        params = {"from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
                  "to": [email], "subject": subject, "html": html}
        await asyncio.to_thread(_send_email_sync, params)
        return

    # 3. Sin backend — mostrar enlace en los logs de uvicorn
    logger.info("📧 ENLACE DE VERIFICACIÓN — Para: %s — Enlace: %s", email, verification_url)
```

> **¿Por qué `asyncio.to_thread()`?**
> FastAPI es asíncrono (async). Si llamamos una función síncrona bloqueante (como el SDK
> de Resend) directamente, bloqueamos el event loop completo: nadie más puede hacer peticiones
> mientras esperamos el email. Con `asyncio.to_thread()`, la llamada síncrona se ejecuta
> en un hilo separado, y el event loop queda libre para otras peticiones.

### 15.2 `limiter.py` — Rate limiting

```python
# app/utils/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia global del limiter — definida aquí para evitar importación circular
# Si estuviera en main.py, auth.py lo importaría generando un ciclo
limiter = Limiter(key_func=get_remote_address)
# key_func=get_remote_address → limita por IP del cliente
```

**Cómo se usa en los routers:**

```python
from app.utils.limiter import limiter

@router.post("/login")
@limiter.limit("10/minute")  # 10 intentos por minuto por IP
async def login(request: Request, ...):
    ...
```

> **¿Por qué limitar peticiones?**
> Sin rate limiting, un atacante puede intentar millones de combinaciones de contraseñas
> en minutos (ataque de fuerza bruta). Limitar a 10 intentos/min hace ese ataque inviable.
> Esto implementa el control **OWASP A07 — Identification and Authentication Failures**.

### 15.3 `audit_log.py` — Registro de eventos de seguridad

```python
# app/utils/audit_log.py — Fragmento pedagógico
import logging
import json

# Logger dedicado solo para eventos de seguridad
audit_logger = logging.getLogger("security.audit")

def log_login_failed(email: str, reason: str, ip: str | None = None) -> None:
    # Solo logueamos el dominio del email (no el usuario) para proteger privacidad
    domain = email.split("@")[-1] if "@" in email else "unknown"
    audit_logger.warning(json.dumps({
        "event": "LOGIN_FAILED",
        "email_domain": domain,    # ← no el email completo
        "reason": reason,          # "invalid_credentials" o "account_inactive"
        "ip": ip,
    }))
    # NEVER: reason="email_not_found" vs "wrong_password" ← permite enumeración de usuarios
```

> **¿Por qué no loguear el email completo?**
> Los logs suelen almacenarse en servicios de terceros (Datadog, Splunk). Si un atacante
> accede a los logs, obtendría una lista de todos los emails que intentaron hacer login.
> Loguear solo el dominio (`@gmail.com`) es suficiente para detectar patrones de ataque
> sin exponer datos personales. Esto implementa **OWASP A09 — Security Logging Failures**.

---

## 16. Punto de entrada (`main.py`)

```python
# app/main.py — Fragmento pedagógico

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.config import settings
from app.utils.limiter import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Se ejecuta al arrancar y al apagar la aplicación."""
    print("✅ NN Auth System iniciando...")
    yield  # ← aquí corre la app
    print("🛑 NN Auth System cerrando...")

# En producción, desactiva Swagger UI (/docs) y ReDoc (/redoc)
# Un atacante no debería ver la documentación de tu API en producción (OWASP A05)
app = FastAPI(
    title="NN Auth System",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Rate limiter global
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — solo permite peticiones desde el frontend (no desde cualquier origen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],    # ← NUNCA ["*"] en producción
    allow_credentials=True,
    allow_methods=["GET", "POST"],            # solo los métodos que usamos
    allow_headers=["Content-Type", "Authorization"],
)

# Headers de seguridad HTTP (middleware personalizado)
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    del response.headers["server"]  # no revelar qué tecnología usamos (fingerprinting)
    return response
```

---

## 17. Tests con pytest

### 17.1 Arquitectura de testing

Los tests corren sobre una **BD exclusiva para pruebas**: el servicio `db-test` del
`docker-compose.yml` (puerto 5433, BD `nn_auth_test`), levantado con
`docker compose up -d --wait db-test`. `conftest.py` lee `TEST_DATABASE_URL` y se detiene si
falta o si es la misma BD que `DATABASE_URL`: los tests borran tablas y nunca deben tocar tus
datos de desarrollo. El envío de emails se reemplaza por un fake (fixture `sent_emails`), así
ningún test manda correos reales.

Los tests usan **rollback por función** para garantizar aislamiento total:

```
Cada test:
  1. INICIA una transacción
  2. EJECUTA el test (crea usuarios, hace peticiones HTTP, etc.)
  3. REVIERTE todo con ROLLBACK
  → La BD queda igual que antes del test, sin importar qué hizo el test
```

Esto es más rápido que re-crear las tablas y garantiza que los tests son independientes
entre sí — pueden correr en cualquier orden sin afectarse.

### 17.2 `conftest.py` — Fixtures compartidos

```python
# app/tests/conftest.py — Fragmento pedagógico

@pytest.fixture(scope="function")
def db():
    """
    Provee una sesión de BD con rollback automático.
    Todos los cambios del test se revierten al terminar.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Maneja los commits internos del servicio sin que salgan de la transacción
    nested = connection.begin_nested()  # savepoint

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            nested.rollback()
            connection.begin_nested()  # nuevo savepoint para el siguiente commit

    yield session  # aquí corre el test

    session.close()
    transaction.rollback()  # ← deshace TODO lo que hizo el test
    connection.close()

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reinicia el contador del rate limiter antes de cada test."""
    yield
    try:
        app.state.limiter._storage.reset()
    except Exception:
        pass
    # sin esto, si un test hace 10 peticiones y el límite es 10/min,
    # el siguiente test fallaría aunque haga solo 1 petición
```

### 17.3 Ejecutar los tests

```bash
# Desde be/ con el .venv activado
cd be && source .venv/bin/activate

# Todos los tests con salida detallada
pytest -v

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Un test específico
pytest app/tests/test_auth.py::TestLogin::test_login_success -v

# Un archivo específico
pytest app/tests/test_auth.py -v
```

### 17.4 Cobertura del proyecto

| Módulo                         | Cobertura |
| ------------------------------ | --------- |
| `app/routers/auth.py`          | ≥ 95%     |
| `app/routers/users.py`         | 100%      |
| `app/services/auth_service.py` | ≥ 90%     |
| `app/utils/security.py`        | 100%      |
| `app/dependencies.py`          | ≥ 85%     |
| **Total**                      | **≥ 90%** |

### 17.5 Tests existentes (43 tests de API)

| Clase de test           | Endpoint              | Casos cubiertos                                                                       |
| ----------------------- | --------------------- | ------------------------------------------------------------------------------------- |
| `TestRegister`          | POST /register        | Éxito, email duplicado, contraseña débil (4 variantes), email inválido, nombre vacío  |
| `TestLogin`             | POST /login           | Éxito, contraseña incorrecta, email inexistente, cuenta inactiva, email no verificado |
| `TestRefresh`           | POST /refresh         | Éxito, token inválido, usar access token como refresh                                 |
| `TestChangePassword`    | POST /change-password | Éxito + verificar login, contraseña actual incorrecta, sin autenticación              |
| `TestForgotPassword`    | POST /forgot-password | Email existente, email inexistente (mismo mensaje — anti-enumeración)                 |
| `TestResetPassword`     | POST /reset-password  | Éxito + verificar login, token inválido, token expirado, token usado                  |
| `TestGetMe`             | GET /users/me         | Éxito, sin autenticación, token inválido                                              |
| `TestEmailVerification` | POST /verify-email    | Éxito + login funciona, token inválido, token expirado, token usado                   |
| `TestHealthCheck`       | GET /health           | Sistema saludable                                                                     |

---

## 18. Ejecutar el servidor

### 18.1 Modo desarrollo (con auto-reload)

```bash
# Desde be/ con el .venv activado
cd be && source .venv/bin/activate

# Arrancar el servidor con recarga automática al guardar cambios
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Verificar que funciona
curl http://localhost:8000/api/v1/health
# Respuesta: {"status":"healthy","project":"NN Auth System","version":"0.1.0"}
```

### 18.2 Swagger UI

Con el servidor corriendo, abre en el navegador:

```
http://localhost:8000/docs
```

Swagger UI te permite probar todos los endpoints directamente desde el navegador,
ver los schemas de request/response y obtener el token JWT para los endpoints protegidos.

> **Recuerda:** En producción (`ENVIRONMENT=production`), Swagger UI está desactivado
> por seguridad. Un atacante no debería tener documentación gratuita de tu API.

### 18.3 Linting con ruff

```bash
# Verificar errores de estilo y problemas de código
ruff check app/

# Formatear el código automáticamente
ruff format app/

# Verificar y formatear de una vez
ruff check --fix app/ && ruff format app/
```

### 18.4 Flujo completo de verificación

```bash
# 1. Base de datos corriendo
docker compose up -d

# 2. Activar entorno virtual
cd be && source .venv/bin/activate

# 3. Aplicar migraciones
alembic upgrade head

# 4. Linting (sin errores antes de testear)
ruff check app/

# 5. Tests completos con cobertura
pytest --cov=app --cov-report=term-missing -v

# 6. Arrancar el servidor
uvicorn app.main:app --reload
```

---

## 19. Ejecutar sin Docker

Si Docker no está disponible en tu entorno (permisos, recursos, o preferencia),
el sistema puede correr completamente sin contenedores.

### 19.1 Opción A — PostgreSQL instalado localmente

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y postgresql

# macOS (Homebrew)
brew install postgresql@17 && brew services start postgresql@17

# Crear usuario y base de datos
sudo -u postgres psql <<SQL
CREATE USER nn_user WITH PASSWORD 'nn_password';
CREATE DATABASE nn_auth_db OWNER nn_user;
\q
SQL
```

Edita `be/.env`:

```bash
DATABASE_URL=postgresql://nn_user:nn_password@localhost:5432/nn_auth_db
```

### 19.2 Opción B — Base de datos cloud gratuita

Servicios como **[Neon](https://neon.tech)**, **[Supabase](https://supabase.com)** o
**[Railway](https://railway.app)** ofrecen planes gratuitos de PostgreSQL.

1. Crear una cuenta y un proyecto en cualquiera de esos servicios.
2. Copiar la **connection string** que te dan (formato `postgresql://...`).
3. Pegarla en `be/.env` como `DATABASE_URL`:

```bash
# Ejemplo (Neon)
DATABASE_URL=postgresql://usuario:contraseña@ep-xxx.us-east-1.aws.neon.tech/nn_auth_db
```

### 19.3 Email sin Docker — Mailpit binario standalone

[Mailpit](https://github.com/axllent/mailpit) también funciona como binario independiente,
sin necesitar Docker:

```bash
# Linux (64-bit)
curl -sSL https://github.com/axllent/mailpit/releases/latest/download/mailpit-linux-amd64.tar.gz \
  | tar -xz
chmod +x mailpit
./mailpit
# → SMTP en localhost:1025 | Web UI en http://localhost:8025

# macOS (Homebrew)
brew install axllent/apps/mailpit
mailpit
```

Luego en `be/.env`:

```bash
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
```

### 19.4 Flujo completo sin Docker

```bash
# Terminal 1 — Mailpit standalone (para capturar emails, opcional)
./mailpit

# Terminal 2 — Backend
cd be && source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload

# Terminal 3 — Frontend
cd fe && pnpm dev
```

> **Sin Mailpit:** Si `SMTP_HOST` está vacío y no hay `RESEND_API_KEY`, el enlace de
> verificación aparece en los logs de uvicorn con el prefijo `📧 ENLACE`.
> Cópialo y ábrelo en el navegador manualmente — es el modo más simple para pruebas rápidas.

---

## Glosario rápido

| Término                  | Qué es en este proyecto                                                        |
| ------------------------ | ------------------------------------------------------------------------------ |
| **ORM**                  | Object-Relational Mapper — SQLAlchemy convierte clases Python en tablas SQL    |
| **Migración**            | Archivo Python que describe un cambio en el esquema de la BD (Alembic)         |
| **Schema Pydantic**      | Clase que define y valida la estructura de los datos de entrada/salida         |
| **JWT**                  | JSON Web Token — string firmado que prueba quién eres sin consultar la BD      |
| **Access Token**         | JWT de corta duración (15 min) para autenticar peticiones                      |
| **Refresh Token**        | JWT de larga duración (7 días) para renovar el access token                    |
| **Hash bcrypt**          | Representación cifrada unidireccional de una contraseña — no se puede revertir |
| **Dependency Injection** | FastAPI ejecuta funciones auxiliares automáticamente antes del endpoint        |
| **CORS**                 | Cross-Origin Resource Sharing — controla quién puede llamar a la API           |
| **Rate Limiting**        | Limitar el número de peticiones por IP/tiempo (OWASP A07)                      |

---

> **Recuerda:** La calidad no es una opción, es una obligación.
> Cada línea de código es una oportunidad de aprender y enseñar.
