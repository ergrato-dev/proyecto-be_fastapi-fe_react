# 🔐 NN Auth System

<!--
  ¿Qué? Documentación principal del proyecto NN Auth System.
  ¿Para qué? Guiar a cualquier desarrollador o aprendiz para entender, configurar y ejecutar el proyecto.
  ¿Impacto? Sin este README, los nuevos colaboradores no sabrían cómo levantar el proyecto
  ni entenderían su propósito, arquitectura o convenciones.
-->

> **Proyecto educativo** — SENA | Febrero 2026

Sistema de autenticación completo para una empresa genérica **"NN"**, diseñado como ejercicio formativo.
Incluye landing page pública, registro de usuarios, login, cambio de contraseña y recuperación por email.

---

## 📝 Antes de empezar

Este repo **no es solo para clonar y cambiar el look**. Antes de presentarlo como evidencia de
aprendizaje, completa la [**Bitácora obligatoria**](BITACORA.md) — es un checklist secuencial
que verifica, con commits de tu propio repo, que entendiste el flujo real (arquitectura, auth,
base de datos) y no solo la apariencia.

Este repo **no acepta pull requests externos** (un bot los cierra automáticamente): el ciclo de
colaboración —issues, ramas, PRs, revisión y merge— se practica en **tu propio fork**, siguiendo
[`docs/colaboracion/flujo-github.md`](docs/colaboracion/flujo-github.md).

---

## 📋 Tabla de Contenidos

