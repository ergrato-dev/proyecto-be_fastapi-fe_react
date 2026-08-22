/**
 * Archivo: VerifyEmailPage.tsx
 * Descripción: Página de verificación de email — procesa el token del enlace enviado al registrarse.
 * ¿Para qué? Capturar el token UUID de la URL (?token=...), llamar al backend y mostrar el resultado.
 * ¿Impacto? Sin esta página, el enlace del email de verificación lleva a un 404 y el usuario
 *           nunca puede activar su cuenta ni iniciar sesión.
 */

import { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { verifyEmail } from "@/api/auth";

// ¿Qué? Estados posibles de la verificación.
// ¿Para qué? Controlar qué se muestra en pantalla según el resultado del proceso.
// ¿Impacto? Permite dar feedback claro al usuario: cargando, éxito o error.
type VerifyStatus = "loading" | "success" | "error";

/**
 * ¿Qué? Página que verifica el email del usuario al visitar el enlace del correo de registro.
 * ¿Para qué? Activar la cuenta del usuario llamando a POST /api/v1/auth/verify-email.
 * ¿Impacto? Tras la verificación exitosa, el usuario puede iniciar sesión normalmente.
 */
export function VerifyEmailPage() {
  // ¿Qué? Hook para leer los query params de la URL (ej: ?token=uuid).
  // ¿Para qué? Extraer el token UUID que viene en el enlace del email de verificación.
  // ¿Impacto? Si no hay token en la URL, mostramos error inmediatamente.
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  // ¿Qué? Estado inicial derivado directamente de la URL, no dentro de un efecto.
  // ¿Para qué? Si no hay token, el resultado ya se conoce en el primer render: no hace falta
  //            renderizar "cargando" para inmediatamente después corregirlo con setState.
  // ¿Impacto? Evita el render en cascada que penaliza React (`react-hooks/set-state-in-effect`)
  //           y elimina el parpadeo del spinner cuando el enlace viene sin token.
  const [status, setStatus] = useState<VerifyStatus>(token ? "loading" : "error");
  const [message, setMessage] = useState<string>(
    token ? "" : "El enlace de verificación no es válido. No se encontró un token.",
  );

  // ¿Qué? Ref para evitar que useEffect llame a la API dos veces en React StrictMode.
  // ¿Para qué? En desarrollo, React monta, desmonta y vuelve a montar los componentes —
  //           sin este ref, el token se usaría dos veces y la segunda llamada fallaría.
  // ¿Impacto? Previene un 400 "token ya usado" inmediatamente después del primer intento exitoso.
  const hasCalled = useRef(false);

  useEffect(() => {
    // ¿Qué? Sin token no hay nada que consultar — el estado de error ya se fijó arriba.
    // ¿Para qué? Evitar una llamada inútil a la API con un token vacío.
    // ¿Impacto? El usuario ve un mensaje claro en lugar de un error genérico del servidor.
    if (!token) return;

    // ¿Qué? Evitar doble ejecución en React StrictMode (desarrollo).
    if (hasCalled.current) return;
    hasCalled.current = true;

    // ¿Qué? Función async para llamar al endpoint de verificación.
    // ¿Para qué? No se pueden usar funciones async directamente en useEffect.
    // ¿Impacto? La verificación es asíncrona — debemos esperar la respuesta del servidor.
    async function verify() {
      try {
        await verifyEmail(token as string);
        setStatus("success");
        setMessage("¡Tu email ha sido verificado exitosamente! Ya puedes iniciar sesión.");
      } catch {
        setStatus("error");
        setMessage(
          "El enlace de verificación no es válido o ya fue utilizado. " +
            "Por favor, solicita un nuevo enlace.",
        );
      }
    }

    verify();
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <div className="w-full max-w-md">
        {/* ¿Qué? Contenedor de la tarjeta de verificación. */}
        {/* ¿Para qué? Centrar el contenido y darle un aspecto limpio y consistente con el resto del app. */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 shadow-sm text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Verificación de email
          </h1>

          {/* ──── Estado: cargando ──── */}
          {status === "loading" && (
            <div className="mt-6">
              {/* ¿Qué? Spinner de carga animado con TailwindCSS. */}
              {/* ¿Para qué? Indicar al usuario que la verificación está en progreso. */}
              <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-accent-600 border-t-transparent" />
              <p className="mt-4 text-gray-600 dark:text-gray-400">Verificando tu email...</p>
            </div>
          )}

          {/* ──── Estado: éxito ──── */}
          {status === "success" && (
            <div className="mt-6">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                {/* ¿Qué? Ícono de check para confirmar éxito visualmente. */}
                <svg
                  className="h-7 w-7 text-green-600 dark:text-green-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="mt-4 text-gray-700 dark:text-gray-300">{message}</p>
              <div className="mt-6 flex justify-end">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-white bg-accent-600 hover:bg-accent-700 dark:bg-accent-500 dark:hover:bg-accent-600 rounded-lg transition-colors"
                >
                  Iniciar sesión
                </Link>
              </div>
            </div>
          )}

          {/* ──── Estado: error ──── */}
          {status === "error" && (
            <div className="mt-6">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
                {/* ¿Qué? Ícono de X para indicar el error visualmente. */}
                <svg
                  className="h-7 w-7 text-red-600 dark:text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <p className="mt-4 text-gray-700 dark:text-gray-300">{message}</p>
              <div className="mt-6 flex justify-end gap-3">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Ir al login
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-accent-600 hover:bg-accent-700 dark:bg-accent-500 dark:hover:bg-accent-600 rounded-lg transition-colors"
                >
                  Crear cuenta
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
