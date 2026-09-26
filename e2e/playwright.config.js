/**
 * Archivo: e2e/playwright.config.js
 * Descripción: Configuración de Playwright para los tests E2E del sistema completo.
 * ¿Para qué? Levantar backend y frontend, y correr los flujos críticos en un navegador real.
 * ¿Impacto? Con un solo `pnpm test` se prueba la app de punta a punta. Antes hay que levantar
 *   la BD de pruebas y Mailpit: docker compose up -d --wait db-test mailpit
 */

import { defineConfig, devices } from "@playwright/test";

// ¿Qué? Puertos del frontend y del backend. Cámbialos si ya están ocupados en tu equipo.
const frontPort = Number(process.env.FRONT_PORT ?? 5173);
const apiPort = Number(process.env.API_PORT ?? 8000);
const frontUrl = `http://localhost:${frontPort}`;
const apiUrl = `http://localhost:${apiPort}`;

export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: frontUrl,
    // ¿Qué? La app detecta el idioma del navegador; los tests esperan los textos en español.
    locale: "es-CO",
    // ¿Qué? Guarda la traza cuando un test falla y se reintenta: se abre con `pnpm report`.
    trace: "on-first-retry",
  },
  reporter: [["list"], ["html", { open: "never" }]],
  retries: process.env.CI ? 1 : 0,
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  // ¿Qué? Playwright levanta backend y frontend antes de los tests y los apaga al terminar.
  // ¿Impacto? En tu equipo reutiliza los que ya estén corriendo (reuseExistingServer).
  webServer: [
    {
      // ¿Qué? Migra la BD de pruebas y arranca FastAPI. `exec` deja a uvicorn como proceso
      //   principal, así Playwright lo detiene al terminar.
      command: `sh -c "uv run alembic upgrade head && exec uv run uvicorn app.main:app --port ${apiPort}"`,
      cwd: "../be",
      url: `${apiUrl}/api/v1/health`,
      reuseExistingServer: !process.env.CI,
      env: {
        // BD de pruebas desechable (servicio db-test), nunca la de desarrollo.
        DATABASE_URL:
          process.env.E2E_DATABASE_URL ??
          "postgresql://nn_user:nn_password@localhost:5433/nn_auth_test",
        // Valor de prueba, nunca el de producción (mínimo 32 caracteres).
        SECRET_KEY: process.env.SECRET_KEY ?? "e2e-secret-key-not-for-production-32chars",
        // Los correos van a Mailpit; los tests leen el enlace de verificación desde su API.
        SMTP_HOST: "localhost",
        SMTP_PORT: "1025",
        FRONTEND_URL: frontUrl,
        ENVIRONMENT: "development",
        // Los tests registran e inician sesión muchas veces desde la misma IP: sin esto,
        // el límite de 5 registros por minuto los haría fallar al azar.
        RATE_LIMIT_ENABLED: "false",
      },
    },
    {
      // Se lanza vite con node, sin pnpm de por medio, para que Playwright pueda detenerlo.
      command: `node node_modules/vite/bin/vite.js --port ${frontPort} --strictPort`,
      cwd: "../fe",
      url: frontUrl,
      reuseExistingServer: !process.env.CI,
      env: { VITE_API_URL: apiUrl },
    },
  ],
});
