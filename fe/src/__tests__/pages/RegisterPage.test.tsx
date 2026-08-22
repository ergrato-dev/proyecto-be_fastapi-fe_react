/**
 * Archivo: __tests__/pages/RegisterPage.test.tsx
 * Descripción: Tests de la página de registro — campos, validación cliente, envío, errores.
 * ¿Para qué? Asegurar que el flujo de registro funciona correctamente y valida inputs.
 * ¿Impacto? Si el registro falla silenciosamente, los usuarios no podrían crear cuentas.
 *
 * NOTA: el formulario exige los tres consentimientos legales (Ley 1581/2012, Ley 1480/2011)
 * y mantiene el botón deshabilitado hasta que todos los campos tengan valor. Por eso los
 * tests llenan el formulario con el helper `fillForm` antes de intentar enviarlo.
 */

import { createEvent, fireEvent, screen } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import userEvent from "@testing-library/user-event";
import { RegisterPage } from "@/pages/RegisterPage";
import { renderWithProviders } from "../helpers";

// ¿Qué? Valores por defecto de un formulario de registro válido.
// ¿Para qué? Cada test sobreescribe solo el campo que quiere poner a prueba.
// ¿Impacto? Evita repetir seis `user.type` en cada caso.
const VALID_FORM = {
  Nombres: "Juan",
  Apellidos: "Pérez",
  "Correo electrónico": "juan@nn.com",
  "Confirmar correo electrónico": "juan@nn.com",
  Contraseña: "Password1",
  "Confirmar contraseña": "Password1",
};

/**
 * ¿Qué? Llena el formulario y marca los tres consentimientos legales.
 * ¿Para qué? El botón "Crear cuenta" está deshabilitado mientras falte un campo o un
 *            consentimiento — sin esto, el click no dispara la validación y nada se muestra.
 * ¿Impacto? Permite que cada test se centre en el campo inválido que quiere verificar.
 */
async function fillForm(user: UserEvent, overrides: Partial<typeof VALID_FORM> = {}) {
  const values = { ...VALID_FORM, ...overrides };

  for (const [label, value] of Object.entries(values)) {
    if (value === "") continue;
    await user.type(screen.getByLabelText(label), value);
  }

  // ¿Qué? Los tres checkboxes de consentimiento legal.
  // ¿Impacto? Sin marcarlos, `isButtonEnabled` es false y el submit nunca ocurre.
  for (const checkbox of screen.getAllByRole("checkbox")) {
    await user.click(checkbox);
  }
}

