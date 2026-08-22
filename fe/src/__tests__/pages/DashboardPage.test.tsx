/**
 * Archivo: __tests__/pages/DashboardPage.test.tsx
 * Descripción: Tests del dashboard — saludo al usuario y demo del componente genérico DataTable.
 * ¿Para qué? Verificar que el usuario autenticado ve su saludo y que el mismo DataTable
 *            funciona con dos datasets distintos (empleados y productos).
 * ¿Impacto? Es la pantalla principal post-login y la demo didáctica del patrón
 *           "componente genérico + definición de columnas externas".
 *
 * NOTA: la ficha de perfil (correo, estado, fecha de registro, botón de cambiar contraseña)
 * ya no vive en esta página — el rediseño con AppShell movió el correo a la barra lateral
 * (`components/layout/AppShell.tsx`). Estos tests describen la página actual, no la anterior.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DashboardPage } from "@/pages/DashboardPage";
import { renderWithProviders, mockUser } from "../helpers";

describe("DashboardPage", () => {
  // ¿Qué? Verifica que se muestra el saludo con el nombre del usuario.
  it("muestra el nombre del usuario en el saludo", () => {
    renderWithProviders(<DashboardPage />, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    expect(
      screen.getByText(`Bienvenido, ${mockUser.first_name} ${mockUser.last_name}`),
    ).toBeInTheDocument();
  });

  // ¿Qué? Verifica el subtítulo de la página.
  // ¿Para qué? Confirmar que el encabezado se traduce (no muestra la clave i18n cruda).
  it("muestra el subtítulo del panel", () => {
    renderWithProviders(<DashboardPage />, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    expect(screen.getByText("Panel de control de tu cuenta")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el dataset por defecto es el de empleados.
  // ¿Para qué? La tabla debe renderizar datos reales, no un estado vacío.
  // ¿Impacto? Si DataTable dejara de recibir data o columns, este test falla.
  it("renderiza la tabla de empleados por defecto", () => {
    renderWithProviders(<DashboardPage />, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    const table = screen.getByRole("table");
    expect(within(table).getByText("Ana Sofía Ramírez")).toBeInTheDocument();
    expect(within(table).getByRole("columnheader", { name: /Departamento/ })).toBeInTheDocument();
  });

  // ¿Qué? Verifica que el toggle cambia el dataset de la misma instancia de DataTable.
  // ¿Para qué? Es el concepto central de la demo: el componente es genérico sobre T.
  // ¿Impacto? Si el swap de data + columns se rompe, se pierde el ejemplo didáctico.
  it("cambia al dataset de productos con el toggle", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DashboardPage />, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    await user.click(screen.getByRole("button", { name: "Productos" }));

    const table = screen.getByRole("table");
    expect(within(table).getByRole("columnheader", { name: /Categoría/ })).toBeInTheDocument();
    expect(within(table).queryByRole("columnheader", { name: /Departamento/ })).toBeNull();
  });

  // ¿Qué? Verifica que las acciones de fila reciben el objeto completo de la fila.
  // ¿Para qué? Demostrar el patrón RowAction<T> — la acción conoce el registro, no solo el ID.
  // ¿Impacto? Sin este test, una regresión en `actions` pasaría desapercibida.
  it("muestra el feedback de la acción ejecutada sobre una fila", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DashboardPage />, {
      authContext: { user: mockUser, isAuthenticated: true },
    });

    // ¿Qué? Abrir el menú de acciones de la primera fila y ejecutar "Ver perfil".
    // ¿Impacto? El feedback debe nombrar al empleado, probando que recibió la fila entera.
    const [firstRowMenu] = screen.getAllByRole("button", { name: /acciones/i });
    await user.click(firstRowMenu);
    await user.click(await screen.findByRole("menuitem", { name: "Ver perfil" }));

    expect(screen.getByText(/Ver perfil → Ana Sofía Ramírez/)).toBeInTheDocument();
  });
});
