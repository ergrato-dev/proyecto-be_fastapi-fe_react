# 🔁 Flujo de trabajo en GitHub — Issues, ramas, PRs y revisión

<!--
  ¿Qué? Guía del ciclo completo de colaboración en GitHub aplicado a este proyecto:
        issue → rama → commits → Pull Request → revisión → merge.
  ¿Para qué? Que el aprendiz practique el proceso real de un equipo de desarrollo, no solo
        el "git add / commit / push" en solitario sobre main.
  ¿Impacto? Sin este flujo, el aprendiz llega a su primer empleo sabiendo programar pero sin
        saber cómo se organiza, se revisa y se integra el trabajo de varias personas —
        que es donde se pierde (o se gana) la calidad de un producto.
-->

> **Proyecto educativo** — SENA CGMLTI | Tecnólogo en ADSO

Esta guía es de práctica obligatoria: la [Fase 6 de la bitácora](../../BITACORA.md) pide como
evidencia un issue, un PR y un merge hechos por ti.

---

## 📋 Tabla de Contenidos

- [1. Por qué issues y pull requests](#1-por-qué-issues-y-pull-requests)
- [2. Dónde practicas: tu propio repo](#2-dónde-practicas-tu-propio-repo)
- [3. El ciclo completo, paso a paso](#3-el-ciclo-completo-paso-a-paso)
- [4. Convención de ramas](#4-convención-de-ramas)
- [5. Commits](#5-commits)
- [6. Vincular el PR con su issue](#6-vincular-el-pr-con-su-issue)
- [7. Labels](#7-labels)
- [8. Modo individual](#8-modo-individual)
- [9. Modo equipo (GAES)](#9-modo-equipo-gaes)
- [10. Errores comunes](#10-errores-comunes)

---

## 1. Por qué issues y pull requests

En este proyecto ya existe la documentación de **qué** hay que construir:
[`docs/requisitos/HUs/`](../requisitos/HUs/) (historias de usuario) y
[`docs/requisitos/RFs/`](../requisitos/RFs/) (requisitos funcionales). Lo que falta es el
**cómo se organiza ese trabajo**, y ahí entran dos herramientas:

| Herramienta      | Qué es                                                   | Qué responde                       |
| ---------------- | -------------------------------------------------------- | ---------------------------------- |
| **Issue**        | La unidad de trabajo: una tarea, un bug, una mejora       | ¿Qué hay que hacer y por qué?      |
| **Pull Request** | La propuesta de cambio: un diff que pide entrar a `main`  | ¿Este código merece ser integrado? |

La cadena completa que se espera de ti:

```
HU/RF documentada  →  Issue  →  Rama  →  Commits  →  Pull Request  →  Revisión  →  Merge
   (el requisito)     (la tarea) (el trabajo)         (la propuesta)   (el filtro)  (la evidencia)
```

**¿Por qué importa?** Porque el instructor —y mañana tu líder técnico— no evalúa solo que la
pantalla se vea bien. Evalúa si se puede rastrear **por qué existe cada línea de código**. Un
`main` con 40 commits sueltos no cuenta esa historia. Un historial de PRs mergeados, cada uno
cerrando un issue que cita un RF, sí.

---

## 2. Dónde practicas: tu propio repo

Este repositorio (`ergrato-dev/proyecto-be_fastapi-fe_react`) **no acepta pull requests
externos**. Si abres uno, un bot lo cierra automáticamente en segundos — mira
[`.github/workflows/close-prs.yml`](../../.github/workflows/close-prs.yml).

No es un castigo: es un **repositorio de referencia**, el "libro de texto". Un libro de texto no
cambia porque un estudiante escriba en el margen. Tú practicas en **tu copia**, donde eres
dueño de todo: issues, ramas, PRs, revisiones y merges.

### Preparar tu copia

```bash
# 1. Haz fork desde la web de GitHub (botón "Fork", arriba a la derecha).

# 2. Clona TU fork (ojo: tu usuario, no ergrato-dev).
git clone git@github.com:TU-USUARIO/proyecto-be_fastapi-fe_react.git
cd proyecto-be_fastapi-fe_react

# 3. Guarda el repo original como "upstream" para poder traer sus actualizaciones.
git remote add upstream git@github.com:ergrato-dev/proyecto-be_fastapi-fe_react.git

# 4. Verifica que tienes dos remotos: origin (tuyo) y upstream (el original).
git remote -v
```

Cuando el repo original reciba cambios y quieras traerlos a tu fork:

```bash
git fetch upstream
git switch main
git merge upstream/main
git push origin main
```

### ⚠️ Activa las Actions de tu fork

GitHub **deshabilita las Actions en los forks** por defecto. Sin activarlas, tu CI
([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)) nunca corre y tus PRs no tendrán
checks.

Ve a la pestaña **Actions** de tu fork → botón _"I understand my workflows, go ahead and enable
them"_. Solo se hace una vez.

---

## 3. El ciclo completo, paso a paso

Todo se puede hacer desde la web de GitHub o desde la terminal con
[`gh`](https://cli.github.com/) (GitHub CLI). Aprende ambos: la web para entender, la CLI para
ir rápido.

| Paso                | Terminal (`gh` / `git`)                       | Web                                    |
| ------------------- | --------------------------------------------- | -------------------------------------- |
| 1. Crear el issue   | `gh issue create`                             | Pestaña Issues → _New issue_           |
| 2. Asignártelo      | `gh issue edit 12 --add-assignee @me`         | Campo _Assignees_ en el issue          |
| 3. Crear la rama    | `git switch -c feat/12-add-locale-field`      | Enlace _Create a branch_ en el issue   |
| 4. Trabajar         | `git add -p && git commit`                    | —                                      |
| 5. Publicar la rama | `git push -u origin feat/12-add-locale-field` | —                                      |
| 6. Abrir el PR      | `gh pr create`                                | Banner _Compare & pull request_        |
| 7. Ver la CI        | `gh pr checks`                                | Pestaña _Checks_ del PR                |
| 8. Revisar          | `gh pr diff`                                  | Pestaña _Files changed_ → _Review_     |
| 9. Mergear          | `gh pr merge --squash --delete-branch`        | Botón _Squash and merge_               |
| 10. Volver a `main` | `git switch main && git pull`                 | —                                      |

### El ciclo, completo, en una sesión de terminal

```bash
# 1-2. Crear el issue y asignártelo.
gh issue create --title "[Tarea] Persistir el idioma preferido del usuario"
gh issue edit 12 --add-assignee @me

# 3. Rama nueva, siempre desde un main actualizado.
git switch main
git pull
git switch -c feat/12-add-locale-field

# 4. Trabajar y commitear en pasos pequeños.
git add be/app/models/user.py
git commit   # el mensaje sigue Conventional Commits — ver sección 5

# 5. Publicar la rama.
git push -u origin feat/12-add-locale-field

# 6. Abrir el PR (se carga la plantilla PULL_REQUEST_TEMPLATE.md).
gh pr create

# 7. Esperar la CI. Si sale roja, corriges y vuelves a hacer push:
#    el PR se actualiza solo, no hay que abrir otro.
gh pr checks --watch

# 9-10. Con la CI en verde y la revisión hecha:
gh pr merge --squash --delete-branch
git switch main
git pull
```

> 💡 **`--squash`**: junta todos los commits del PR en uno solo al entrar a `main`. Deja el
> historial de `main` limpio (un commit = un cambio completo) mientras tú commiteas todas las
> veces que quieras dentro de tu rama.

---

## 4. Convención de ramas

```
<tipo>/<número-de-issue>-<descripción-corta-en-inglés>
```

```bash
feat/12-add-locale-field        # ✅ tipo, issue y qué hace
fix/27-expired-refresh-token    # ✅
docs/31-collaboration-guide     # ✅

nueva-rama                      # ❌ no dice nada
arreglos                        # ❌ ni el tipo ni el issue
feat/agregar-campo-idioma       # ❌ los nombres de rama van en inglés
```

Los **tipos** son los mismos de los commits:
`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`
(ver [`.github/prompts/commit-message.prompt.md`](../../.github/prompts/commit-message.prompt.md)).

El nombre va en **inglés** porque en este proyecto todo lo técnico —código, endpoints, tablas,
commits y ramas— es en inglés, y solo comentarios y documentación en español
(regla §3.1 de [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md)).

Incluir el número de issue en la rama no es decorativo: cuando vuelvas a esa rama tres días
después, o cuando un compañero vea `feat/12-...` en la lista, saben exactamente qué se está
haciendo y dónde está escrito el porqué.

---

## 5. Commits

Este proyecto ya tiene su convención documentada y no se repite aquí:
👉 [`.github/prompts/commit-message.prompt.md`](../../.github/prompts/commit-message.prompt.md)

En resumen, el asunto va **en inglés**, máximo 72 caracteres, y el cuerpo explica motivo e
impacto:

```
feat(user): persist preferred locale on the user profile

For: The language selector reset to Spanish on every login
Impact: Adds a `locale` column to users; requires running `alembic upgrade head`
```

Reglas prácticas:

- **Un commit = un cambio con sentido propio.** Si el mensaje necesita un "y", probablemente
  son dos commits.
- **Nunca commitees directo en `main`.** Siempre en una rama.
- Si te equivocaste en el último mensaje y **aún no hiciste push**: `git commit --amend`.

---

## 6. Vincular el PR con su issue

En la descripción del PR (la plantilla ya trae la línea preparada):

```
Closes #12
```

Al mergear el PR, GitHub **cierra el issue #12 automáticamente** y deja el enlace entre ambos
para siempre. Palabras que funcionan igual: `Closes`, `Fixes`, `Resolves`.

¿Por qué importa? Porque un mes después alguien mira una línea rara de código, hace
`git blame`, llega al commit, del commit al PR, del PR al issue, y del issue al RF que lo
motivó. Esa cadena es lo que hace mantenible un proyecto. Cerrar el issue a mano rompe el
eslabón.

---

## 7. Labels

Las labels clasifican los issues para poder filtrarlos. Set mínimo para este proyecto:

| Label              | Cuándo se usa                                         |
| ------------------ | ----------------------------------------------------- |
| `type:feat`        | Funcionalidad nueva                                   |
| `type:bug`         | Algo roto                                             |
| `type:docs`        | Documentación, refactor o mejora sin nueva función    |
| `area:be`          | Toca el backend (`be/`)                               |
| `area:fe`          | Toca el frontend (`fe/`)                              |
| `area:db`          | Toca modelos o migraciones Alembic                    |
| `prio:alta`        | Bloquea a otros o rompe el flujo principal            |
| `prio:media`       | Importante, no urgente                                |
| `prio:baja`        | Deseable                                              |
| `good-first-issue` | Buena entrada para quien recién llega al repo         |
| `bloqueado`        | No se puede avanzar hasta que se resuelva otra cosa   |

Crearlas todas de una vez en tu repo:

```bash
gh label create "type:feat"        --color 0E8A16 --description "Funcionalidad nueva"
gh label create "type:bug"         --color D73A4A --description "Algo no funciona"
gh label create "type:docs"        --color 0075CA --description "Documentación o mejora"
gh label create "area:be"          --color 5319E7 --description "Backend (be/)"
gh label create "area:fe"          --color 1D76DB --description "Frontend (fe/)"
gh label create "area:db"          --color 8B4513 --description "Modelos y migraciones"
gh label create "prio:alta"        --color B60205 --description "Prioridad alta"
gh label create "prio:media"       --color FBCA04 --description "Prioridad media"
gh label create "prio:baja"        --color C2E0C6 --description "Prioridad baja"
gh label create "good-first-issue" --color 7057FF --description "Buen primer issue"
gh label create "bloqueado"        --color 000000 --description "Bloqueado por otra tarea"
```

Filtrar después: `gh issue list --label "area:be" --label "prio:alta"`.

---

## 8. Modo individual

Trabajas solo en tu repo. La tentación es obvia: _"si nadie va a revisar, commiteo en `main` y
ya"_. No lo hagas — pierdes justo lo que se está evaluando.

Tu flujo es el mismo de la sección 3, con una diferencia: **tú eres el revisor**.

Y auto-revisar de verdad significa:

1. Abrir la pestaña **Files changed** del PR y leer **todo el diff**, línea por línea. Leer tu
   código en la vista de revisión, fuera del editor, hace visible lo que en el editor no ves:
   el `console.log` olvidado, el archivo que no querías subir, el comentario sin actualizar.
2. Recorrer el checklist de la plantilla de PR, marcando solo lo que de verdad cumpliste.
3. Dejar al menos **un comentario en una línea concreta** explicando una decisión que tomaste.
   Escribirle a un lector obliga a justificar lo que en tu cabeza parecía obvio.
4. Esperar a que la **CI esté en verde**. Roja = no se mergea. Sin excepciones.
5. Recién ahí, _Squash and merge_.

> Un PR que abres y mergeas en el mismo minuto sin abrir el diff no es un PR: es un `git push`
> con pasos extra.

---

## 9. Modo equipo (GAES)

Varios aprendices sobre un mismo repo. Cambia poco en lo técnico y mucho en lo humano.

### Configuración inicial (una vez, quien administra el repo)

1. **Colaboradores**: _Settings → Collaborators_ → agregar a cada integrante.
2. **Proteger `main`**: _Settings → Branches → Add branch ruleset_ sobre `main`:
   - ✅ Require a pull request before merging → **1 aprobación**
   - ✅ Require status checks to pass → seleccionar los checks `Backend` y `Frontend` de la CI
   - ✅ Require branches to be up to date before merging

   Con esto **nadie** —ni quien creó el repo— puede empujar directo a `main`. La regla deja de
   depender de la buena memoria del equipo.

3. **Repartir el trabajo**: cada issue con **un solo** `assignee`. Dos personas en el mismo
   issue = dos ramas tocando los mismos archivos = conflicto garantizado.

### Revisar el PR de un compañero

Revisar no es buscar culpables ni aprobar por cortesía. Es preguntar y proponer.

En _Files changed_, haz clic en el número de línea para comentar ahí mismo. Al terminar,
_Review changes_ y elige:

| Opción              | Cuándo                                                       |
| ------------------- | ------------------------------------------------------------ |
| **Comment**         | Dudas o sugerencias que no bloquean                          |
| **Approve**         | Lo entendiste, cumple los criterios del issue y la CI pasa    |
| **Request changes** | Hay algo que debe corregirse antes de entrar a `main`         |

Qué mirar, en este orden:

1. ¿Hace lo que dice el issue? ¿Cumple sus criterios de aceptación?
2. ¿Hay tests que lo respalden?
3. ¿Se entiende sin que el autor lo explique? (comentarios ¿Qué? ¿Para qué? ¿Impacto?)
4. ¿Rompe algo que ya funcionaba?
5. Estilo y nombres — **al final**, y solo si lo anterior está bien.

Comenta el código, no a la persona: _"esta función no valida el email vacío, ¿qué pasa si
llega `""`?"_ en vez de _"te faltó validar"_.

### Mantener tu rama al día

Mientras trabajas, `main` avanza con los PRs de tus compañeros. Antes de pedir revisión:

```bash
git fetch origin
git rebase origin/main
```

Si hay conflicto, git te dice qué archivos. Los abres, dejas la versión correcta (borrando las
marcas `<<<<<<<`, `=======`, `>>>>>>>`), y sigues:

```bash
git add <archivo-resuelto>
git rebase --continue
git push --force-with-lease   # el rebase reescribió tu historial: hay que reescribir el remoto
```

> ⚠️ `--force-with-lease` (no `--force`) aborta el push si alguien más subió commits a tu rama
> mientras tanto. Solo úsalo en **tu** rama de trabajo, **nunca** en `main`.
>
> Si el rebase se complica, `git rebase --abort` te devuelve al punto de partida sin daños.

---

## 10. Errores comunes

| Error                                            | Por qué duele                                                                 | Qué hacer                                                     |
| ------------------------------------------------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Commitear directo en `main`                      | Sin PR no hay revisión, ni CI, ni historial de por qué                        | Rama siempre; protege `main` en modo equipo                    |
| Un PR con 40 archivos y tres funciones distintas | Nadie lo revisa de verdad; se aprueba a ciegas                                | Un issue = un PR. Si crece, divídelo                           |
| PR sin issue                                     | No hay requisito que lo justifique ni trazabilidad                            | Abre el issue primero, aunque tarde un minuto                  |
| Rama vieja, sin actualizar                       | Conflictos gigantes al final, cuando ya no recuerdas el contexto              | `git fetch origin && git rebase origin/main` seguido           |
| Mergear con la CI en rojo                        | `main` queda roto para todo el equipo                                         | Rojo = se corrige y se hace push otra vez                      |
| `npm install`                                    | Genera `package-lock.json`, rompe el lock de `pnpm` y ensucia el PR           | **Siempre `pnpm`** (§4.2 de `copilot-instructions.md`)         |
| Commitear el `.env`                              | Filtra credenciales — y el historial de git no olvida                         | Solo `.env.example`; verifica el diff antes de commitear       |
| Borrar la rama antes de mergear                  | Pierdes el trabajo que no estaba en `main`                                    | `--delete-branch` **después** del merge, no antes              |
| Cerrar el issue a mano                           | Se pierde el vínculo issue ↔ PR                                               | `Closes #N` en el PR y deja que GitHub lo cierre               |

---

## 📚 Ver también

| Documento                                                                             | Para qué                                          |
| ------------------------------------------------------------------------------------- | ------------------------------------------------- |
| [`BITACORA.md`](../../BITACORA.md)                                                    | Fase 6 — la evidencia que se te pide de este flujo |
| [`.github/prompts/commit-message.prompt.md`](../../.github/prompts/commit-message.prompt.md) | Convención completa de mensajes de commit   |
| [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md)             | Reglas de idioma, dependencias y calidad          |
| [`docs/requisitos/`](../requisitos/)                                                  | Las HUs y RFs que tus issues deben referenciar     |
| [`docs/setup/`](../setup/)                                                            | Levantar el proyecto antes de tocar código         |
