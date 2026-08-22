"""
Módulo: main.py
Descripción: Punto de entrada de la aplicación FastAPI — configura y arranca el servidor.
¿Para qué? Crear la instancia principal de FastAPI, configurar CORS, incluir routers
           y definir el ciclo de vida de la aplicación.
¿Impacto? Este es el archivo que Uvicorn ejecuta. Sin él, no hay servidor.
          Todo endpoint, middleware y configuración se conecta aquí.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging
import sys

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

# ¿Qué? Importación del limiter desde su módulo dedicado.
# ¿Para qué? Evitar una importación circular — si el limiter se definiera aquí,
#            auth.py (que importa limiter) sería importado desde main.py,
#            creando un ciclo: main → auth → main.
# ¿Impacto? Al definirlo en utils/limiter.py (módulo sin dependencias internas),
#           tanto main.py como los routers pueden importarlo sin ciclos.
from app.utils.limiter import limiter


# ¿Qué? Función de ciclo de vida (lifespan) que se ejecuta al iniciar y al cerrar la app.
# ¿Para qué? Realizar tareas de inicialización (ej: verificar conexión a BD) al arrancar
#            y tareas de limpieza (ej: cerrar conexiones) al apagar.
# ¿Impacto? Sin lifespan, no hay un lugar centralizado para código de startup/shutdown,
#           lo que podría causar fugas de recursos o conexiones huérfanas.
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestiona el ciclo de vida de la aplicación FastAPI.

    ¿Qué? Context manager async que se ejecuta al inicio y al cierre del servidor.
    ¿Para qué? Ejecutar lógica de arranque (verificaciones, logs) y limpieza (cerrar pools).
    ¿Impacto? El código antes de `yield` se ejecuta al INICIAR.
              El código después de `yield` se ejecuta al CERRAR.
    """
    # --- Startup ---
    # ¿Qué? Configura el logger del paquete `app` con un StreamHandler a stdout.
    # ¿Para qué? Uvicorn NO agrega handlers al root logger — solo configura sus propios
    #            loggers (uvicorn, uvicorn.access). Sin un handler explícito, los logs
    #            INFO/ERROR de `app.utils.email`, `app.services.*`, etc. se pierden.
    # ¿Impacto? Igual que audit_log.py que sí añade su StreamHandler, esto garantiza
    #           que `logger.info/error/warning` del paquete `app` aparezcan en
    #           `docker logs nn_auth_be`.
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    if not app_logger.handlers:
        _handler = logging.StreamHandler(sys.stdout)
        _handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        app_logger.addHandler(_handler)
        app_logger.propagate = False
    print("🚀 NN Auth System — Backend iniciando...")
    print(f"📡 CORS habilitado para: {settings.FRONTEND_URL}")
    yield
    # --- Shutdown ---
    print("🛑 NN Auth System — Backend cerrando...")


# ¿Qué? Instancia principal de la aplicación FastAPI.
# ¿Para qué? Es el objeto central que recibe las peticiones HTTP, las enruta a los
#            endpoints correctos y devuelve las respuestas.
# ¿Impacto? Los metadatos (title, description, version) aparecen automáticamente
#           en la documentación interactiva de Swagger UI (/docs).
#
# OWASP A05 — Security Misconfiguration:
# En producción, /docs y /redoc se deshabilitan para evitar exponer la superficie
# de ataque de la API a cualquier visitante sin autenticación.
# En desarrollo y testing se mantienen activos para facilitar el trabajo del equipo.
_is_production = settings.ENVIRONMENT == "production"
app = FastAPI(
    title="NN Auth System",
    description=(
        "🔐 Sistema de autenticación completo para la empresa NN. "
        "Incluye registro, login, cambio y recuperación de contraseña. "
        "Proyecto educativo — SENA."
    ),
    version="0.1.0",
    # ¿Qué? docs_url/redoc_url = None desactiva esas rutas completamente.
    # ¿Para qué? Nadie puede explorar la documentación interactiva en producción.
    # ¿Impacto? El equipo de desarrollo sigue teniendo /docs localmente (ENVIRONMENT=development).
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    lifespan=lifespan,
)

# ¿Qué? Registra el limiter en el estado de la app y el handler de error 429.
# ¿Para qué? SlowAPIMiddleware necesita encontrar el limiter en app.state.limiter.
#            El handler convierte RateLimitExceeded en una respuesta HTTP 429 estándar.
# ¿Impacto? Sin el handler, un rate limit superado causaría un 500 Internal Server Error
#           en lugar del semánticamente correcto 429 Too Many Requests.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ¿Qué? Middleware CORS (Cross-Origin Resource Sharing).
# ¿Para qué? Permitir que el frontend (http://localhost:5173) haga peticiones HTTP al backend
#            (http://localhost:8000), que técnicamente está en un "origen" diferente.
# ¿Impacto? Sin CORS, el navegador BLOQUEA todas las peticiones del frontend al backend
#           por política de seguridad del mismo origen (Same-Origin Policy).
#
# OWASP A05 — Security Misconfiguration:
# ❌ INCORRECTO: allow_methods=["*"] y allow_headers=["*"] son excesivamente permisivos.
#    Un XSS podría explotar métodos como DELETE o PUT con headers arbitrarios.
# ✅ CORRECTO: Especificar exactamente qué métodos y headers necesita la app.
#    Esta API solo usa GET y POST; los headers son Content-Type y Authorization.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,  # Único origen permitido — el frontend de desarrollo
    ],
    allow_credentials=True,
    # ¿Qué? Solo los métodos HTTP que realmente usa la API.
    # ¿Para qué? Prevenir que un XSS cause peticiones DELETE/PUT desde el origen permitido.
    # ¿Impacto? Si un endpoint necesita PUT o DELETE en el futuro, se agrega aquí explícitamente.
    allow_methods=["GET", "POST"],
    # ¿Qué? Solo los headers que la API necesita recibir del frontend.
    # ¿Para qué? Limitar la superficie de ataque — headers arbitrarios no deben aceptarse.
    # ¿Impacto? Content-Type para JSON, Authorization para JWT. Nada más es necesario.
    allow_headers=["Content-Type", "Authorization"],
)


