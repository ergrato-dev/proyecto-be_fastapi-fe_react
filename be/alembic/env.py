"""
Módulo: alembic/env.py
Descripción: Configuración del entorno de ejecución de Alembic para migraciones.
¿Para qué? Conectar Alembic con nuestra base de datos y nuestros modelos ORM,
           para que pueda detectar cambios en los modelos y generar migraciones automáticamente.
¿Impacto? Sin esta configuración personalizada, Alembic no sabría dónde está la BD
          ni qué modelos existen, y las migraciones auto-generadas estarían vacías.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ¿Qué? Importamos la Base de SQLAlchemy y todos los modelos.
# ¿Para qué? Alembic necesita acceso a Base.metadata para comparar el estado actual
#            de los modelos con el estado de la BD y detectar diferencias.
# ¿Impacto? El import de app.models ejecuta models/__init__.py, que a su vez importa
#           User y PasswordResetToken. Sin estos imports, autogenerate no detecta nada.
from app.database import Base
from app.models import User, PasswordResetToken, EmailVerificationToken  # noqa: F401 — necesarios para autogenerate
from app.config import settings

# ¿Qué? Objeto de configuración de Alembic que lee alembic.ini.
# ¿Para qué? Acceder a valores del archivo .ini (rutas, logging, etc.).
config = context.config

# ¿Qué? Sobreescribimos la URL de la BD con el valor de nuestro archivo .env.
# ¿Para qué? Evitar hardcodear credenciales en alembic.ini.
# ¿Impacto? Alembic usará la misma DATABASE_URL que el backend, garantizando consistencia.
#           Si quien invoca a Alembic ya fijó una URL (los tests, con TEST_DATABASE_URL),
#           se respeta esa: así las migraciones corren sobre la BD de pruebas.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ¿Qué? Configura el sistema de logging de Python según alembic.ini.
# ¿Para qué? Ver mensajes informativos durante las migraciones (ej: "Running upgrade ...").
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ¿Qué? Metadata de todos los modelos ORM registrados en Base.
# ¿Para qué? Alembic compara este metadata contra el estado real de la BD
#            para generar migraciones automáticas (autogenerate).
# ¿Impacto? Si target_metadata es None, autogenerate no detecta ningún cambio.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline' (sin conexión a la BD).

    ¿Qué? Genera el SQL de las migraciones como texto sin ejecutarlo.
    ¿Para qué? Revisar el SQL antes de ejecutarlo, o generar scripts para DBAs.
    ¿Impacto? Útil para entornos donde no se tiene acceso directo a la BD.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online' (con conexión activa a la BD).

    ¿Qué? Conecta a la BD real y aplica las migraciones directamente.
    ¿Para qué? Es el modo estándar de ejecución — modifica las tablas en la BD.
    ¿Impacto? Cada migración altera la estructura de la BD. Siempre hacer backup
              antes de ejecutar migraciones en producción.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ¿Qué? Punto de entrada — decide si ejecutar en modo offline u online.
# ¿Para qué? Alembic soporta ambos modos; el modo se determina por flags de línea de comandos.
# ¿Impacto? Por defecto se usa modo online (conexión real a la BD).
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
