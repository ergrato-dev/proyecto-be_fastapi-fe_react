/**
 * Archivo: e2e/tests/support/auth-dialogs.js
 * Descripción: Objeto de página de los diálogos de registro e inicio de sesión.
 * ¿Para qué? Que los tests no repitan los mismos locators: si una etiqueta cambia, se
 *   corrige aquí y no en cada test.
 * ¿Impacto? Solo tiene locators y acciones; las aserciones se quedan en los tests.
 */

export class AuthDialogs {
  constructor(page) {
    this.page = page;
    this.dialog = page.getByRole("dialog");
  }

  async register({ firstName, lastName, email, password }) {
    await this.page.goto("/register");
    await this.dialog.getByLabel("Nombres").fill(firstName);
    await this.dialog.getByLabel("Apellidos").fill(lastName);
    await this.dialog.getByLabel("Correo electrónico", { exact: true }).fill(email);
    await this.dialog.getByLabel("Confirmar correo electrónico").fill(email);
    await this.dialog.getByLabel("Contraseña", { exact: true }).fill(password);
    await this.dialog.getByLabel("Confirmar contraseña").fill(password);
    for (const consent of await this.dialog.getByRole("checkbox").all()) {
      await consent.check();
    }
    await this.dialog.getByRole("button", { name: "Crear cuenta" }).click();
  }

  async login(email, password) {
    await this.page.goto("/login");
    await this.dialog.getByLabel("Correo electrónico").fill(email);
    await this.dialog.getByLabel("Contraseña", { exact: true }).fill(password);
    await this.dialog.getByRole("button", { name: "Iniciar sesión" }).click();
  }
}
