/**
 * Archivo: api/axios.ts
 * Descripción: Instancia de Axios configurada con la URL base de la API y interceptores.
 * ¿Para qué? Centralizar la configuración HTTP — todos los módulos de API usan esta instancia.
 * ¿Impacto? Sin este archivo, cada petición tendría que configurar la URL, headers y manejo
 *           de errores por separado, causando duplicación y posibles inconsistencias.
 */

import axios from "axios";

// ¿Qué? URL base de la API leída desde variables de entorno de Vite.
// ¿Para qué? Permite cambiar la URL sin tocar código (dev: localhost:8000, prod: dominio real).
// ¿Impacto? Si VITE_API_URL no está definida, las peticiones irán a la URL relativa (fallará).
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * ¿Qué? Instancia de Axios preconfigurada con URL base, headers y timeout.
 * ¿Para qué? Reutilizar esta instancia en todos los módulos de API (auth, users, etc.).
 * ¿Impacto? Garantiza consistencia: todas las peticiones usan JSON, timeout de 10s,
 *           y la misma URL base.
 */
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000, // 10 segundos máximo por petición
});

/**
 * ¿Qué? Interceptor de request que agrega el token JWT automáticamente.
 * ¿Para qué? Cada petición a endpoints protegidos necesita el header Authorization.
 *           En vez de agregarlo manualmente en cada llamada, el interceptor lo hace.
 * ¿Impacto? Sin este interceptor, el frontend tendría que pasar el token en cada fetch,
 *           aumentando el riesgo de olvidarlo y recibir 401.
 */
api.interceptors.request.use(
  (config) => {
    // ¿Qué? Lee el access token almacenado en memoria (sessionStorage).
    // ¿Para qué? Adjuntarlo como Bearer token en el header Authorization.
    // ¿Impacto? sessionStorage se borra al cerrar el navegador — más seguro que localStorage.
    const token = sessionStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

/**
 * ¿Qué? Interceptor de response que maneja errores HTTP de forma centralizada.
 * ¿Para qué? Extraer mensajes de error del backend y formatearlos para el frontend.
 * ¿Impacto? Sin esto, cada componente tendría que parsear el error de Axios por separado.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // ¿Qué? Error HTTP del servidor (4xx, 5xx).
      // ¿Para qué? Extraer el mensaje de error del body de la respuesta.
      const data = error.response.data;

      // ¿Qué? Manejo especial para errores de validación Pydantic (422).
      // ¿Para qué? Los errores 422 tienen estructura { detail: [{loc, msg, type}] }.
      if (error.response.status === 422 && Array.isArray(data.detail)) {
        const messages = data.detail.map((err: { msg: string }) => err.msg);
        error.message = messages.join(". ");
      } else if (typeof data.detail === "string") {
        error.message = data.detail;
      }
    } else if (error.request) {
      // ¿Qué? La petición se envió pero no hubo respuesta.
      // ¿Para qué? Informar al usuario que el servidor no respondió.
      error.message = "No se pudo conectar con el servidor";
    }
    return Promise.reject(error);
  },
);

export default api;
