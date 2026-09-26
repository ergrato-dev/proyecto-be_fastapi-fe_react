"""
Módulo: utils/limiter.py
Descripción: Instancia centralizada del rate limiter de slowapi.
¿Para qué? Evitar importaciones circulares — tanto main.py como los routers
           necesitan acceder al mismo objeto Limiter. Al definirlo aquí, en un
           módulo sin dependencias de app, ambos pueden importarlo sin ciclos.
¿Impacto? OWASP A04 — Insecure Design: sin rate limiting, los endpoints de
           autenticación son vulnerables a ataques de fuerza bruta. Un atacante
           podría probar miles de contraseñas por segundo sin ningún obstáculo.
           slowapi integra el rate limiting directamente en el ciclo de vida de FastAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# ¿Qué? Instancia global del rate limiter compartida por main.py y todos los routers.
# ¿Para qué? Los decoradores @limiter.limit() en los routers necesitan referenciar
#            el MISMO objeto Limiter que está registrado en app.state.limiter.
#            Si cada módulo creara su propio Limiter, los contadores estarían
#            desincronizados y el rate limiting no funcionaría.
# ¿Impacto? Al importar desde este módulo neutral, tanto main.py como auth.py
#           obtienen la misma instancia — se rompe el ciclo de importación circular.
#
# get_remote_address: extrae la IP del cliente desde request.client.host.
# En producción detrás de un proxy/load balancer (nginx, AWS ALB), configurar
# el proxy para enviar X-Forwarded-For y usar get_ipaddr en su lugar.
# ¿Qué? enabled=False desactiva todos los límites (solo para los tests E2E; ver config.py).
limiter = Limiter(key_func=get_remote_address, enabled=settings.RATE_LIMIT_ENABLED)
