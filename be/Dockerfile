# ========================
# NN Auth System — Dockerfile del Backend
# ========================
# ¿Qué? Imagen Docker multi-stage para el backend FastAPI.
# ¿Para qué? Separar la instalación de dependencias (builder) del runtime final,
#            generando una imagen más pequeña y segura para producción/desarrollo.
# ¿Impacto? Sin Dockerfile, el backend sólo puede ejecutarse en entornos con Python
#           configurado manualmente. Con él, corre en cualquier máquina que tenga Docker.

# ────────────────────────────
# Stage 1: builder
# ¿Qué? Instala todas las dependencias Python en un venv aislado con uv.
# ¿Para qué? Aprovechar el caché de capas de Docker — si pyproject.toml/uv.lock no cambian,
#            esta capa se reutiliza y el build es mucho más rápido.
# ¿Impacto? Sin este stage, cada rebuild reinstalaría todas las dependencias desde cero.
# ────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar uv — gestor de paquetes ultrarrápido escrito en Rust
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv

# Instalar dependencias directamente en /opt/venv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# ¿Qué? Copia SOLO los archivos de dependencias antes que el resto del código.
# ¿Para qué? Optimizar el caché de Docker — si el código cambia pero pyproject.toml
#            y uv.lock no, Docker reutiliza la capa de instalación de paquetes.
# ¿Impacto? Build hasta 10x más rápido en iteraciones del día a día.
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project


# ────────────────────────────
# Stage 2: runtime
# ¿Qué? Imagen final que se ejecuta en producción/desarrollo.
# ¿Para qué? Contiene solo lo necesario para correr la app — no las herramientas de build.
# ¿Impacto? Imagen más pequeña (~200MB vs ~500MB+), menor superficie de ataque.
# ────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# ¿Qué? Variables de entorno que mejoran el comportamiento de Python en contenedores.
# ¿Para qué?
#   PYTHONDONTWRITEBYTECODE=1 → No genera archivos .pyc (innecesarios en contenedor).
#   PYTHONUNBUFFERED=1        → Los logs aparecen en tiempo real (sin buffer).
# ¿Impacto? Sin PYTHONUNBUFFERED, los logs del servidor podrían aparecer con retraso
#           o no aparecer si el contenedor falla antes de vaciar el buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# ¿Qué? Copia el venv con todas las dependencias instaladas desde el stage builder.
# ¿Para qué? Evitar reinstalar paquetes en el stage runtime — el builder ya lo hizo.
# ¿Impacto? El stage runtime no necesita pip ni compiladores C, lo que reduce la imagen.
COPY --from=builder /opt/venv /opt/venv

# ¿Qué? Copia el código fuente completo del backend al contenedor.
# ¿Para qué? Proveer al servidor uvicorn todos los módulos de la aplicación.
# ¿Impacto? Los archivos en .dockerignore NO se copian (ej: .env, .venv local, __pycache__).
COPY . .

# ¿Qué? Hace ejecutable el entrypoint que corre migraciones + valida el esquema.
# ¿Para qué? sh necesita el bit +x para poder ejecutar el script directamente.
# ¿Impacto? Sin esto, el contenedor falla al arrancar con "Permission denied".
RUN chmod +x docker-entrypoint.sh

# ¿Qué? Documenta que el contenedor escucha en el puerto 8000.
# ¿Para qué? Convención Docker que informa a herramientas y operadores qué puerto usar.
# ¿Impacto? No abre el puerto por sí solo — docker-compose.yml define el mapeo real.
EXPOSE 8000

# ¿Qué? Comando de inicio del contenedor — ver docker-entrypoint.sh.
# ¿Para qué? Corre las migraciones de Alembic, valida que el esquema real coincida con lo
#            que Alembic cree haber aplicado, y solo entonces arranca Uvicorn en 0.0.0.0:8000.
# ¿Impacto? Si el volumen de Postgres queda con alembic_version en head sin las tablas
#           reales (visto en desarrollo), el contenedor falla al arrancar con un mensaje
#           claro en vez de exponer un backend que responde 500 en cada request.
CMD ["./docker-entrypoint.sh"]
