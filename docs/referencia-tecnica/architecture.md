# Arquitectura del Sistema — NN Auth System

<!--
  ¿Qué? Documentación de la arquitectura general del sistema NN Auth System.
  ¿Para qué? Que cualquier desarrollador entienda cómo interconectan los módulos,
             capas y responsabilidades antes de leer el código fuente.
  ¿Impacto? Sin este documento, un desarrollador nuevo tardaría horas en entender
             por qué el código está estructurado así y cuál es el flujo de cada operación.
             Este documento reduce significativamente el tiempo de onboarding.
-->

> **Proyecto**: NN Auth System 
> **Stack**: FastAPI (Python 3.12) + React (TypeScript) + PostgreSQL 17 + Docker
> **Tests**: 48/48 backend (43 de API + 5 unitarios) · 165/165 frontend · 3 E2E (Playwright)

---

## Vista General del Sistema

El sistema sigue una **arquitectura Cliente–Servidor de 3 capas**, donde cada capa tiene
una responsabilidad única y se comunica solo con la capa adyacente:

```
┌──────────────────────────────────────────────────────────────────┐
│  CAPA 3 — CLIENTE (Navegador Web)                                │
│                                                                  │
│  React 18 + TypeScript + TailwindCSS + React Router              │
│  http://localhost:5173                                           │
│                                                                  │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────┐ │
│  │   Pages     │  │   Components    │  │  Context / Hooks     │ │
│  │  (vistas)   │  │  (UI + Layout)  │  │  (estado de auth)    │ │
│  └──────┬──────┘  └────────┬────────┘  └──────────────────────┘ │
│         │                  │                                     │
│         └──────────────────┤                                     │
│                            ▼                                     │
│  ┌───────────────────────────────────┐                           │
│  │   api/auth.ts + api/axios.ts      │  (HTTP + JWT)             │
│  └───────────────────────────────────┘                           │
└──────────────────────────────────────████████████████████────────┘
                                        ↕ JSON / HTTPS
┌──────────────────────────────────────████████████████████────────┐
│  CAPA 2 — SERVIDOR (Backend API)                                 │
│                                                                  │
│  FastAPI + Uvicorn (ASGI)                                        │
│  http://localhost:8000                                           │
│                                                                  │
│  ┌────────────┐   ┌─────────────┐   ┌────────────┐              │
│  │  Routers   │ → │  Services   │ → │  Utils     │              │
│  │ (endpoints)│   │  (lógica)   │   │ (sec/email)│              │
│  └────────────┘   └─────────────┘   └────────────┘              │
│         │                 │                 │                    │
│         ▼                 ▼                 ▼                    │
│  ┌───────────────────────────────────────────────┐               │
│  │  Schemas (Pydantic) + Models (SQLAlchemy ORM) │               │
│  └───────────────────────────────────────────────┘               │
└──────────────────────────────────────████████████████████────────┘
                                        ↕ SQL (psycopg2)
┌──────────────────────────────────────████████████████████────────┐
│  CAPA 1 — DATOS (Base de Datos)                                  │
│                                                                  │
│  PostgreSQL 17 (Docker Container)                                │
│  localhost:5432                                                  │
│                                                                  │
│  ┌──────┐  ┌──────────────────────┐  ┌─────────────────────┐    │
│  │users │  │password_reset_tokens │  │email_verification_  │    │
│  │      │  │                      │  │tokens               │    │
│  └──────┘  └──────────────────────┘  └─────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Arquitectura del Backend (`be/`)

### Estructura de capas

```
be/app/
│
├── main.py          ← Punto de entrada: FastAPI app, CORS, middleware, routers
├── config.py        ← Variables de entorno con Pydantic Settings
├── database.py      ← Engine + Session de SQLAlchemy
├── dependencies.py  ← Dependencias inyectables: get_db(), get_current_user()
│
├── routers/         ← CAPA DE PRESENTACIÓN (HTTP)
│   ├── auth.py      ← POST /register, /login, /refresh, /change-password,
│   │                   /forgot-password, /reset-password, /verify-email
│   └── users.py     ← GET /me
│
├── services/        ← CAPA DE LÓGICA DE NEGOCIO
│   └── auth_service.py  ← register_user, login_user, refresh_access_token,
│                            change_password, request_password_reset,
│                            reset_password, verify_email
│
├── models/          ← CAPA DE DATOS (ORM)
│   ├── user.py      ← Tabla users
│   ├── password_reset_token.py   ← Tabla password_reset_tokens
│   └── email_verification_token.py ← Tabla email_verification_tokens
│
├── schemas/         ← VALIDACIÓN (Pydantic)
│   └── user.py      ← UserCreate, UserLogin, UserResponse, TokenResponse,
│                       ChangePasswordRequest, ForgotPasswordRequest,
│                       ResetPasswordRequest, VerifyEmailRequest, MessageResponse
│
└── utils/           ← UTILIDADES TRANSVERSALES
    ├── security.py  ← hash_password, verify_password, create_access_token,
    │                   create_refresh_token, decode_token
    ├── email.py     ← send_verification_email, send_password_reset_email
    ├── limiter.py   ← Instancia de SlowAPI (rate limiter)
    └── audit_log.py ← log_login_success/failed, log_password_changed, etc.
