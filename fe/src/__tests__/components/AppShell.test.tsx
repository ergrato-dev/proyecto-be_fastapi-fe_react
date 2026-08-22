/**
 * Archivo: __tests__/components/AppShell.test.tsx
 * Descripción: Tests del shell autenticado — identidad del usuario, cierre de sesión y sidebar.
 * ¿Para qué? La ficha con el nombre y el correo del usuario vive aquí desde el rediseño con
 *            sidebar; sin estos tests, esa información quedaría sin cobertura en todo el frontend.
 * ¿Impacto? Si el bloque de usuario dejara de renderizarse, el usuario perdería la única
 *           confirmación visual de con qué cuenta está trabajando.
 */

import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppShell } from "@/components/layout/AppShell";
import { renderWithProviders, mockUser } from "../helpers";

describe("AppShell", () => {
  // ¿Qué? Verifica que el shell renderiza el contenido de la página que envuelve.
  // ¿Para qué? Es su responsabilidad principal: layout alrededor del contenido.
  it("renderiza el contenido que envuelve", () => {
    renderWithProviders(
      <AppShell>
        <p>Contenido de la página</p>
      </AppShell>,
      { authContext: { user: mockUser, isAuthenticated: true } },
    );

    expect(screen.getByText("Contenido de la página")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que se muestran nombre y correo del usuario autenticado.
  // ¿Impacto? Es la única parte de la interfaz que confirma la identidad de la sesión activa.
  it("muestra el nombre y el correo del usuario autenticado", () => {
    renderWithProviders(<AppShell>{null}</AppShell>, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    expect(screen.getByText(`${mockUser.first_name} ${mockUser.last_name}`)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  // ¿Qué? Verifica que sin sesión no se pinta la ficha de usuario.
  // ¿Para qué? Evitar renderizar un bloque vacío o con datos de una sesión anterior.
  it("no muestra la ficha de usuario si no hay sesión", () => {
    renderWithProviders(<AppShell>{null}</AppShell>, {
      authContext: { user: null, isAuthenticated: false },
    });

    expect(screen.queryByText(mockUser.email)).toBeNull();
  });

  // ¿Qué? Verifica que colapsar el sidebar oculta la ficha de usuario.
  // ¿Para qué? En modo colapsado solo caben los íconos — el texto debe desaparecer.
  // ¿Impacto? Si el texto siguiera montado, desbordaría el sidebar de 64px.
  it("oculta la ficha de usuario al colapsar el sidebar", async () => {
    const user = userEvent.setup();
    renderWithProviders(<AppShell>{null}</AppShell>, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    await user.click(screen.getByRole("button", { name: "Colapsar menú lateral" }));

    expect(screen.queryByText(mockUser.email)).toBeNull();
    expect(screen.getByRole("button", { name: "Expandir menú lateral" })).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el botón de salir invoca logout() del AuthContext.
  // ¿Para qué? Sin esta llamada, los tokens seguirían en sessionStorage tras "cerrar sesión".
  // ¿Impacto? Una sesión que no se cierra de verdad es un riesgo en equipos compartidos.
  it("cierra la sesión al pulsar salir", async () => {
    const logoutMock = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<AppShell>{null}</AppShell>, {
      authContext: { user: mockUser, isAuthenticated: true, logout: logoutMock },
    });

    await user.click(screen.getByRole("button", { name: "Salir" }));

    expect(logoutMock).toHaveBeenCalledTimes(1);
  });
});