- [🔐 NN Auth System](#-nn-auth-system)
  - [📋 Tabla de Contenidos](#-tabla-de-contenidos)
  - [🛠️ Stack Tecnológico](#️-stack-tecnológico)
  - [✅ Prerrequisitos](#-prerrequisitos)
    - [Instalar pnpm (si no lo tienes)](#instalar-pnpm-si-no-lo-tienes)
  - [🚀 Instalación y Setup](#-instalación-y-setup)
    - [1. Clonar el repositorio](#1-clonar-el-repositorio)
    - [2. Levantar la base de datos](#2-levantar-la-base-de-datos)
    - [3. Configurar el Backend](#3-configurar-el-backend)
    - [4. Configurar el Frontend](#4-configurar-el-frontend)
  - [▶️ Ejecución](#️-ejecución)
    - [Levantar todo el sistema (3 terminales)](#levantar-todo-el-sistema-3-terminales)
  - [🧪 Testing](#-testing)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Linting](#linting)
  - [📁 Estructura del Proyecto](#-estructura-del-proyecto)
  - [📏 Convenciones](#-convenciones)
  - [📚 Documentación Adicional](#-documentación-adicional)
  - [🎓 Propósito Educativo](#-propósito-educativo)
  - [⚠️ Exención de Responsabilidades](#️-exención-de-responsabilidades)
  - [📄 Licencia](#-licencia)

---

## 🛠️ Stack Tecnológico

| Capa              | Tecnologías                                         |
| ----------------- | --------------------------------------------------- |
| **Backend**       | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, JWT |
| **Frontend**      | React 18+, Vite, TypeScript, TailwindCSS 4+         |
| **Base de datos** | PostgreSQL 17+ (Docker Compose)                     |
| **Email (dev)**   | Mailpit — captura SMTP local, UI en puerto 8025     |
| **Testing**       | pytest + httpx (BE), Vitest + Testing Library (FE)  |
| **Linting**       | ruff (Python), ESLint + Prettier (TypeScript)       |

---

## ✅ Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

| Herramienta        | Versión mínima | Verificar con            |
| ------------------ | -------------- | ------------------------ |
| **Python**         | 3.12+          | `python3 --version`      |
| **Node.js**        | 20 LTS+        | `node --version`         |
| **pnpm**           | 9+             | `pnpm --version`         |
| **Docker**         | 24+            | `docker --version`       |
| **Docker Compose** | 2.20+          | `docker compose version` |
| **Git**            | 2.40+          | `git --version`          |

> ⚠️ **Importante**: Usar **pnpm** como gestor de paquetes de Node.js. **Nunca usar npm ni yarn.**

> 🖥️ **Usuarios de Windows — leer antes de continuar**
> Todos los comandos de este proyecto usan sintaxis Bash (`source`, `export`, `/`, etc.).
> Usa siempre **Git Bash** como terminal — viene incluido al instalar
> [Git para Windows](https://git-scm.com/download/win).
> **No uses CMD ni PowerShell** — los comandos no funcionarán igual.

### Instalar pnpm (si no lo tienes)

```bash
# Opción recomendada — vía corepack (incluido con Node.js 16+)
corepack enable
corepack prepare pnpm@latest --activate

# Alternativa — instalación independiente
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

---

## 🚀 Instalación y Setup

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd proyecto
```

### 2. Levantar la base de datos

```bash
# Inicia PostgreSQL 17 + Mailpit (captura de emails) en contenedores Docker
docker compose up -d

# Verificar que están corriendo
docker compose ps
# Deberías ver nn_auth_db y nn_auth_mailpit con estado "healthy"
```

### 3. Configurar el Backend

```bash
cd be

# Crear entorno virtual de Python
python3 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate          # Linux/macOS y Windows (Git Bash) ← usar siempre
# source .venv/Scripts/activate    # Windows (Git Bash — ruta alternativa si la anterior falla)

# Instalar dependencias
uv sync

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores si es necesario

# Ejecutar migraciones de base de datos
alembic upgrade head
```

### 4. Configurar el Frontend

```bash
cd fe

# Instalar dependencias con pnpm (¡NUNCA con npm!)
pnpm install

# Copiar y configurar variables de entorno
cp .env.example .env
```

---

## ▶️ Ejecución

### Levantar todo el sistema (3 terminales)

```bash
# Terminal 1 — Base de datos (si no está corriendo)
docker compose up -d

# Terminal 2 — Backend (FastAPI)
cd be && source .venv/bin/activate
uvicorn app.main:app --reload
# → API disponible en http://localhost:8000
# → Swagger UI en http://localhost:8000/docs  (solo si ENVIRONMENT=development, que es el default)

# Terminal 3 — Frontend (React + Vite)
cd fe && pnpm dev
# → Landing page en http://localhost:5173
# → App disponible en http://localhost:5173
```

> 📧 **Mailpit** — bandeja de entrada de emails de desarrollo: `http://localhost:8025`
> Aquí se capturan los emails de verificación de cuenta y recuperación de contraseña.

---

## 🧪 Testing

### Backend

```bash
cd be && source .venv/bin/activate

# Ejecutar todos los tests
pytest -v

# Ejecutar con cobertura
pytest --cov=app --cov-report=term-missing

# Ejecutar un test específico
pytest app/tests/test_auth.py -v
```

### Frontend

```bash
cd fe

# Ejecutar todos los tests
pnpm test

# Ejecutar en modo watch
pnpm test:watch

# Ejecutar con cobertura
pnpm test:coverage
```

### Linting

```bash
# Backend
cd be && ruff check app/ && ruff format app/

# Frontend
cd fe && pnpm lint && pnpm format
```

---

## 📁 Estructura del Proyecto

```
proyecto/
├── .github/copilot-instructions.md   # Reglas y convenciones del proyecto
├── .gitignore                        # Archivos ignorados por git
├── docker-compose.yml                # PostgreSQL 17 para desarrollo
├── README.md                         # ← Este archivo
├── docs/                             # Documentación técnica
├── assets/                           # Recursos estáticos
├── be/                               # Backend — FastAPI + Python
│   ├── app/                          # Código fuente
│   │   ├── main.py                   # Punto de entrada FastAPI
│   │   ├── config.py                 # Configuración (Pydantic Settings)
│   │   ├── database.py               # Conexión a PostgreSQL
│   │   ├── models/                   # Modelos ORM (User, PasswordResetToken, EmailVerificationToken)
│   │   ├── schemas/                  # Schemas Pydantic (request/response)
│   │   ├── routers/                  # Endpoints (auth, users)
│   │   ├── services/                 # Lógica de negocio
│   │   ├── utils/                    # Utilidades (security, email)
│   │   └── tests/                    # Tests con pytest
│   ├── alembic/                      # Migraciones de BD
│   └── pyproject.toml / uv.lock       # Dependencias Python (uv)
└── fe/                               # Frontend — React + Vite + TypeScript
    ├── src/
    │   ├── api/                      # Clientes HTTP
    │   ├── components/               # Componentes reutilizables
    │   ├── pages/                    # Páginas/vistas (Landing, Login, Register, Dashboard…)
    │   ├── hooks/                    # Custom hooks
    │   ├── context/                  # Context providers
    │   └── types/                    # Tipos TypeScript
    ├── package.json                  # Dependencias (pnpm)
    └── vite.config.ts                # Configuración de Vite
```

---

## 📏 Convenciones

| Aspecto              | Regla                                            |
| -------------------- | ------------------------------------------------ |
| Nomenclatura técnica | Inglés (variables, funciones, clases, endpoints) |
| Comentarios/docs     | Español (con ¿Qué? ¿Para qué? ¿Impacto?)         |
| Commits              | Conventional Commits en inglés + What/For/Impact |
| Python               | PEP 8 + type hints obligatorios + ruff           |
| TypeScript           | strict mode + ESLint + Prettier                  |
| Gestor de paquetes   | `venv` (Python), `pnpm` (Node.js)                |
| Testing              | Código generado = código probado                 |
| Ramas y PRs          | `<tipo>/<issue>-<slug>` + PR con `Closes #N`     |

Para las reglas completas, ver [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

---

## 📚 Documentación Adicional

| Documento                                                                                    | Descripción                                              |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| [`BITACORA.md`](BITACORA.md)                                                                 | Checklist obligatorio de aprendizaje, fase por fase       |
| [`AUDITORIA.md`](AUDITORIA.md)                                                               | Auditoría de pertinencia/relevancia/completitud/actualidad/seguridad |
| [`docs/colaboracion/flujo-github.md`](docs/colaboracion/flujo-github.md)                     | Flujo de Issues, ramas, Pull Requests, revisión y merge  |
| [`docs/referencia-tecnica/architecture.md`](docs/referencia-tecnica/architecture.md)         | Arquitectura general, flujos y decisiones técnicas       |
| [`docs/referencia-tecnica/api-endpoints.md`](docs/referencia-tecnica/api-endpoints.md)       | Todos los endpoints con parámetros, respuestas y errores |
| [`docs/referencia-tecnica/database-schema.md`](docs/referencia-tecnica/database-schema.md)   | Esquema ER, tablas, columnas y migraciones               |
| [`docs/conceptos/owasp-top-10.md`](docs/conceptos/owasp-top-10.md)                           | Implementación del OWASP Top 10 2021                     |
| [`docs/conceptos/accesibilidad-aria-wcag.md`](docs/conceptos/accesibilidad-aria-wcag.md)     | Estándares ARIA/WCAG 2.1 AA aplicados                    |
| [`.github/copilot-instructions.md`](.github/copilot-instructions.md)                         | Reglas y convenciones del proyecto                       |

---

## 🎓 Propósito Educativo

Este proyecto está diseñado para **aprender haciendo**. Cada archivo, función y componente incluye comentarios pedagógicos que explican:

- **¿Qué?** — Qué hace este código
- **¿Para qué?** — Por qué existe y cuál es su propósito
- **¿Impacto?** — Qué pasa si no existiera o si se implementa mal

> _"La calidad no es una opción, es una obligación."_

---

## ⚠️ Exención de Responsabilidades

Este proyecto es de naturaleza **exclusivamente educativa**, desarrollado como ejercicio formativo en el marco del SENA.

- **No apto para producción** — El sistema no ha sido auditado ni endurecido para entornos productivos reales. No debe usarse para proteger datos sensibles de usuarios reales sin una revisión de seguridad profesional previa.
- **Credenciales de ejemplo** — Las contraseñas, claves secretas y cadenas de conexión presentes en `.env.example` y en la documentación son únicamente ilustrativas. **Nunca usarlas en producción.**
- **Sin garantía de disponibilidad** — El proyecto puede contener bugs o comportamientos no documentados propios de un entorno de aprendizaje.
- **Uso de terceros** — El proyecto referencia servicios externos (Resend, Neon, Supabase, Railway) como ejemplos pedagógicos. El autor no tiene afiliación con dichos servicios ni garantiza su disponibilidad o condiciones de uso.
- **Responsabilidad del aprendiz** — Cada aprendiz es responsable de comprender el código que ejecuta en su equipo y de no reutilizarlo sin entenderlo completamente.

> Este material se provee **"tal cual"**, sin garantías explícitas ni implícitas de ningún tipo.

---

## 📄 Licencia

[![CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Este proyecto está licenciado bajo **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.

**Puedes:**

- ✅ Compartir — copiar y redistribuir el material en cualquier medio o formato
- ✅ Adaptar — remezclar, transformar y crear a partir del material (forks educativos permitidos)

**Bajo las siguientes condiciones:**

- 📝 **Atribución** — Debes dar crédito apropiado, enlazar la licencia e indicar si se realizaron cambios.
- 🚫 **No Comercial** — No puedes usar el material con fines comerciales.
- 🔄 **Compartir Igual** — Si remezclas o transformas el material, debes distribuir tus contribuciones bajo la misma licencia.

Consulta el archivo [LICENSE](./LICENSE) o visita [creativecommons.org/licenses/by-nc-sa/4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) para más información.