```

### Flujo de una petición HTTP

```
1. Cliente envía:   POST /api/v1/auth/login { email, password }
                    ↓
2. FastAPI valida   El schema `UserLogin` (Pydantic) valida email y password
   el body:         Si hay errores de validación → 422 automático
                    ↓
3. Rate limiting:   @limiter.limit("10/minute") verifica si la IP superó el límite
                    Si sí → 429 Too Many Requests
                    ↓
4. Router:          routers/auth.py::login() recibe los datos validados
                    Llama a auth_service.login_user(db, login_data)
                    ↓
5. Service:         auth_service.login_user():
                    - Busca user por email (db.query(User).filter(email=...))
                    - Verifica password: verify_password(plain, hashed)
                    - Verifica is_email_verified y is_active
                    - Genera access_token y refresh_token
                    - Llama a audit_log.log_login_success(...)
                    ↓
6. Response:        Router retorna TokenResponse(access_token, refresh_token, token_type)
                    FastAPI serializa a JSON con el response_model
```

### Seguridad en el backend

```
┌────────────────────────────────────────────────────────────┐
│  Capas de seguridad (de afuera hacia adentro)              │
│                                                            │
│  1. CORS Middleware          → Solo FRONTEND_URL           │
│  2. Security Headers         → X-Frame-Options, nosniff   │
│  3. Rate Limiter (slowapi)   → Por IP, por endpoint        │
│  4. Pydantic Validation      → Tipos, formato, fortaleza   │
│  5. JWT Verification         → get_current_user dependency │
│  6. Business Logic Checks    → is_active, is_email_verified│
│  7. SQLAlchemy ORM           → No raw SQL, no injection    │
│  8. bcrypt Hashing           → Contraseñas nunca en plano  │
│  9. Audit Logging            → Trazabilidad de eventos     │
└────────────────────────────────────────────────────────────┘
```

---

## Arquitectura del Frontend (`fe/`)

### Estructura de capas

```
fe/src/
│
├── main.tsx         ← Punto de entrada: renderiza <App /> en el DOM
├── App.tsx          ← Rutas de la aplicación (React Router)
├── index.css        ← Estilos globales + imports de TailwindCSS
│
├── context/         ← ESTADO GLOBAL
│   ├── AuthContext.tsx     ← Provider: usuario actual, tokens, loading
│   └── authContextDef.ts   ← Definición de tipos del contexto
│
├── hooks/           ← LÓGICA REUTILIZABLE
│   └── useAuth.ts   ← Acceso al contexto de auth desde cualquier componente
│
├── api/             ← COMUNICACIÓN HTTP
│   ├── auth.ts      ← Funciones: register, login, refresh, changePassword, etc.
│   └── axios.ts     ← Instancia de Axios con interceptores JWT automáticos
│
├── components/      ← COMPONENTES REUTILIZABLES
│   ├── ProtectedRoute.tsx  ← Guarda de rutas autenticadas
│   ├── layout/
│   │   ├── AuthLayout.tsx  ← <main> landmark para páginas de auth
│   │   └── Navbar.tsx      ← Barra de navegación con tema y logout
│   └── ui/
│       ├── Button.tsx      ← Botón con estado loading (aria-busy)
│       ├── InputField.tsx  ← Input con label, ícono, validación y a11y
│       └── Alert.tsx       ← Mensajes de éxito/error/info
│
├── pages/           ← VISTAS (una por ruta)
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── DashboardPage.tsx
│   ├── ChangePasswordPage.tsx
│   ├── ForgotPasswordPage.tsx
│   ├── ResetPasswordPage.tsx
│   └── DataTableDemoPage.tsx
│
└── types/           ← TIPOS TYPESCRIPT
    └── auth.ts      ← LoginRequest, RegisterRequest, UserResponse, TokenResponse, etc.