# ¿Qué? Middleware de cabeceras de seguridad HTTP.
# ¿Para qué? Instruir al navegador a activar protecciones adicionales contra ataques
#            comunes como XSS, clickjacking e inyección de MIME type.
# ¿Impacto? Corresponde a OWASP A05 (Security Misconfiguration). La ausencia de estas
#           cabeceras no causa ataques directamente, pero permite que los ataques sean
#           más efectivos. Son baratas de implementar y muy valiosas como defensa en profundidad.
@app.middleware("http")
async def add_security_headers(request: Request, call_next: object) -> Response:
    """Añade cabeceras de seguridad HTTP a todas las respuestas.

    ¿Qué? Middleware que intercepta todas las respuestas y les agrega headers de seguridad.
    ¿Para qué? Activar protecciones del navegador que reducen el impacto de vulnerabilidades
               como XSS, clickjacking y sniffing de contenido.
    ¿Impacto? Cada header hace una cosa específica — ver comentarios inline.
    """
    response: Response = await call_next(request)  # type: ignore[operator]

    # ¿Qué? Evita que el navegador detecte el MIME type del contenido (sniffing).
    # ¿Para qué? Prevenir que un archivo .txt con código JS sea ejecutado como script.
    # ¿Impacto? Si se omite, un atacante puede subir un archivo con MIME incorrecto
    #           y causar su ejecución como script malicioso.
    response.headers["X-Content-Type-Options"] = "nosniff"

    # ¿Qué? Impide que la app se embeba en un <iframe> de otro sitio.
    # ¿Para qué? Prevenir ataques de clickjacking — el atacante sobrepone un iframe
    #            invisible de la app sobre un botón atractivo para capturar clicks.
    # ¿Impacto? Con DENY, ningún iframe puede embeber esta app, sin importar el origen.
    response.headers["X-Frame-Options"] = "DENY"

    # ¿Qué? Controla cuánta información de referencia se envía al navegar a otro sitio.
    # ¿Para qué? Evitar filtrar la URL completa (con tokens en query string) como Referer.
    # ¿Impacto? Con strict-origin-when-cross-origin, solo se envía el origen (no la ruta)
    #           al navegar a otro dominio — protege tokens o IDs en URLs.
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # ¿Qué? Política de permisos para APIs del navegador (cámara, micrófono, geolocalización).
    # ¿Para qué? Una API de autenticación no necesita acceder a ningún hardware del dispositivo.
    #            Restringir estas APIs reduce la superficie de ataque si hay XSS.
    # ¿Impacto? Si la app embebiera contenido de terceros, este header limita lo que pueden hacer.
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # ¿Qué? Elimina el header Server que Uvicorn/Starlette agrega por defecto.
    # ¿Para qué? Prevenir que atacantes sepan qué tecnología usa el servidor (fingerprinting).
    # ¿Impacto? Conocer que el servidor es "uvicorn" ayuda a atacantes a buscar exploits
    #           específicos de esa versión. "Seguridad por oscuridad" no es suficiente,
    #           pero eliminar información gratuita siempre es buena práctica.
    if "server" in response.headers:
        del response.headers["server"]

    return response


# ────────────────────────────
# 📍 Incluir routers
# ────────────────────────────

# ¿Qué? Registro de los routers de autenticación y usuarios en la app.
# ¿Para qué? Conectar todos los endpoints definidos en los módulos routers/ a la aplicación
#            principal, para que FastAPI pueda enrutarlos correctamente.
# ¿Impacto? Sin include_router(), los endpoints de auth y users NO existirían — las
#           peticiones a /api/v1/auth/* y /api/v1/users/* retornarían 404.
app.include_router(auth_router)
app.include_router(users_router)


# ────────────────────────────
# 📍 Endpoint de salud (health check)
# ────────────────────────────
@app.get(
    "/api/v1/health",
    tags=["health"],
    summary="Verificar estado del servidor",
)
async def health_check() -> dict[str, str]:
    """Endpoint de verificación de salud del servidor.

    ¿Qué? Retorna un JSON simple indicando que el servidor está activo.
    ¿Para qué? Permitir a herramientas de monitoreo, Docker healthchecks o desarrolladores
              verificar rápidamente que el backend responde.
    ¿Impacto? Si este endpoint no responde, significa que el servidor está caído.
              Es el primer endpoint a probar tras levantar el servidor.

    Returns:
        Diccionario con el estado del servidor y el nombre del proyecto.
    """
    return {
        "status": "healthy",
        "project": "NN Auth System",
        "version": "0.1.0",
    }
