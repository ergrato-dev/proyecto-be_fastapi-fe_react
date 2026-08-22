/**
 * Archivo: __tests__/components/InputField.test.tsx
 * Descripción: Tests del componente InputField — label, error, password toggle, accesibilidad.
 * ¿Para qué? Verificar que el input muestra label, placeholder, errores de validación
 *           y el toggle de visibilidad de contraseña.
 * ¿Impacto? Este componente se usa en TODOS los formularios — fallos aquí afectan todo.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InputField } from "@/components/ui/InputField";

describe("InputField", () => {
  // ¿Qué? Props base que se reutilizan en cada test.
  const baseProps = {
    label: "Correo electrónico",
    name: "email",
    value: "",
    onChange: vi.fn(),
  };

  // ¿Qué? Verifica que el label se renderiza correctamente.
  it("renderiza el label", () => {
    render(<InputField {...baseProps} />);
    expect(screen.getByLabelText("Correo electrónico")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el placeholder se muestra.
  it("muestra el placeholder", () => {
    render(<InputField {...baseProps} placeholder="correo@ejemplo.com" />);
    expect(screen.getByPlaceholderText("correo@ejemplo.com")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el valor se refleja en el input.
  it("muestra el valor proporcionado", () => {
    render(<InputField {...baseProps} value="test@test.com" />);
    expect(screen.getByLabelText("Correo electrónico")).toHaveValue("test@test.com");
  });

  // ¿Qué? Verifica que onChange se ejecuta al escribir.
  it("ejecuta onChange al escribir", async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<InputField {...baseProps} onChange={handleChange} />);
    await user.type(screen.getByLabelText("Correo electrónico"), "a");

    expect(handleChange).toHaveBeenCalled();
  });

  // ¿Qué? Verifica que el mensaje de error se muestra.
  it("muestra el mensaje de error", () => {
    render(<InputField {...baseProps} error="El correo es obligatorio" />);
    expect(screen.getByText("El correo es obligatorio")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que aria-invalid se activa cuando hay error.
  it("marca aria-invalid cuando hay error", () => {
    render(<InputField {...baseProps} error="Error" />);
    expect(screen.getByLabelText("Correo electrónico")).toHaveAttribute("aria-invalid", "true");
  });

  // ¿Qué? Verifica que el error tiene role="alert" (accesibilidad).
  it("el mensaje de error tiene role='alert'", () => {
    render(<InputField {...baseProps} error="Campo requerido" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Campo requerido");
  });

  // ¿Qué? Verifica que no se muestra error cuando no hay.
  it("no muestra error cuando no hay", () => {
    render(<InputField {...baseProps} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  // ¿Qué? Verifica que el input de password tiene botón de toggle.
  it("muestra botón de mostrar/ocultar en campos de password", () => {
    render(<InputField {...baseProps} type="password" />);
    expect(screen.getByLabelText("Mostrar contraseña")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el toggle cambia el tipo de input.
  it("alterna entre password y text al hacer clic en el toggle", async () => {
    const user = userEvent.setup();

    render(<InputField {...baseProps} name="password" type="password" />);
    const input = screen.getByLabelText("Correo electrónico");

    // Inicialmente es password.
    expect(input).toHaveAttribute("type", "password");

    // Clic en mostrar → cambia a text.
    await user.click(screen.getByLabelText("Mostrar contraseña"));
    expect(input).toHaveAttribute("type", "text");

    // Clic en ocultar → vuelve a password.
    await user.click(screen.getByLabelText("Ocultar contraseña"));
    expect(input).toHaveAttribute("type", "password");
  });

  // ¿Qué? Verifica que inputs no-password NO muestran toggle.
  it("no muestra toggle para inputs de tipo text", () => {
    render(<InputField {...baseProps} type="text" />);
    expect(screen.queryByLabelText("Mostrar contraseña")).not.toBeInTheDocument();
  });

  // ¿Qué? Verifica que el icono se renderiza a la izquierda del input.
  // ¿Para qué? Confirmar que la prop icon se muestra correctamente.
  // ¿Impacto? Sin este test, podríamos romper los iconos sin darnos cuenta.
  it("renderiza el icono cuando se pasa la prop icon", () => {
    render(<InputField {...baseProps} icon={<span data-testid="test-icon">icon</span>} />);
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que sin la prop icon no se agrega el contenedor del icono.
  it("no renderiza contenedor de icono cuando no se pasa la prop", () => {
    const { container } = render(<InputField {...baseProps} />);
    expect(container.querySelector(".pointer-events-none")).not.toBeInTheDocument();
  });
});
