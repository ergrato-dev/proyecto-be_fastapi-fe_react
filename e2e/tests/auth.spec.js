/**
 * Archivo: e2e/tests/auth.spec.js
 * Descripción: Flujos críticos de autenticación en un navegador real, con backend, BD y Mailpit.
 */

import { expect, test } from "@playwright/test";
import { AuthDialogs } from "./support/auth-dialogs.js";
import { apiUrl } from "./support/env.js";
import { findLinkInEmail } from "./support/mailpit.js";

const password = "Segura123";

// ¿Qué? Correo único por test: los tests corren en paralelo sobre la misma BD.
function uniqueEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@nn-company.com`;
}

test("should register, verify the email from Mailpit and reach the dashboard", async ({
  page,
  request,
}) => {
  // Arrange
  const auth = new AuthDialogs(page);
  const email = uniqueEmail();

  // Act: registro por la UI
  await auth.register({ firstName: "Ana", lastName: "Prueba", email, password });

  // Assert: la app pide verificar el correo
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(email);

  // Act: la persona abre el enlace del correo que llegó a Mailpit
  await page.goto(await findLinkInEmail(request, email, "/verify-email"));
  await expect(page.getByText("¡Tu email ha sido verificado exitosamente!")).toBeVisible();

  // Act: inicia sesión
  await auth.login(email, password);

  // Assert: llega al dashboard con su nombre
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Bienvenido, ANA PRUEBA");
});

test("should show an error and stay on login when the password is wrong", async ({
  page,
  request,
}) => {
  // Arrange: la cuenta se crea por API; el test prueba solo el login
  const email = uniqueEmail();
  const response = await request.post(`${apiUrl}/api/v1/auth/register`, {
    data: { email, first_name: "Ana", last_name: "Prueba", password },
  });
  expect(response.ok()).toBe(true);
  const auth = new AuthDialogs(page);

  // Act
  await auth.login(email, "Incorrecta123");

  // Assert
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});

test("should redirect to login when opening the dashboard without a session", async ({
  page,
}) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/login$/);
});