describe("RegisterPage", () => {
  // ¿Qué? Verifica que todos los campos del formulario están presentes.
  it("renderiza el formulario completo de registro", () => {
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    expect(screen.getByRole("heading", { name: "Crear cuenta" })).toBeInTheDocument();
    expect(screen.getByLabelText("Nombres")).toBeInTheDocument();
    expect(screen.getByLabelText("Apellidos")).toBeInTheDocument();
    expect(screen.getByLabelText("Correo electrónico")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirmar correo electrónico")).toBeInTheDocument();
    expect(screen.getByLabelText("Contraseña")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirmar contraseña")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeInTheDocument();
  });

  // ¿Qué? Verifica que existe enlace a login.
  // ¿Para qué? La página lo ofrece dos veces (aviso de verificación y pie del formulario),
  //            por eso se consultan todos los enlaces con ese nombre y no uno solo.
  it("muestra enlace a iniciar sesión", () => {
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    const loginLinks = screen.getAllByRole("link", { name: "Iniciar sesión" });
    expect(loginLinks.length).toBeGreaterThan(0);
    expect(loginLinks[0]).toHaveAttribute("href", "/login");
  });

  // ¿Qué? Verifica que el botón sigue bloqueado si falta un campo obligatorio.
  // ¿Para qué? Es la primera barrera del formulario: sin todos los campos no hay envío.
  // ¿Impacto? Si el botón se habilitara, se enviarían registros incompletos al backend.
  it("mantiene deshabilitado el botón si falta un campo", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    await fillForm(user, { "Confirmar correo electrónico": "" });

    expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeDisabled();
  });

  // ¿Qué? Verifica que el botón sigue bloqueado si falta un consentimiento legal.
  // ¿Para qué? Ley 1581/2012 — el consentimiento debe ser explícito, no asumido.
  // ¿Impacto? Sin este bloqueo, se registrarían usuarios sin aceptar los documentos legales.
  it("mantiene deshabilitado el botón si falta un consentimiento", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    for (const [label, value] of Object.entries(VALID_FORM)) {
      await user.type(screen.getByLabelText(label), value);
    }
    const [terms, privacy] = screen.getAllByRole("checkbox");
    await user.click(terms);
    await user.click(privacy);

    expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeDisabled();
  });

  // ¿Qué? Verifica validación de nombre corto.
  it("muestra error si el nombre tiene menos de 2 caracteres", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    await fillForm(user, { Nombres: "A" });
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(screen.getByText("El nombre debe tener al menos 2 caracteres")).toBeInTheDocument();
  });

  // ¿Qué? Verifica validación de contraseña débil.
  it("muestra error si la contraseña es muy corta", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    await fillForm(user, { Contraseña: "Ab1", "Confirmar contraseña": "Ab1" });
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(screen.getByText("Mínimo 8 caracteres")).toBeInTheDocument();
  });

  // ¿Qué? Verifica validación de contraseñas que no coinciden.
  it("muestra error si las contraseñas no coinciden", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    await fillForm(user, { "Confirmar contraseña": "Password2" });
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(screen.getByText("Las contraseñas no coinciden")).toBeInTheDocument();
  });

  // ¿Qué? Verifica validación de correos que no coinciden.
  // ¿Para qué? Confirmar que la comparación email vs confirmEmail funciona correctamente.
  // ¿Impacto? Sin este test, podría colarse una regresión que permita registros con emails distintos.
  it("muestra error si los correos no coinciden", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    await fillForm(user, { "Confirmar correo electrónico": "otro@b.com" });
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(screen.getByText("Los correos electrónicos no coinciden")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el campo "confirmar correo" bloquea el pegado.
  // ¿Para qué? Garantizar que el usuario escribe el correo a mano — la defensa técnica
  //            contra el anti-patrón de copiar y pegar el mismo dato erróneo dos veces.
  // ¿Impacto? Si defaultPrevented=false, el usuario podría pegar sin intervención humana.
  it("bloquea el pegado en el campo confirmar correo electrónico", () => {
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    const input = screen.getByLabelText("Confirmar correo electrónico");
    const pasteEvent = createEvent.paste(input);
    fireEvent(input, pasteEvent);

    expect(pasteEvent.defaultPrevented).toBe(true);
  });

  // ¿Qué? Verifica que el campo "confirmar contraseña" también bloquea el pegado.
  // ¿Para qué? Misma garantía de intervención humana que para el correo.
  // ¿Impacto? Sin este bloqueo, contraseñas erróneas podrían confirmarse por accidente.
  it("bloquea el pegado en el campo confirmar contraseña", () => {
    renderWithProviders(<RegisterPage />, { initialRoute: "/register" });

    const input = screen.getByLabelText("Confirmar contraseña");
    const pasteEvent = createEvent.paste(input);
    fireEvent(input, pasteEvent);

    expect(pasteEvent.defaultPrevented).toBe(true);
  });

  // ¿Qué? Verifica que register() se llama con datos correctos.
  it("ejecuta register al enviar formulario válido", async () => {
    const registerMock = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderWithProviders(<RegisterPage />, {
      initialRoute: "/register",
      authContext: { register: registerMock },
    });

    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(registerMock).toHaveBeenCalledWith({
      email: "juan@nn.com",
      first_name: "Juan",
      last_name: "Pérez",
      password: "Password1",
    });
  });

  // ¿Qué? Verifica que muestra error del backend.
  it("muestra alerta de error cuando register falla", async () => {
    const registerMock = vi.fn().mockRejectedValue(new Error("El email ya está registrado"));
    const user = userEvent.setup();

    renderWithProviders(<RegisterPage />, {
      initialRoute: "/register",
      authContext: { register: registerMock },
    });

    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByText("El email ya está registrado")).toBeInTheDocument();
  });
});
