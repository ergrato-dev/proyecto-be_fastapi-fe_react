# 🧭 Bitácora obligatoria del aprendiz

<!--
  ¿Qué? Checklist secuencial obligatorio antes de presentar este proyecto como propio.
  ¿Para qué? Forzar comprensión real del flujo (auth, DB, arquitectura) en vez de solo
  cambiar estilos/colores sobre un clon sin entender.
  ¿Impacto? Sin esto, el instructor no tiene forma de verificar que el aprendiz entendió
  el código que está presentando como evidencia de aprendizaje.
-->

> **Regla de oro**: esta bitácora se completa **en orden**, fase por fase. No se avanza a la
> siguiente fase sin cerrar la anterior. El instructor verifica en **tu propio repo**
> (`git log`, diffs de los commits referenciados) — no basta con escribir texto aquí si el
> commit no existe o no contiene lo que declaras.

Copia este archivo a tu propio repo (fork o clon) y complétalo ahí. Cada fase pide un
**commit hash** de tu repo como evidencia — el instructor revisa ese commit puntual.

---

## Fase 0 — Entorno verificado

Levanta el proyecto siguiendo [`docs/setup/con-docker.md`](docs/setup/con-docker.md) o
[`docs/setup/sin-docker.md`](docs/setup/sin-docker.md).

- [ ] Login y registro funcionan en tu máquina.
- [ ] Commit: `docs: bitácora fase 0` → hash: `___________`
- [ ] Captura del dashboard corriendo adjunta en tu repo (`docs/evidencia/` o similar).

## Fase 1 — Arquitectura propia

Lee [`docs/referencia-tecnica/architecture.md`](docs/referencia-tecnica/architecture.md),
[`api-endpoints.md`](docs/referencia-tecnica/api-endpoints.md) y
[`database-schema.md`](docs/referencia-tecnica/database-schema.md).

- [ ] Elige **un** endpoint y escribe abajo, con tus propias palabras (10-15 líneas), el flujo
      completo request → response (routers → services → DB → respuesta).

```
(tu respuesta aquí)
```

- [ ] Commit: `docs: bitácora fase 1` → hash: `___________`

## Fase 2 — Trazar login línea a línea

Sigue el login desde `fe/src/pages/LoginPage.tsx` → `fe/src/api/auth.ts` →
`be/app/routers/auth.py` → `be/app/services/auth_service.py` → `be/app/utils/security.py` → DB.

- [ ] ¿Dónde se genera el JWT? ¿Dónde se valida en requests posteriores?

```
(tu respuesta aquí)
```

- [ ] ¿Dónde se hashea el password y con qué algoritmo? ¿Por qué ese algoritmo y no otro?

```
(tu respuesta aquí)
```

- [ ] Commit: `docs: bitácora fase 2` → hash: `___________`

## Fase 3 — Modificar una regla de negocio real (no CSS)

Elige **una** tarea que toque backend + DB + frontend a la vez, referenciando el RF que aplica
en [`docs/requisitos/RFs/`](docs/requisitos/RFs/). Ejemplos:

- Agregar un campo nuevo a `User` (modelo + migración Alembic + exponerlo en el frontend).
- Cambiar y justificar la expiración del access/refresh token.
- Agregar una regla de validación de negocio nueva en el registro.

- [ ] RF referenciado: `___________`
- [ ] Commit con el cambio de lógica real (no solo estilos) → hash: `___________`
- [ ] Explica qué cambiaste y por qué:

```
(tu respuesta aquí)
```

## Fase 4 — Dashboard con dato real

Reemplaza uno de los datasets mock de `DataTable` (`fe/src/pages/DashboardPage.tsx`) por datos
reales obtenidos de un endpoint propio (no mock, no hardcode).

- [ ] Endpoint nuevo/reutilizado: `___________`
- [ ] Commit → hash: `___________`
- [ ] Captura del dashboard mostrando el dato real adjunta en tu repo.

## Fase 5 — Autoevaluación de seguridad

Basado en [`docs/conceptos/owasp-top-10.md`](docs/conceptos/owasp-top-10.md), evalúa **tu propio
cambio** de la Fase 3 y/o Fase 4:

- [ ] ¿Tu endpoint/cambio nuevo requiere autenticación? ¿Debería?
- [ ] ¿Valida el input recibido? ¿Qué pasa si mandas un valor inválido o vacío?
- [ ] ¿Qué pasa si un usuario sin permisos intenta usar tu cambio?

```
(tu respuesta aquí)
```

- [ ] Commit: `docs: bitácora fase 5` → hash: `___________`

## Fase 6 — Colaborar como en un equipo real

Lee [`docs/colaboracion/flujo-github.md`](docs/colaboracion/flujo-github.md) y aplica el ciclo
completo **en tu propio repo**: issue → rama → commits → Pull Request → revisión → merge.
El repo original no acepta PRs externos; esta fase se hace y se evidencia en tu fork.

- [ ] Issue abierto con la plantilla "Tarea (HU/RF)", referenciando un RF o HU real
      → número: `#______`
- [ ] Rama creada con la convención `<tipo>/<issue>-<slug-en-ingles>`
      → nombre: `___________________________`
- [ ] PR abierto con `Closes #N` y el checklist de la plantilla completo → número: `#______`
- [ ] CI en verde en ese PR (enlace al run o captura en tu repo)
      → enlace: `___________________________`
- [ ] Revisión hecha: en equipo, un compañero aprobó; individual, comentaste tu propio diff
      línea a línea antes de mergear.
- [ ] Merge realizado y el issue se cerró **solo** → merge commit hash: `___________`
- [ ] Explica qué revisaste en el diff y qué habrías pedido cambiar si el PR fuera de otra
      persona:

```
(tu respuesta aquí)
```

---

Al completar las 7 fases, tu bitácora queda como parte del historial de tu repo — es la
evidencia que el instructor revisa para verificar comprensión, no solo funcionalidad visual.
