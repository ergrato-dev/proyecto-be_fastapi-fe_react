/**
 * Archivo: vite.config.ts
 * Descripción: Configuración de Vite — bundler y servidor de desarrollo.
 * ¿Para qué? Definir plugins (React, TailwindCSS), alias de paths y opciones del servidor.
 * ¿Impacto? Sin esta configuración, Vite no sabría cómo procesar JSX, TypeScript ni TailwindCSS.
 */

/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// ¿Qué? Configuración principal de Vite con plugins, alias y testing.
// ¿Para qué? React para JSX, TailwindCSS para estilos utility-first, alias para imports limpios.
// ¿Impacto? Permite usar `@/` como alias a `src/`, simplificando imports entre módulos.
//           También configura Vitest para tests unitarios con jsdom.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    open: false,
  },
  // ¿Qué? Configuración de Vitest integrada en Vite.
  // ¿Para qué? Definir entorno (jsdom), globals, setup y cobertura.
  // ¿Impacto? Sin esto, Vitest no sabría dónde buscar tests ni cómo simular el DOM.
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      // ¿Qué? "html" genera coverage/index.html, que el CI sube como artefacto.
      reporter: ["text", "text-summary", "html"],
      include: ["src/**/*.{ts,tsx}"],
      // ¿Qué? Se mide la lógica de la interfaz. Quedan fuera los tests, el arranque
      //       (main.tsx, App.tsx con las rutas), la configuración (i18n.ts), los tipos y el
      //       cliente HTTP (src/api), que se prueba con MSW a nivel de red.
      exclude: [
        "src/__tests__/**",
        "src/main.tsx",
        "src/App.tsx",
        "src/i18n.ts",
        "src/vite-env.d.ts",
        "src/types/**",
        "src/api/**",
      ],
      // ¿Qué? Umbral mínimo: `pnpm test:coverage` falla si la cobertura baja de aquí.
      // ¿Impacto? Es la cobertura real redondeada hacia abajo (regla de trinquete): solo
      //           sube, PR a PR, hasta el 80%. Sin cubrir aún: AuthContext, Navbar,
      //           AppLayout y ContactPage.
      thresholds: { statements: 64, branches: 67, functions: 62, lines: 65 },
    },
  },
});
