<!--
  ¿Qué? Plantilla que se carga automáticamente en la descripción de cada Pull Request.
  ¿Para qué? Que quien revisa (un compañero o tú mismo) sepa qué mira, por qué y cómo probarlo.
  ¿Impacto? Sin esto, los PRs llegan con la descripción vacía y la revisión se vuelve adivinanza.
-->

Closes #

## ¿Qué cambia?

<!-- Una o dos frases. El detalle está en el diff, no lo repitas línea por línea. -->

## ¿Para qué?

<!-- La necesidad que lo motiva. Debe coincidir con el objetivo del issue enlazado arriba. -->

## ¿Impacto?

<!-- Qué habilita o qué afecta: rutas nuevas, migraciones a correr, cambios que rompen algo. -->

## ¿Cómo probarlo?

<!-- Pasos reproducibles para quien revisa. Si requiere migración o variable de entorno nueva, dilo aquí. -->

1.
2.

## Checklist

- [ ] El PR está enlazado a un issue con `Closes #N` (arriba).
- [ ] La rama sigue la convención `<tipo>/<issue>-<slug-en-ingles>`.
- [ ] Los commits siguen Conventional Commits (ver `.github/prompts/commit-message.prompt.md`).
- [ ] Nombres técnicos en inglés; comentarios y docs en español con ¿Qué? ¿Para qué? ¿Impacto?
- [ ] Los archivos nuevos llevan la cabecera obligatoria de módulo.
- [ ] Dependencias nuevas pineadas exactas (`==` en Python, `@X.Y.Z` en Node) y lock commiteado.
- [ ] Usé `pnpm` (nunca `npm` ni `yarn`) y `venv`/`uv` para Python.
- [ ] Hay tests que cubren el cambio, o explico abajo por qué no aplican.
- [ ] No hay secretos, `.env` ni credenciales reales en el diff.
- [ ] La CI está en verde.
- [ ] Leí mi propio diff completo en la pestaña **Files changed** antes de pedir revisión.

## Notas para quien revisa

<!-- Decisiones discutibles, deuda que dejas a propósito, dudas donde quieres opinión. -->
