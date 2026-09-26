# Hallazgos para las demostraciones de testing

> ¿Qué? Defectos reales de este proyecto que se dejan **sin corregir a propósito**.
> ¿Para qué? Demostrar en clase cómo cada tipo de prueba encuentra lo que las otras no ven, en
> una app real y no en un ejemplo de juguete. Se usan en el
> [Bootcamp Testing ADSO](https://github.com/ergrato-dev/bc-testing-adso).
> ¿Impacto? Si corriges uno, actualiza esta tabla: la demostración de esa semana cambia.

Todos se reprodujeron el 26 de septiembre de 2026 con la BD de pruebas (`db-test`) y Mailpit.

| # | Hallazgo | Quién lo encuentra | Semana |
|:-:|---|---|:-:|
| 1 | El navegador bloquea `PATCH /users/me/locale` por CORS | E2E (Playwright) | 4 y 7 |
| 2 | El token de verificación se puede usar dos veces con peticiones simultáneas | Integración / API concurrente | 6 y 7 |
| 3 | El JSON mal formado responde 422 con un `detail` distinto al del resto del API | API | 4 |

Y un contraste que vale la pena mostrar: **si el SMTP está caído, el registro responde 201** y el enlace queda en el log. La app resiste la caída de una dependencia externa (semana 5). La versión Express del mismo proyecto no resiste: compáralas.

---

## 1. CORS bloquea el cambio de idioma

**Qué pasa.** `app/main.py` configura CORS con `allow_methods=["GET", "POST"]`, pero el frontend guarda el idioma con `PATCH /api/v1/users/me/locale` (`fe/src/api/auth.ts`). El navegador hace un *preflight* `OPTIONS`, recibe 400 y cancela la petición: la preferencia nunca se guarda en el servidor.

**Por qué los tests no lo ven.** Los 5 tests de `TestUpdateLocale` pasan: `TestClient` llama a la app directamente y no aplica CORS, que es una regla del navegador.

**Cómo reproducirlo.**

```bash
# Con el backend corriendo (ver e2e/playwright.config.js)
curl -i -X OPTIONS -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: PATCH" http://localhost:8000/api/v1/users/me/locale
# → 400 Bad Request, access-control-allow-methods: GET, POST
```

En Playwright: inicia sesión, pulsa **English** y escucha `page.on('requestfailed')`: aparece `PATCH …/users/me/locale net::ERR_FAILED`. Es el ejemplo de la semana 7 de un defecto que solo ve el navegador.

## 2. Token de verificación reutilizable bajo concurrencia

**Qué pasa.** `verify_email` lee el token, comprueba que no esté usado y después lo marca como usado. Dos peticiones simultáneas con el mismo token leen "no usado" antes de que alguna lo marque: **ambas responden 200**. Una tercera, ya en serie, sí responde 400 (*"Este token de verificación ya fue utilizado"*).

**Por qué los tests no lo ven.** Los tests de API hacen una petición a la vez. El rollback por test tampoco permite ver dos transacciones concurrentes.

**Cómo reproducirlo.** Registra un usuario, toma el token del correo en Mailpit (`http://localhost:8025`) y lanza dos `POST /api/v1/auth/verify-email` en paralelo (por ejemplo, dos `curl … &` y `wait`). En 5 de 5 intentos respondieron 200 y 200.

**Pista.** Actualizar el token con una condición (`UPDATE … SET used = true WHERE token = :t AND used = false`) y comprobar cuántas filas cambió, o bloquear la fila con `SELECT … FOR UPDATE`.

## 3. Contrato de error del JSON mal formado

**Qué pasa.** `POST /api/v1/auth/login` con el cuerpo `{"email":` responde `422` con `detail` como **lista** de errores de Pydantic, mientras que los errores de la app usan `detail` como **texto**. El frontend tiene que manejar dos formas distintas.

**Cómo reproducirlo.**

```bash
curl -s -H 'content-type: application/json' -d '{"email":' http://localhost:8000/api/v1/auth/login
```

Es un buen caso para la semana 4: escribir el test del contrato y decidir qué forma debe tener.

---

## Ya corregido en este repo (no son demostraciones)

- Los tests de pytest corrían sobre la BD de desarrollo y ejecutaban `drop_all`. Ahora usan `TEST_DATABASE_URL` (servicio `db-test`) y crean el esquema con Alembic.
- Ningún test envía correos reales: el fixture `sent_emails` reemplaza el envío.
- El CI exige cobertura y corre los E2E con PostgreSQL y Mailpit como servicios.
