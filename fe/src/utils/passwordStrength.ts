/**
 * Archivo: utils/passwordStrength.ts
 * Descripción: Cálculo de la fortaleza de una contraseña a partir de cuatro criterios.
 * ¿Para qué? Aislar la lógica pura del componente que la dibuja, para poder testearla sola
 *            y reutilizarla desde cualquier formulario que pida contraseña.
 * ¿Impacto? Un archivo de componente que además exporta funciones rompe el Fast Refresh de
 *           Vite (regla `react-refresh/only-export-components`): al editar el componente se
 *           recarga la página entera en vez de actualizar solo el componente.
 */

/**
 * ¿Qué? Nivel de fortaleza calculado a partir de los criterios de la contraseña.
 * ¿Para qué? Tipado explícito para evitar valores inválidos en el cálculo de fortaleza.
 * ¿Impacto? TypeScript garantiza que solo se usen los cuatro valores definidos.
 */
export type PasswordStrength = 0 | 1 | 2 | 3 | 4;

/**
 * ¿Qué? Calcula la fortaleza de una contraseña evaluando cuatro criterios.
 * ¿Para qué? Centralizamos la lógica de cálculo fuera del componente para poder testearla
 *            de forma independiente y reutilizarla si fuese necesario.
 * ¿Impacto? Un punto por cada criterio:
 *           1 — longitud >= 8 caracteres
 *           2 — contiene al menos una letra mayúscula
 *           3 — contiene al menos una letra minúscula
 *           4 — contiene al menos un número
 *           Total 0 (vacío), 1 (muy débil), 2 (débil), 3 (buena), 4 (fuerte).
 */
export function calculatePasswordStrength(password: string): PasswordStrength {
  if (!password) return 0;

  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;

  return score as PasswordStrength;
}
