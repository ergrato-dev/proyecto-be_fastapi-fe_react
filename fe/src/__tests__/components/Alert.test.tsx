/**
 * Archivo: __tests__/components/Alert.test.tsx
 * Descripción: Tests del componente Alert — tipos, mensaje, botón de cierre.
 * ¿Para qué? Verificar que las alertas muestran el mensaje correcto, el ícono según tipo
 *           y que el botón de cierre ejecuta onClose.
 * ¿Impacto? Sin estos tests, un cambio en Alert podría romper el feedback de error/éxito.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Alert } from "@/components/ui/Alert";

describe("Alert", () => {
  // ¿Qué? Verifica que el mensaje se muestra correctamente.
  it("renderiza el mensaje proporcionado", () => {
    render(<Alert type="info" message="Esto es informativo" />);
    expect(screen.getByText("Esto es informativo")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el rol de alerta está presente (accesibilidad).
  it("tiene role='alert' para accesibilidad", () => {
    render(<Alert type="error" message="Error" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  // ¿Qué? Verifica las tres variantes de tipo.
  it.each(["success", "error", "info"] as const)("renderiza correctamente el tipo '%s'", (type) => {
    render(<Alert type={type} message={`Alerta ${type}`} />);
    expect(screen.getByText(`Alerta ${type}`)).toBeInTheDocument();
  });

  // ¿Qué? Verifica que no se muestra botón de cierre si no se pasa onClose.
  it("no muestra botón de cierre sin onClose", () => {
    render(<Alert type="info" message="Sin cierre" />);
    expect(screen.queryByLabelText("Cerrar alerta")).not.toBeInTheDocument();
  });

  // ¿Qué? Verifica que el botón de cierre aparece y ejecuta onClose.
  it("muestra botón de cierre y ejecuta onClose al hacer clic", async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();

    render(<Alert type="error" message="Cerrable" onClose={handleClose} />);

    const closeButton = screen.getByLabelText("Cerrar alerta");
    expect(closeButton).toBeInTheDocument();

    await user.click(closeButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
