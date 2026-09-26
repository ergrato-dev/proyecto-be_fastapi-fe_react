/**
 * Archivo: e2e/tests/support/env.js
 * Descripción: URLs del API y de Mailpit que usan los tests para preparar datos y leer correos.
 * ¿Para qué? Tener un solo lugar con los mismos valores por defecto que playwright.config.js.
 */

export const apiUrl = process.env.API_URL ?? `http://localhost:${process.env.API_PORT ?? 8000}`;
export const mailpitUrl = process.env.MAILPIT_URL ?? "http://localhost:8025";
