/**
 * Archivo: __tests__/components/PasswordStrengthIndicator.test.tsx
 * Descripción: Tests del indicador de fortaleza de contraseña — cálculo, renderizado y accesibilidad.
 * ¿Para qué? Garantizar que las 4 barras y etiquetas reflejan correctamente la fortaleza calculada.
 * ¿Impacto? Un indicador incorrecto daría retroalimentación falsa, induciendo al usuario a
 *           creer que su contraseña es fuerte cuando no lo es.
 */

import { render, screen } from "@testing-library/react";
import { PasswordStrengthIndicator } from "@/components/ui/PasswordStrengthIndicator";
import { calculatePasswordStrength } from "@/utils/passwordStrength";

// ════════════════════════════════════════
// Tests de la función calculatePasswordStrength (lógica pura)
// ════════════════════════════════════════

describe("calculatePasswordStrength", () => {
  // ¿Qué? Contraseña vacía → nivel 0 (no se muestra el indicador).
  it("retorna 0 para contraseña vacía", () => {
    expect(calculatePasswordStrength("")).toBe(0);
  });

  // ¿Qué? Solo cumple un criterio (mayúscula, sin longitud ni otros) → nivel 1.
  it("retorna 1 cuando solo se cumple un criterio", () => {
    // "A": uppercase ✓  |  length < 8 ✗  |  lowercase ✗  |  digit ✗  → score 1
    expect(calculatePasswordStrength("A")).toBe(1);
  });

  // ¿Qué? Longitud + minúscula → nivel 2.
  it("retorna 2 cuando se cumplen 2 criterios (longitud + minúscula)", () => {
    // "aaaaaaaa": length ✓  |  lowercase ✓  |  uppercase ✗  |  digit ✗  → score 2
    expect(calculatePasswordStrength("aaaaaaaa")).toBe(2);
  });

  // ¿Qué? Contraseña con longitud, minúscula y mayúscula → nivel 3.
  it("retorna 3 cuando se cumplen 3 criterios", () => {
    // longitud + minúscula + mayúscula
    expect(calculatePasswordStrength("Aaaaaaaa")).toBe(3);
  });

  // ¿Qué? Contraseña que cumple todos los criterios → nivel 4 (fuerte).
  it("retorna 4 cuando se cumplen todos los criterios", () => {
    // longitud + mayúscula + minúscula + dígito
    expect(calculatePasswordStrength("Password1")).toBe(4);
  });

  // ¿Qué? Contraseña corta con mayúsculas, minúsculas y dígito → nivel 3 (sin longitud).
  it("retorna 3 si tiene mayúscula, minúscula y dígito pero < 8 chars", () => {
    // mayúscula + minúscula + dígito, pero length=4
    expect(calculatePasswordStrength("Ab1x")).toBe(3);
  });

  // ¿Qué? Contraseña de un solo carácter → nivel mínimo activo (1).
  it("retorna al menos 1 para cualquier contraseña no vacía", () => {
    expect(calculatePasswordStrength("a")).toBeGreaterThanOrEqual(1);
  });
});

// ════════════════════════════════════════
// Tests del componente PasswordStrengthIndicator (renderizado)
// ════════════════════════════════════════

describe("PasswordStrengthIndicator", () => {
  // ¿Qué? No se renderiza con contraseña vacía.
  // ¿Para qué? El formulario debe verse limpio antes de que el usuario escriba.
  it("no renderiza nada cuando la contraseña está vacía", () => {
    const { container } = render(<PasswordStrengthIndicator password="" />);
    expect(container.firstChild).toBeNull();
  });

  // ¿Qué? Muestra etiqueta "Muy débil" para contraseñas de nivel 1.
  it('muestra "Muy débil" para contraseña de nivel 1', () => {
    // Solo minúsculas de longitud < 8 → 1 criterio (minúscula)
    render(<PasswordStrengthIndicator password="a" />);
    expect(screen.getByText("Muy débil")).toBeInTheDocument();
  });

  // ¿Qué? Muestra etiqueta "Débil" para contraseñas de nivel 2.
  it('muestra "Débil" para contraseña de nivel 2', () => {
    // longitud(8) + minúscula = 2 criterios
    render(<PasswordStrengthIndicator password="aaaaaaaa" />);
    expect(screen.getByText("Débil")).toBeInTheDocument();
  });

  // ¿Qué? Muestra etiqueta "Buena" para contraseñas de nivel 3.
  it('muestra "Buena" para contraseña de nivel 3', () => {
    // longitud(8) + mayúscula + minúscula = 3 criterios
    render(<PasswordStrengthIndicator password="Aaaaaaaa" />);
    expect(screen.getByText("Buena")).toBeInTheDocument();
  });

  // ¿Qué? Muestra etiqueta "Fuerte" para contraseñas que cumplen todos los criterios.
  it('muestra "Fuerte" para contraseña que cumple todos los criterios', () => {
    render(<PasswordStrengthIndicator password="Password1" />);
    expect(screen.getByText("Fuerte")).toBeInTheDocument();
  });

  // ¿Qué? Verifica que existe el aria-label con la descripción del nivel.
  // ¿Para qué? Accesibilidad — lectores de pantalla anuncian la fortaleza sin depender del color.
  // ¿Impacto? WCAG 1.4.1 exige que la información no se transmita solo por color.
  it("tiene aria-label con la descripción textual del nivel", () => {
    render(<PasswordStrengthIndicator password="Password1" />);
    expect(
      screen.getByRole("status", { name: "Fortaleza de contraseña: Fuerte" }),
    ).toBeInTheDocument();
  });

  // ¿Qué? Verifica que siempre se renderizan exactamente 4 barras.
  // ¿Para qué? La representación visual de "4 barras = 4 criterios" es parte del contrato de diseño.
  it("siempre renderiza 4 barras", () => {
    const { container } = render(<PasswordStrengthIndicator password="Password1" />);
    // Las barras son div hijos directos del contenedor de barras (aria-hidden)
    const barsContainer = container.querySelector("[aria-hidden='true']");
    expect(barsContainer?.children).toHaveLength(4);
  });
});
