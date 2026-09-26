/**
 * Archivo: e2e/tests/support/mailpit.js
 * Descripción: Lee los correos que el backend envió a Mailpit, usando su API HTTP.
 * ¿Para qué? Completar en el test el flujo real de verificación: el backend envía el correo
 *   y el test abre el mismo enlace que abriría la persona.
 * ¿Impacto? Sin esto, el E2E tendría que saltarse la verificación escribiendo en la BD.
 */

import { expect } from "@playwright/test";
import { mailpitUrl } from "./env.js";

// ¿Qué? Espera a que llegue a Mailpit un correo para `email` y devuelve el primer enlace
//   que contiene `path` (por ejemplo "/verify-email").
// ¿Impacto? expect.poll reintenta sin pausas fijas: el correo puede tardar unos milisegundos.
export async function findLinkInEmail(request, email, path) {
  let link;
  await expect
    .poll(async () => {
      const query = encodeURIComponent(`to:${email}`);
      const search = await (await request.get(`${mailpitUrl}/api/v1/search?query=${query}`)).json();
      if (search.messages_count === 0) return undefined;
      const message = await (
        await request.get(`${mailpitUrl}/api/v1/message/${search.messages[0].ID}`)
      ).json();
      link = message.Text.match(new RegExp(`https?://\\S+${path}\\?token=[\\w-]+`))?.[0];
      return link;
    })
    .toBeDefined();
  return link;
}