```

### Rutas de la aplicación

```
/                → Redirige a /login o /dashboard (según auth)
/login           → LoginPage (pública)
/register        → RegisterPage (pública)
/forgot-password → ForgotPasswordPage (pública)
/reset-password  → ResetPasswordPage (pública, requiere ?token=...)
/verify-email    → (manejado con ?token=...) → llama al backend
/dashboard       → DashboardPage (PROTEGIDA — requiere auth)
/change-password → ChangePasswordPage (PROTEGIDA — requiere auth)
/demo/datatable  → DataTableDemoPage (PROTEGIDA — requiere auth)
```

### Flujo de autenticación en el frontend

```
Arranque de la app:
1. AuthContext se monta → lee access_token de memoria (no localStorage)
2. Si hay token → verifica con GET /api/v1/users/me
3. Si 200 → usuario autenticado, redirecciona a /dashboard
4. Si 401 → intenta refresh con POST /api/v1/auth/refresh
5. Si refresh falla → usuario va a /login

Login exitoso:
1. LoginPage → auth.login(email, password) → TokenResponse
2. AuthContext guarda tokens en memoria (no localStorage por seguridad)
3. GET /api/v1/users/me → guarda perfil en estado
4. React Router navega a /dashboard

Acceso a ruta protegida sin token:
1. <ProtectedRoute> detecta que no hay usuario autenticado
2. Muestra spinner (role="status") mientras verifica
3. Si no autenticado → <Navigate to="/login" />

Expiración del access_token (15 min):
1. Axios interceptor detecta 401 en respuesta
2. Automáticamente llama POST /api/v1/auth/refresh
3. Si refresh exitoso → reintenta la petición original
4. Si refresh falla → logout + redirect a /login
```

---

## Flujos de Autenticación de Extremo a Extremo

### Flujo 1 — Registro y Verificación de Email

```
Usuario                  Frontend (React)            Backend (FastAPI)         Email (Resend)
   │                           │                             │                      │
   │ Rellena formulario        │                             │                      │
   │ ─────────────────────────►│                             │                      │
   │                           │ POST /auth/register         │                      │
   │                           │────────────────────────────►│                      │
   │                           │                             │ 1. Valida Pydantic   │
   │                           │                             │ 2. Verifica email ∄  │
   │                           │                             │ 3. Hash bcrypt       │
   │                           │                             │ 4. Crea User (is_email_verified=false)
   │                           │                             │ 5. Crea EmailVerificationToken
   │                           │                             │ 6. send_verification_email()
   │                           │                             │─────────────────────►│
   │                           │◄────────────────────────────│                      │
   │ Ve mensaje "Verifica email"│  201 UserResponse           │  Envía email con token
   │◄──────────────────────────│                             │                      │
   │                           │                             │                      │
   │ Hace clic en el enlace    │                             │                      │
   │ ─────────────────────────►│                             │                      │
   │                           │ POST /auth/verify-email     │                      │
   │                           │────────────────────────────►│                      │
   │                           │                             │ 1. Busca token en BD │
   │                           │                             │ 2. Verifica no expirado
   │                           │                             │ 3. Marca used=true   │
   │                           │                             │ 4. is_email_verified=true
   │                           │◄────────────────────────────│                      │
   │ "Verificado, ya puedes login"  200 MessageResponse       │                      │
   │◄──────────────────────────│                             │                      │
```

### Flujo 2 — Login y Acceso a Dashboard

```
Usuario           Frontend                Backend               PostgreSQL
   │                 │                       │                       │
   │ email+password  │                       │                       │
   │────────────────►│                       │                       │
   │                 │ POST /auth/login       │                       │
   │                 │──────────────────────►│                       │
   │                 │                       │ SELECT * FROM users   │
   │                 │                       │ WHERE email = $1 ────►│
   │                 │                       │◄──────────────────────│
   │                 │                       │ verify_password()     │
   │                 │                       │ create_access_token() │
   │                 │                       │ create_refresh_token()│
   │                 │◄──────────────────────│                       │
   │                 │ 200 TokenResponse     │                       │
   │                 │ (access+refresh)      │                       │
   │                 │                       │                       │
   │                 │ GET /users/me         │                       │
   │                 │ Authorization: Bearer │                       │
   │                 │──────────────────────►│                       │
   │                 │                       │ decode_token()        │
   │                 │                       │ SELECT user by id ───►│
   │                 │◄──────────────────────│                       │
   │ Dashboard carga │ 200 UserResponse      │                       │
   │◄────────────────│                       │                       │
