"""
Módulo: config.py
Descripción: Configuración centralizada del backend usando Pydantic Settings.
¿Para qué? Cargar y validar TODAS las variables de entorno necesarias al iniciar la app.
           Si falta alguna variable o tiene un formato inválido, la app no arranca y muestra
           un error claro indicando cuál es el problema.
¿Impacto? Sin este módulo, las variables de entorno se leerían con os.getenv() sin validación,
          lo que podría causar errores silenciosos o difíciles de depurar en tiempo de ejecución.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno.

    ¿Qué? Clase que define todas las variables de entorno que necesita el backend.
    ¿Para qué? Centralizar la configuración en un solo lugar con validación automática.
    ¿Impacto? Pydantic valida tipos y valores al instanciar — si DATABASE_URL no es un string
              válido o si SECRET_KEY está vacía, la app falla inmediatamente con un error descriptivo.
    """

    # ────────────────────────────
    # 🗄️ Base de datos
    # ────────────────────────────
    # ¿Qué? URL de conexión a PostgreSQL en formato SQLAlchemy.
    # ¿Para qué? Conectar el backend con la base de datos.
    # ¿Impacto? Si es incorrecta, ninguna operación de lectura/escritura a la BD funcionará.
    DATABASE_URL: str

    # ¿Qué? URL de la BD exclusiva para los tests (servicio db-test del docker-compose).
    # ¿Para qué? Que pytest nunca toque la BD de desarrollo: los tests crean y borran tablas.
    # ¿Impacto? Si falta o apunta a la misma BD que DATABASE_URL, conftest.py detiene los
    #           tests antes de conectarse. La app no la usa: solo la leen los tests.
    TEST_DATABASE_URL: str | None = None

    # ────────────────────────────
    # 🔐 JWT y Seguridad
    # ────────────────────────────
    # ¿Qué? Clave secreta para firmar y verificar tokens JWT.
    # ¿Para qué? Garantizar que solo nuestro backend puede generar tokens válidos.
    # ¿Impacto? Si se filtra, un atacante podría generar tokens falsos y suplantar usuarios.
    #           OWASP A02 — Cryptographic Failures: usar una clave corta o predecible
    #           facilita ataques de fuerza bruta contra la firma del JWT.
    SECRET_KEY: str

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_strength(cls, v: str) -> str:
        """Valida que SECRET_KEY tenga longitud mínima aceptable.

        ¿Qué? Verifica que la clave secreta tenga al menos 32 caracteres.
        ¿Para qué? Una SECRET_KEY corta puede romperse por fuerza bruta, permitiendo
                   al atacante forjar tokens JWT para cualquier usuario.
        ¿Impacto? OWASP A02 — Cryptographic Failures: 32 caracteres es el mínimo
                   recomendado para HMAC-SHA256 (la base de HS256). En producción
                   usar `openssl rand -hex 32` para generar una clave aleatoria segura.

        Args:
            v: Valor de SECRET_KEY de la variable de entorno.

        Returns:
            El valor válido si supera la validación.

        Raises:
            ValueError: Si la clave tiene menos de 32 caracteres.
        """
        if len(v) < 32:  # noqa: PLR2004
            raise ValueError(
                "SECRET_KEY debe tener al menos 32 caracteres. Genera una con: openssl rand -hex 32"
            )
        return v

    # ¿Qué? Algoritmo criptográfico para firmar JWT (HS256 = HMAC con SHA-256).
    # ¿Para qué? Definir cómo se firma el token — HS256 es simétrico (misma clave firma y verifica).
    # ¿Impacto? Cambiar el algoritmo invalida todos los tokens existentes.
    ALGORITHM: str = "HS256"

    # ¿Qué? Tiempo de vida del access token en minutos.
    # ¿Para qué? Limitar la ventana de tiempo en que un token robado es útil.
    # ¿Impacto? Muy corto = el usuario debe re-autenticarse frecuentemente.
    #           Muy largo = mayor riesgo si el token es comprometido.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # ¿Qué? Tiempo de vida del refresh token en días.
    # ¿Para qué? Permitir al usuario obtener nuevos access tokens sin re-ingresar credenciales.
    # ¿Impacto? Define cuánto tiempo puede el usuario permanecer "logueado" sin volver a hacer login.
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ────────────────────────────
    # 📧 Email — Resend
    # ────────────────────────────
    # ¿Qué? API key de Resend para envío de emails transaccionales.
    # ¿Para qué? Autenticar todas las llamadas a la API de Resend (verificación + recuperación).
    # ¿Impacto? Si está vacía, los emails se simulan (se registran en los logs del servidor).
    #           En producción DEBE tener un valor real: obtener en https://resend.com/api-keys
    #           Capa gratuita: 3,000 emails/mes, 100 emails/día — suficiente para desarrollo.
    RESEND_API_KEY: str = ""

    # ¿Qué? Dirección de origen visible en los emails enviados.
    # ¿Para qué? El receptor del email verá este remitente en su cliente de correo.
    # ¿Impacto? Para producción, debe ser un dominio verificado en Resend.
    #           Para desarrollo, "onboarding@resend.dev" funciona sin verificación de dominio.
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    # ¿Qué? Nombre visible del remitente en los emails.
    # ¿Para qué? El usuario ve "NN Auth System <onboarding@resend.dev>" en su bandeja.
    # ¿Impacto? Un nombre reconocible reduce las posibilidades de que el email sea marcado como spam.
    RESEND_FROM_NAME: str = "NN Auth System"

    # ────────────────────────────
    # 📧 Email — SMTP (alternativa a Resend, sin cuenta ni dominio)
    # ────────────────────────────
    # ¿Qué? Configuración del servidor SMTP para envío de emails con smtplib (stdlib de Python).
    # ¿Para qué? Si SMTP_HOST está configurado, se usa en lugar de Resend.
    #           En Docker con Mailpit: SMTP_HOST="mailpit" (hostname del servicio en la red Docker).
    #           En producción con Gmail: SMTP_HOST="smtp.gmail.com", SMTP_PORT=587.
    # ¿Impacto? Si SMTP_HOST está vacío Y RESEND_API_KEY está vacío → emails solo en logs de consola.
    SMTP_HOST: str = ""

    # ¿Qué? Puerto del servidor SMTP.
    # ¿Para qué? Mailpit escucha en 1025; Gmail usa 587 (STARTTLS); el puerto 25 suele estar bloqueado.
    # ¿Impacto? Un puerto incorrecto causará un error de conexión y el email no se enviará.
    SMTP_PORT: int = 1025

    # ¿Qué? Credenciales opcionales para autenticación SMTP.
    # ¿Para qué? Mailpit no requiere autenticación (dejar vacíos). Gmail sí requiere credenciales.
    # ¿Impacto? Para Gmail, usar una "contraseña de aplicación" generada en Google Account Settings,
    #           nunca la contraseña personal. OWASP A02: no hardcodear credenciales en el código.
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # ────────────────────────────
    # 🌐 URLs
    # ────────────────────────────
    # ¿Qué? URL base del frontend.
    # ¿Para qué? Construir enlaces de recuperación de contraseña y configurar CORS.
    # ¿Impacto? Si no coincide con la URL real del frontend, los enlaces de recovery no funcionan
    #           y las peticiones del frontend serán bloqueadas por CORS.
    FRONTEND_URL: str = "http://localhost:5173"

    # ────────────────────────────
    # 🌍 Entorno de ejecución
    # ────────────────────────────
    # ¿Qué? Identifica el entorno en que corre la aplicación.
    # ¿Para qué? Tomar decisiones de seguridad dependientes del entorno — por ejemplo,
    #            deshabilitar Swagger UI (/docs) y ReDoc (/redoc) en producción.
    # ¿Impacto? OWASP A05 — Security Misconfiguration: exponer la documentación interactiva
    #           de la API en producción permite que cualquier persona explore todos los endpoints,
    #           schemas y modelos sin autenticación, facilitando el reconocimiento previo a un ataque.
    #           Valores válidos: "development" | "production" | "testing"
    ENVIRONMENT: str = "development"

    # ¿Qué? Configuración del modelo Pydantic Settings.
    # ¿Para qué? Indicar que las variables se cargan desde el archivo .env en la carpeta be/.
    # ¿Impacto? Sin esto, Pydantic no lee el archivo .env y solo busca variables del sistema.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# ¿Qué? Instancia singleton de la configuración.
# ¿Para qué? Importar `settings` desde cualquier módulo sin re-instanciar la clase.
# ¿Impacto? Se crea UNA sola vez al importar — todas las variables se validan en ese momento.
#           Si falta alguna variable requerida, la app falla aquí con un error claro.
settings = Settings()
