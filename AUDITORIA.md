# 🔍 Auditoría del repo (piloto para replicar en el resto de `proyecto-*`)

<!--
  ¿Qué? Auditoría en 5 ejes de este repo como proyecto de referencia.
  ¿Para qué? Servir de checklist reutilizable antes de replicar este mismo patrón
  (bitácora + auditoría + nombre representativo del stack) en los demás repos proyecto-*.
  ¿Impacto? Sin esto, los gaps de este repo (el más completo de los 9) se replicarían
  silenciosamente en el resto en vez de corregirse primero.
-->

Fecha de la auditoría: 2026-07-11. Repo evaluado en el momento del rename a
`proyecto-be_fastapi-fe_react`.

## Pertinencia

Alineado al RAP *"Planear actividades de construcción del software de acuerdo con el diseño
establecido"*: tiene Historias de Usuario y Requisitos Funcionales/No Funcionales en
[`docs/requisitos/`](docs/requisitos/) y arquitectura documentada en
[`docs/referencia-tecnica/`](docs/referencia-tecnica/). ✅ Sin acción requerida.

## Relevancia

Stack vigente y coherente con el stack de referencia real (FastAPI, React 19/Vite/TS,
PostgreSQL). ✅ Sin acción requerida.

## Completitud

Gaps identificados — **quedan documentados, no se corrigen en esta ronda**:

- ~~`.github/workflows/` solo tiene `close-prs.yml` (bot que cierra PRs externos). No hay CI que
  corra tests/lint/build en cada push o PR.~~ **Resuelto**: se agregó
  `.github/workflows/ci.yml` (ruff + pytest con PostgreSQL de servicio, ESLint + Prettier +
  build + vitest), junto con plantillas de Issue/PR y la guía
  `docs/colaboracion/flujo-github.md`.
- Backend tiene un solo archivo de test (`be/app/tests/test_auth.py`) pese a una superficie de
  auth completa (JWT, reset de password, verificación de email, rate limiting). El frontend, en
  cambio, tiene 13 archivos de test — asimetría marcada entre BE y FE.
- No existe `.pre-commit-config.yaml` pese a que `ruff` (backend) y ESLint+Prettier (frontend)
  ya están configurados — se podría automatizar el lint en pre-commit en vez de dejarlo manual.

## Actualidad

Último commit `80e0c9b` el 2026-07-01 (~10 días antes de esta auditoría), 50 commits totales —
el repo más activo de los 9 `proyecto-*`. ✅ Sin acción requerida.

## Seguridad

En general sólido:

- Password hashing con bcrypt (`passlib`).
- JWT con rotación de refresh token (access 15 min / refresh 7 días).
- `SECRET_KEY` con validador de longitud mínima (≥32 caracteres) en `be/app/config.py`.
- CORS acotado a un solo origin, métodos y headers explícitos (`be/app/main.py`).
- Rate limiting en endpoints de auth vía `slowapi`.
- Audit log de intentos de login, cambio de password y verificación de email
  (`be/app/utils/audit_log.py`).
- Mensajes de error genéricos para evitar enumeración de usuarios.

Hallazgo a documentar (no urgente, es dev-only y el propio README lo advierte en
"⚠️ Exención de Responsabilidades", pero debe quedar anotado explícitamente):

- `docker-compose.yml` en la raíz trae hardcodeado `SECRET_KEY:
  dev-secret-key-change-in-production-min-32-chars` y credenciales de DB en texto plano.
  Correcto para un compose de desarrollo, pero se recomienda un comentario explícito en el
  propio archivo aclarando que es intencional y que **nunca** debe copiarse tal cual a un
  compose de producción.

## Próximos pasos sugeridos (fuera de alcance de esta ronda)

1. ~~Agregar workflow de CI (`.github/workflows/ci.yml`) que corra `ruff`, `pytest`, ESLint y
   `vitest` en cada PR.~~ ✅ **Hecho** — incluye además `ISSUE_TEMPLATE/`,
   `PULL_REQUEST_TEMPLATE.md` y la guía de colaboración para los aprendices.
2. Ampliar cobertura de tests backend más allá de auth (services, utils, otros routers si los
   hay).
3. Agregar `.pre-commit-config.yaml` reutilizando la config de lint ya existente.
4. Comentario explícito de "dev-only, no copiar a prod" en `docker-compose.yml`.
5. Una vez resueltos 1-4 en este repo, replicar el mismo patrón (auditoría + bitácora + rename)
   en el resto de `proyecto-*`, empezando por `proyecto-beex-fe` (ver tabla de nombres en el
   plan de esta ronda).