```

### Flujo 3 — Recuperación de Contraseña

```
Usuario           Frontend                Backend               PostgreSQL    Email
   │                 │                       │                       │           │
   │ Ingresa email   │                       │                       │           │
   │────────────────►│ POST /auth/forgot-password                    │           │
   │                 │──────────────────────►│                       │           │
   │                 │                       │ Busca user por email─►│           │
   │                 │                       │ (si no existe, retorna │           │
   │                 │                       │  respuesta genérica)  │           │
   │                 │                       │ Crea PasswordResetToken           │
   │                 │                       │──────────────────────────────────►│
   │"Revisa tu email"│◄──────────────────────│                       │  Envía mail
   │◄────────────────│ 200 (siempre igual)   │                       │           │
   │                 │                       │                       │           │
   │ Clic en link    │                       │                       │           │
   │────────────────►│ POST /auth/reset-password { token, new_pass } │           │
   │                 │──────────────────────►│                       │           │
   │                 │                       │ Valida token ────────►│           │
   │                 │                       │ hash(new_password)    │           │
   │                 │                       │ UPDATE users password │           │
   │                 │                       │ UPDATE token used=true│           │
   │ "Contraseña restablecida"◄──────────────│                       │           │
   │◄────────────────│ 200 MessageResponse   │                       │           │
```

---

## Decisiones Técnicas Clave

### ¿Por qué FastAPI y no Django o Flask?

| Criterio             | FastAPI                | Flask        | Django               |
| -------------------- | ---------------------- | ------------ | -------------------- |
| Velocidad            | ⚡ Ultra rápido (ASGI) | Medio (WSGI) | Medio (WSGI)         |
| Tipado               | ✅ Nativo (Pydantic)   | ❌ Manual    | ⚠️ Parcial           |
| Validación           | ✅ Automática          | ❌ Manual    | ✅ Forms/Serializers |
| Documentación        | ✅ Swagger auto        | ❌ Manual    | ❌ Manual (o DRF)    |
| Curva de aprendizaje | Baja                   | Muy baja     | Alta                 |

FastAPI fue elegido por su soporte nativo de tipos Python, validación automática con Pydantic y documentación Swagger auto-generada.

### ¿Por qué JWT stateless y no sesiones en servidor?

| Criterio           | JWT Stateless         | Sesiones en servidor                |
| ------------------ | --------------------- | ----------------------------------- |
| Escalabilidad      | ✅ Horizontal fácil   | ❌ Requiere sticky sessions o Redis |
| Estado en servidor | ✅ Ninguno            | ❌ Almacenamiento de sesiones       |
| Revocación         | ❌ Requiere blacklist | ✅ Borrar sesión                    |
| Apropiado para SPA | ✅ Diseñado para esto | ⚠️ Problemas con CORS               |

Para este proyecto educativo, la arquitectura stateless con JWT es la más apropiada — permite escalar horizontalmente sin coordinación entre servidores.

### ¿Por qué React + Vite y no Next.js?

Este es un proyecto de **SPA (Single Page Application)** — toda la navegación ocurre en el cliente. Next.js agrega SSR (Server-Side Rendering) que no es necesario para una app de auth. Vite es más rápido en desarrollo y la configuración es más simple para aprendizaje.

### ¿Por qué TailwindCSS 4?

- Utility-first: clases aplicadas directamente en JSX, sin saltar entre archivos CSS
- Consistencia: la escala de espaciado, colores y tipografía es uniforme
- Dark mode: soporte nativo con variante `dark:`
- Purge automático: solo los estilos usados llegan al bundle de producción

---

## Configuración de Entornos

| Variable          | Desarrollo                   | Producción                                     |
| ----------------- | ---------------------------- | ---------------------------------------------- |
| `ENVIRONMENT`     | `development`                | `production`                                   |
| `/docs` (Swagger) | ✅ Disponible                | ❌ Deshabilitado (404)                         |
| `DATABASE_URL`    | `localhost:5432`             | Servidor de BD en cloud                        |
| `FRONTEND_URL`    | `http://localhost:5173`      | `https://tu-dominio.com`                       |
| `SECRET_KEY`      | Clave de desarrollo (≥32 ch) | Clave aleatoria larga (`openssl rand -hex 64`) |
| `RESEND_API_KEY`  | Vacío (logs en consola)      | API key de Resend.com                          |

> Ver [be/.env.example](../be/.env.example) para la lista completa de variables.
