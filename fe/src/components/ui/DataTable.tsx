/**
 * Archivo: components/ui/DataTable.tsx
 * Descripción: Componente genérico de tabla de datos con paginación, ordenación,
 *              búsqueda global, estilo cebra y menú de acciones por fila.
 * ¿Para qué? Proveer una tabla reutilizable que pueda mostrar cualquier conjunto de datos
 *            estructurados de forma consistente en toda la aplicación.
 * ¿Impacto? Sin este componente, cada vista que necesite una tabla debería reimplementar
 *           paginación, ordenación y filtros por separado, causando duplicación y errores.
 *           Con este componente, basta con pasar `data` y `columns` para obtener una tabla
 *           completamente funcional.
 */

import {
  useState,
  useMemo,
  useRef,
  useEffect,
  useCallback,
  type ReactNode,
  type RefObject,
  type ChangeEvent,
} from "react";
import jsPDF from "jspdf";
import { autoTable } from "jspdf-autotable";
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Search,
  MoreVertical,
  ChevronLeft,
  ChevronRight,
  FileDown,
} from "lucide-react";

// ============================================================================
// TIPOS E INTERFACES
// ¿Qué? Definen el contrato del componente — qué datos acepta y en qué forma.
// ¿Para qué? TypeScript usa estos tipos para validar que el uso del componente
//            sea correcto en tiempo de compilación, antes de correr el código.
// ¿Impacto? Sin tipos, cualquier error de uso solo se detectaría en runtime.
// ============================================================================

/**
 * ¿Qué? Definición de una columna de la tabla.
 * ¿Para qué? Describir cómo se muestra cada campo del dataset: encabezado,
 *            si es ordenable, y cómo renderizar el valor de la celda.
 * ¿Impacto? Es la pieza central de la parametrización del componente.
 *           Cambiando las columnas, la misma tabla sirve para usuarios, productos, pedidos, etc.
 */
export interface ColumnDef<T> {
  /**
   * Clave del campo en el objeto de datos.
   * Soporta notación de punto para campos anidados: "address.city".
   */
  key: string;

  /** Texto visible en el encabezado de la columna. */
  header: string;

  /**
   * Permite ordenar la tabla por esta columna haciendo clic en el encabezado.
   * Default: false.
   */
  sortable?: boolean;

  /**
   * Ancho personalizado de la columna — puede ser px, %, rem, etc.
   * Ejemplo: "200px", "20%", "12rem".
   */
  width?: string;

  /**
   * ¿Qué? Función de renderizado personalizado para la celda.
   * ¿Para qué? Permite mostrar componentes React en lugar del valor crudo:
   *            badges de estado, imágenes, botones inline, etc.
   * ¿Impacto? Sin esta función, la tabla solo podría mostrar texto plano.
   *
   * @param value - Valor extraído del campo `key` en el objeto de datos.
   * @param row   - Objeto completo de la fila (útil para acceder a otros campos).
   * @param rowIndex - Índice de la fila en el dataset filtrado/ordenado.
   */
  render?: (value: unknown, row: T, rowIndex: number) => ReactNode;
}

/**
 * ¿Qué? Definición de una acción disponible en el menú de tres puntos por fila.
 * ¿Para qué? Permitir que el consumidor del componente defina qué operaciones
 *            se pueden realizar sobre cada fila (editar, eliminar, ver detalles, etc.).
 * ¿Impacto? Desacopla las acciones del componente genérico: cada uso puede
 *           definir sus propias acciones sin modificar DataTable.
 */
export interface RowAction<T> {
  /** Texto visible de la acción en el menú desplegable. */
  label: string;

  /** Ícono opcional que aparece a la izquierda del texto. */
  icon?: ReactNode;

  /**
   * Función que se ejecuta al seleccionar esta acción.
   * Recibe el objeto completo de la fila afectada.
   */
  onClick: (row: T) => void;

  /**
   * Variante visual de la acción:
   * - "default": texto azul/gris neutro (para editar, ver, etc.)
   * - "danger": texto rojo (para eliminar, deshabilitar, etc.)
   * Default: "default".
   */
  variant?: "default" | "danger";

  /**
   * ¿Qué? Función que determina si esta acción está deshabilitada para una fila específica.
   * ¿Para qué? Algunas acciones solo aplican bajo ciertas condiciones.
   *            Ejemplo: no se puede "activar" un usuario que ya está activo.
   * ¿Impacto? Sin esto, habría que filtrar acciones fuera del componente o mostrarlas siempre.
   */
  disabled?: (row: T) => boolean;
}

/**
 * ¿Qué? Props del componente DataTable — incluye la configuración completa.
 * ¿Para qué? Centralizar la configuración en un único objeto tipado.
 * ¿Impacto? TypeScript verifica en compilación que el uso sea correcto.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface DataTableProps<T extends Record<string, any>> {
  /** Array de objetos a mostrar en la tabla. Puede estar vacío. */
  data: T[];

  /** Definición de las columnas a mostrar. */
  columns: ColumnDef<T>[];

  /**
   * Acciones disponibles por cada fila.
   * Si no se provee, la columna de acciones no se muestra.
   */
  actions?: RowAction<T>[];

  /**
   * Cantidad de filas visibles por página.
   * Default: 10.
   */
  pageSize?: number;

  /**
   * Opciones disponibles para cambiar el tamaño de página.
   * Default: [5, 10, 25, 50].
   */
  pageSizeOptions?: number[];

  /**
   * Habilita el campo de búsqueda global sobre todos los campos visibles.
   * Default: true.
   */
  searchable?: boolean;

  /** Texto de placeholder del campo de búsqueda. */
  searchPlaceholder?: string;

  /**
   * Mensaje mostrado cuando no hay datos o no hay resultados para la búsqueda.
   * Default: "No se encontraron resultados."
   */
  emptyMessage?: string;

  /**
   * ¿Qué? Indica que los datos están siendo cargados.
   * ¿Para qué? Mostrar un skeleton de carga en lugar de la tabla vacía.
   * ¿Impacto? Mejora la UX: el usuario sabe que hay datos en camino.
   */
  isLoading?: boolean;

  /**
   * Texto descriptivo de la tabla (accesibilidad — HTML <caption>).
   * Recomendado para lectores de pantalla.
   */
  caption?: string;

  /**
   * ¿Qué? Muestra botones de exportación (CSV y PDF) en la barra superior.
   * ¿Para qué? Permitir al usuario descargar los datos filtrados/ordenados.
   * ¿Impacto? Solo exporta lo que el usuario ve (filtrado + ordenado), no el dataset completo.
   * Default: false.
   */
  exportable?: boolean;

  /**
   * Nombre base del archivo exportado, sin extensión.
   * ¿Para qué? El archivo descargado tendrá este nombre + ".csv" o ".pdf".
   * Default: valor de `caption` si existe, o "tabla".
   */
  exportFilename?: string;
}

// ============================================================================
// FUNCIONES DE EXPORTACIÓN
// ¿Qué? Transforman los datos de la tabla en archivos CSV o PDF descargables.
// ¿Para qué? Permitir que el usuario exporte los datos filtrados/ordenados a su equipo.
// ¿Impacto? Operan sobre `sortedData` (datos filtrados + ordenados, todas las páginas),
//           no sobre `pagedData` — el usuario obtiene todos los registros visibles,
//           no solo los de la página actual.
// ============================================================================

/**
 * Genera y descarga un archivo CSV con las columnas y filas proporcionadas.
 *
 * ¿Qué? Construye una cadena CSV válida y la descarga como archivo en el navegador.
 * ¿Para qué? Dar al usuario una copia de los datos en un formato universal.
 * ¿Impacto? No requiere librería externa — usa la API nativa de Blob + URL del navegador.
 *
 * @param columns  - Definición de columnas (para extraer headers y keys).
 * @param rows     - Filas de datos ya filtradas y ordenadas.
 * @param filename - Nombre del archivo sin extensión.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function exportToCSV<T extends Record<string, any>>(
  columns: ColumnDef<T>[],
  rows: T[],
  filename: string,
): void {
  // ¿Qué? Primera fila del CSV con los nombres de columna.
  // ¿Para qué? El receptor del archivo sabrá qué representa cada columna.
  const headerRow = columns.map((col) => `"${col.header.replace(/"/g, '""')}"`).join(",");

  // ¿Qué? Filas de datos transformadas a strings escapados correctamente.
  // ¿Para qué? El estándar CSV requiere que los valores que contienen comas o comillas
  //            sean envueltos en comillas dobles, con las comillas internas duplicadas.
  const dataRows = rows.map((row) =>
    columns
      .map((col) => {
        const value = getNestedValue(row, col.key);
        const str = valueToString(value);
        // Escapar comillas dobles internas duplicándolas (RFC 4180).
        return `"${str.replace(/"/g, '""')}"`;
      })
      .join(","),
  );

  // ¿Qué? Unir encabezado y filas con saltos de línea.
  const csvContent = [headerRow, ...dataRows].join("\n");

  // ¿Qué? Crear un Blob con el contenido y forzar la descarga via <a href>.
  // ¿Para qué? Esta es la técnica estándar para descargar archivos generados en el cliente.
  // ¿Impacto? No se hace ninguna solicitud al servidor — todo ocurre en el navegador.
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename}.csv`;
  link.click();
  // Liberar la URL del objeto para evitar fugas de memoria.
  URL.revokeObjectURL(url);
}

/**
 * Genera y descarga un archivo PDF con las columnas y filas proporcionadas.
 *
 * ¿Qué? Usa jsPDF + jspdf-autotable para crear un PDF con una tabla formateada.
 * ¿Para qué? Dar al usuario una representación de los datos lista para imprimir.
 * ¿Impacto? Requiere jspdf + jspdf-autotable. El PDF se descarga directamente
 *           en el navegador sin pasar por el servidor.
 *
 * @param columns  - Definición de columnas (para encabezados de tabla).
 * @param rows     - Filas de datos ya filtradas y ordenadas.
 * @param filename - Nombre del archivo sin extensión.
 * @param title    - Título opcional a mostrar en la parte superior del PDF.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function exportToPDF<T extends Record<string, any>>(
  columns: ColumnDef<T>[],
  rows: T[],
  filename: string,
  title?: string,
): void {
  // ¿Qué? Crear instancia de jsPDF en modo horizontal si hay muchas columnas.
  // ¿Para qué? Evitar que columnas se corten si son más de 5-6.
  const orientation = columns.length > 6 ? "landscape" : "portrait";
  const doc = new jsPDF({ orientation });

  // ¿Qué? Agregar un título en la parte superior si se proporcionó `caption`.
  // ¿Para qué? El PDF debe ser auto-descriptivo al abrirse o imprimirse.
  if (title) {
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text(title, 14, 16);
  }

  // ¿Qué? Construir los encabezados y cuerpo de la tabla para autoTable.
  // ¿Para qué? autoTable espera arrays de strings para head y body.
  const tableHead = [columns.map((col) => col.header)];
  const tableBody = rows.map((row) =>
    columns.map((col) => {
      const value = getNestedValue(row, col.key);
      return valueToString(value);
    }),
  );

  // ¿Qué? Llamar a autoTable para renderizar la tabla en el documento PDF.
  // ¿Para qué? autoTable maneja automáticamente el layout, paginación y estilos de la tabla.
  // ¿Impacto? Sin autoTable, dibujar una tabla en jsPDF requeriría cálculos manuales complejos.
  autoTable(doc, {
    head: tableHead,
    body: tableBody,
    startY: title ? 22 : 10,
    headStyles: { fillColor: [59, 130, 246] }, // Azul-500 de Tailwind
    alternateRowStyles: { fillColor: [249, 250, 251] }, // Gray-50 de Tailwind
    styles: { fontSize: 9, cellPadding: 3 },
    margin: { left: 14, right: 14 },
  });

  // ¿Qué? Guardar el PDF con el nombre de archivo provisto.
  doc.save(`${filename}.pdf`);
}

// ============================================================================
// FUNCIÓN AUXILIAR: getNestedValue
// ¿Qué? Extrae el valor de un campo en un objeto usando notación de punto.
// ¿Para qué? Permite acceder a campos anidados como "address.city" en la definición
//            de columnas sin que el consumidor deba aplanar sus datos.
// ¿Impacto? Sin esto, solo se podrían usar claves de primer nivel (planas).
// ============================================================================

/**
 * Extrae un valor de un objeto usando notación de punto.
 *
 * @param obj  - Objeto del que extraer el valor.
 * @param path - Ruta de la clave. Ej: "address.city", "name", "meta.tags.0".
 * @returns El valor encontrado, o undefined si la ruta no existe.
 *
 * @example
 * getNestedValue({ user: { name: "Ana" } }, "user.name") // → "Ana"
 * getNestedValue({ age: 25 }, "age")                     // → 25
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getNestedValue(obj: Record<string, any>, path: string): unknown {
  // ¿Qué? Divide la ruta por puntos y recorre el objeto nivel a nivel.
  // ¿Para qué? Soportar objetos anidados sin necesidad de lógica especial en columnas.
  // ¿Impacto? Si path="address.city", accede a obj["address"]["city"] paso a paso.
  return path.split(".").reduce((current, key) => {
    // Si en algún nivel el valor es null/undefined, devolver undefined de inmediato.
    if (current == null) return undefined;
    return (current as Record<string, unknown>)[key];
  }, obj as unknown);
}

// ============================================================================
// FUNCIÓN AUXILIAR: valueToString
// ¿Qué? Convierte cualquier valor a string para comparaciones de búsqueda.
// ¿Para qué? La búsqueda globla compara texto, no valores tipados.
// ¿Impacto? Sin esto, buscar "42" no encontraría filas con el número 42.
// ============================================================================

function valueToString(value: unknown): string {
  if (value == null) return "";
  // ¿Qué? Para objetos y arrays, serializar a JSON para evitar "[object Object]".
  if (typeof value === "object") {
    try {
      return JSON.stringify(value).toLowerCase();
    } catch {
      return "";
    }
  }
  return String(value as string | number | boolean | bigint).toLowerCase();
}

// ============================================================================
// HOOK PERSONALIZADO: useClickOutside
// ¿Qué? Detecta clics fuera de un elemento referenciado.
// ¿Para qué? Cerrar el menú desplegable de acciones cuando el usuario hace
//            clic en cualquier otro lugar de la página.
// ¿Impacto? Sin esto, el menú quedaría abierto hasta que el usuario haga
//            clic en otra acción, degradando la experiencia de uso.
// ============================================================================

function useClickOutside(ref: RefObject<HTMLElement | null>, callback: () => void): void {
  useEffect(() => {
    // ¿Qué? Manejador de eventos que verifica si el clic fue fuera del ref.
    // ¿Para qué? Solo cerrar el menú si el clic no fue dentro de él.
    function handleClick(event: MouseEvent): void {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    }

    // ¿Qué? Se registra en la fase de captura (true) para detectar antes que otros handlers.
    // ¿Para qué? Asegurar que el menú se cierre incluso si el clic abre otro menú.
    document.addEventListener("mousedown", handleClick, true);

    // ¿Qué? Cleanup — se elimina el listener cuando el componente se desmonta.
    // ¿Para qué? Evitar memory leaks y listeners huérfanos.
    // ¿Impacto? Sin cleanup, handlers se acumularían en cada re-render.
    return () => document.removeEventListener("mousedown", handleClick, true);
  }, [ref, callback]);
}

// ============================================================================
// SUBCOMPONENTE: SortIcon
// ¿Qué? Ícono indicador del estado de ordenación en una columna.
// ¿Para qué? Comunicar visualmente si la columna está sin ordenar, ordenada
//            ascendente o descendente.
// ¿Impacto? Sin indicador visual, el usuario no sabría por qué columna está
//            ordenada la tabla ni en qué dirección.
// ============================================================================

interface SortIconProps {
  /** Estado actual: sin ordenar, ascendente o descendente. */
  direction: "none" | "asc" | "desc";
}

function SortIcon({ direction }: Readonly<SortIconProps>) {
  const baseClass = "h-4 w-4 flex-shrink-0";

  if (direction === "asc") {
    return (
      <ChevronUp
        className={`${baseClass} text-accent-600 dark:text-accent-400`}
        aria-hidden="true"
      />
    );
  }
  if (direction === "desc") {
    return (
      <ChevronDown
        className={`${baseClass} text-accent-600 dark:text-accent-400`}
        aria-hidden="true"
      />
    );
  }
  return (
    <ChevronsUpDown
      className={`${baseClass} text-gray-400 dark:text-gray-500`}
      aria-hidden="true"
    />
  );
}

// ============================================================================
// SUBCOMPONENTE: ActionsMenu
// ¿Qué? Menú desplegable de tres puntos con las acciones disponibles por fila.
// ¿Para qué? Agrupar múltiples acciones en un lugar compacto sin saturar la UI.
// ¿Impacto? Sin este menú, habría que mostrar un botón por acción en cada fila,
//            ocupando espacio y haciendo la tabla difícil de leer.
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface ActionsMenuProps<T extends Record<string, any>> {
  row: T;
  actions: RowAction<T>[];
  rowId: string;
  openMenuId: string | null;
  onToggle: (id: string | null) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ActionsMenu<T extends Record<string, any>>({
  row,
  actions,
  rowId,
  openMenuId,
  onToggle,
}: Readonly<ActionsMenuProps<T>>) {
  const menuRef = useRef<HTMLDivElement>(null);
  const isOpen = openMenuId === rowId;

  useClickOutside(
    menuRef,
    useCallback(() => {
      if (isOpen) onToggle(null);
    }, [isOpen, onToggle]),
  );

  return (
    <div ref={menuRef} className="relative flex justify-center">
      {/* ── Botón de tres puntos ── */}
      <button
        onClick={() => onToggle(isOpen ? null : rowId)}
        className={`rounded-md p-1.5 transition-colors duration-150
          text-gray-500 hover:text-gray-700 hover:bg-gray-100
          dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700
          focus:outline-none focus:ring-2 focus:ring-accent-500/40
          ${isOpen ? "bg-gray-100 dark:bg-gray-700" : ""}`}
        aria-label="Abrir menú de acciones"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <MoreVertical className="h-4 w-4" aria-hidden="true" />
      </button>

      {/* ── Menú desplegable ──
          ¿Qué? Panel con z-index alto para aparecer sobre las filas vecinas.
          ¿Para qué? Evitar que el menú quede oculto detrás de otros elementos.
          ¿Impacto? Sin z-50 el menú aparecería detrás de otras filas.
      */}
      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-1 min-w-40 overflow-hidden
            rounded-lg border border-gray-200 bg-white shadow-lg
            dark:border-gray-700 dark:bg-gray-800"
        >
          {actions.map((action) => {
            const isDisabled = action.disabled ? action.disabled(row) : false;

            // ¿Qué? Extraer la clase de color fuera del JSX para evitar ternarios anidados.
            let colorClass: string;
            if (isDisabled) {
              colorClass = "text-gray-300 dark:text-gray-600 cursor-not-allowed";
            } else if (action.variant === "danger") {
              colorClass =
                "text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20";
            } else {
              colorClass =
                "text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700";
            }

            return (
              <button
                key={action.label}
                role="menuitem"
                disabled={isDisabled}
                onClick={() => {
                  onToggle(null);
                  action.onClick(row);
                }}
                className={`flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm
                  transition-colors duration-150 ${colorClass}`}
              >
                {action.icon && (
                  <span className="shrink-0" aria-hidden="true">
                    {action.icon}
                  </span>
                )}
                {action.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// SUBCOMPONENTE: SkeletonRows
// ¿Qué? Filas de esqueleto animadas para el estado de carga.
// ¿Para qué? Comunicar al usuario que los datos están siendo cargados,
//            sin mostrar una tabla vacía ni un spinner genérico.
// ¿Impacto? Mejora la percepción de rendimiento (perceived performance).
// ============================================================================

interface SkeletonRowsProps {
  /** Número de filas de skeleton a mostrar. */
  rows: number;
  /** Número de columnas (incluyendo acciones si las hay). */
  cols: number;
}

function SkeletonRows({ rows, cols }: Readonly<SkeletonRowsProps>) {
  return (
    <>
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <tr key={`sk-row-${rowIdx}`} className="border-b border-gray-100 dark:border-gray-700">
          {Array.from({ length: cols }).map((_, colIdx) => (
            <td key={`sk-col-${rowIdx}-${colIdx}`} className="px-4 py-3">
              {/* Barra animada que simula el texto de la celda */}
              <div
                className="h-4 animate-pulse rounded bg-gray-200 dark:bg-gray-700"
                style={{ width: `${60 + ((rowIdx * 7 + colIdx * 13) % 30)}%` }}
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// ============================================================================
// COMPONENTE PRINCIPAL: DataTable
// ¿Qué? Tabla de datos genérica y completamente parametrizable.
// ¿Para qué? Centralizar la lógica de presentación de datos tabulares:
//            paginación, ordenación, búsqueda y acciones.
// ¿Impacto? Único punto de mantenimiento para toda la lógica de tabla.
//            Un bug corregido aquí se corrige en toda la aplicación.
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  actions,
  pageSize: initialPageSize = 10,
  pageSizeOptions = [5, 10, 25, 50],
  searchable = true,
  searchPlaceholder = "Buscar...",
  emptyMessage = "No se encontraron resultados.",
  isLoading = false,
  caption,
  exportable = false,
  exportFilename,
}: Readonly<DataTableProps<T>>) {
  // ──────────────────────────────────────────────────────────────────────────
  // ESTADO DEL COMPONENTE
  // ¿Qué? Variables de estado que controlan el comportamiento dinámico de la tabla.
  // ¿Para qué? React re-renderiza el componente cada vez que cambia un estado,
  //            actualizando la UI automáticamente.
  // ¿Impacto? Sin estado, la tabla sería estática — no podría paginar ni ordenar.
  // ──────────────────────────────────────────────────────────────────────────

  /** Texto ingresado en el campo de búsqueda global. */
  const [searchQuery, setSearchQuery] = useState("");

  /** Clave de la columna por la que se está ordenando actualmente. Null = sin orden activo. */
  const [sortKey, setSortKey] = useState<string | null>(null);

  /**
   * Dirección de la ordenación actual.
   * "asc"  = menor a mayor (A → Z, 0 → 9).
   * "desc" = mayor a menor (Z → A, 9 → 0).
   */
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  /** Página actual (base 1 para ser legible en la UI). */
  const [currentPage, setCurrentPage] = useState(1);

  /** Cantidad de filas visibles por página. */
  const [rowsPerPage, setRowsPerPage] = useState(initialPageSize);

  /**
   * ID del menú de acciones actualmente abierto.
   * Se genera como `row-{index}`. Null = ningún menú abierto.
   */
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  // ──────────────────────────────────────────────────────────────────────────
  // DATOS FILTRADOS (useMemo)
  // ¿Qué? Derivación del array de datos filtrado por el término de búsqueda.
  // ¿Para qué? useMemo memoriza el resultado — solo recalcula si cambian
  //            `data` o `searchQuery`, no en cada render.
  // ¿Impacto? Sin memoización, el filtro correría en cada keystroke Y en
  //            cada re-render por otras razones, degradando el rendimiento.
  // ──────────────────────────────────────────────────────────────────────────
  const filteredData = useMemo(() => {
    // Si no hay búsqueda activa, devolver todos los datos sin procesar.
    if (!searchQuery.trim()) return data;

    const query = searchQuery.toLowerCase().trim();

    // ¿Qué? Filtrar filas donde AL MENOS UN campo visible contenga el término.
    // ¿Para qué? Búsqueda global — el usuario no necesita saber en qué columna está el dato.
    return data.filter((row) =>
      columns.some((col) => {
        const value = getNestedValue(row, col.key);
        return valueToString(value).includes(query);
      }),
    );
  }, [data, searchQuery, columns]);

  // ──────────────────────────────────────────────────────────────────────────
  // DATOS ORDENADOS (useMemo)
  // ¿Qué? Derivación del array filtrado con ordenación aplicada.
  // ¿Para qué? Separar filtrado de ordenación facilita el razonamiento
  //            y permite que cada transformación sea independiente.
  // ¿Impacto? La ordenación opera sobre los datos ya filtrados, no sobre
  //           el dataset completo — coherente con lo que el usuario ve.
  // ──────────────────────────────────────────────────────────────────────────
  const sortedData = useMemo(() => {
    // Si no hay columna de orden activa, devolver los datos filtrados tal cual.
    if (!sortKey) return filteredData;

    // ¿Qué? Crear una copia antes de ordenar — sort() muta el array original.
    // ¿Para qué? Evitar efectos secundarios en el array filtrado memoizado.
    return [...filteredData].sort((a, b) => {
      const aValue = getNestedValue(a, sortKey);
      const bValue = getNestedValue(b, sortKey);

      // ¿Qué? Manejar valores nulos — siempre van al final independientemente del orden.
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // ¿Qué? Comparación numérica si ambos valores son números.
      // ¿Para qué? Evitar que "10" ordene antes que "9" (comparación de strings).
      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
      }

      // ¿Qué? Comparación de strings usando localeCompare para respetar acentos.
      // ¿Para qué? "ángel" debe ordenar antes que "beto", no después de "zebra".
      const aStr = valueToString(aValue);
      const bStr = valueToString(bValue);
      const comparison = aStr.localeCompare(bStr);

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredData, sortKey, sortDirection]);

  // ──────────────────────────────────────────────────────────────────────────
  // PAGINACIÓN (useMemo + derivados)
  // ¿Qué? Cálculo de las filas visibles en la página actual.
  // ¿Para qué? No renderizar todos los datos de golpe — solo la "ventana" visible.
  // ¿Impacto? Con 10.000 filas, renderizar el DOM completo sería muy lento.
  //           La paginación mantiene el DOM ligero mostrando solo lo necesario.
  // ──────────────────────────────────────────────────────────────────────────

  /** Total de páginas calculado en base a los datos filtrados y el tamaño de página. */
  const totalPages = Math.max(1, Math.ceil(sortedData.length / rowsPerPage));

  /**
   * ¿Qué? Ajuste reactivo de la página actual cuando los filtros reducen el total.
   * ¿Para qué? Evitar que `currentPage` quede en una página que ya no existe.
   *            Ejemplo: estaba en página 5, el filtro reduce a 3 páginas → ir a 3.
   */
  const safePage = Math.min(currentPage, totalPages);

  /** Slice de datos visibles: solo las filas de la página actual. */
  const pagedData = useMemo(() => {
    const start = (safePage - 1) * rowsPerPage;
    return sortedData.slice(start, start + rowsPerPage);
  }, [sortedData, safePage, rowsPerPage]);

  // ──────────────────────────────────────────────────────────────────────────
  // MANEJADORES DE EVENTOS
  // ¿Qué? Funciones que responden a interacciones del usuario.
  // ¿Para qué? Separar la lógica de los eventos del JSX para mayor legibilidad.
  // ──────────────────────────────────────────────────────────────────────────

  /**
   * ¿Qué? Maneja el clic en el encabezado de una columna ordenable.
   * ¿Para qué? Activar la ordenación o invertir la dirección si ya está activa.
   * ¿Impacto? Implementa el ciclo: sin orden → asc → desc → asc → desc…
   */
  const handleSort = useCallback(
    (key: string) => {
      if (sortKey === key) {
        // ¿Qué? Si se hace clic en la misma columna, invertir la dirección.
        setSortDirection((prev: "asc" | "desc") => (prev === "asc" ? "desc" : "asc"));
      } else {
        // ¿Qué? Si es una columna diferente, ordenar ascendente por defecto.
        setSortKey(key);
        setSortDirection("asc");
      }
      // ¿Qué? Al cambiar el orden, volver a la primera página.
      // ¿Para qué? El usuario debería ver los primeros resultados del nuevo orden.
      setCurrentPage(1);
    },
    [sortKey],
  );

  /**
   * ¿Qué? Maneja cambios en el campo de búsqueda.
   * ¿Para qué? Actualizar `searchQuery` y resetear a página 1.
   * ¿Impacto? Sin resetear la página, el usuario podría quedarse en página 5
   *           de una búsqueda que solo tiene 1 página de resultados.
   */
  const handleSearch = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  }, []);

  /**
   * ¿Qué? Maneja el cambio de tamaño de página en el selector.
   * ¿Para qué? Actualizar `rowsPerPage` y resetear a la primera página.
   */
  const handlePageSizeChange = useCallback((e: ChangeEvent<HTMLSelectElement>) => {
    setRowsPerPage(Number(e.target.value));
    setCurrentPage(1);
  }, []);

  // ──────────────────────────────────────────────────────────────────────────
  // NÚMEROS DE PÁGINA (useMemo)
  // ¿Qué? Genera el array de páginas visibles con elipsis para tablas largas.
  // ¿Para qué? Mostrar solo un subconjunto de páginas evita que el paginador
  //            desborde con 100+ páginas: [1] [...] [4] [5] [6] [...] [100]
  // ¿Impacto? Sin esto, un paginador con 50 páginas sería inutilizable.
  // ──────────────────────────────────────────────────────────────────────────
  const pageNumbers = useMemo(() => {
    const pages: (number | "ellipsis")[] = [];

    if (totalPages <= 7) {
      // ¿Qué? Con 7 o menos páginas, mostrar todas sin elipsis.
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }

    // ¿Qué? Siempre incluir la primera y última página.
    pages.push(1);

    // ¿Qué? Determinar el rango de páginas "cercanas" a la página actual.
    const start = Math.max(2, safePage - 1);
    const end = Math.min(totalPages - 1, safePage + 1);

    // Elipsis izquierda — si hay un hueco entre 1 y el inicio del rango.
    if (start > 2) pages.push("ellipsis");

    for (let i = start; i <= end; i++) pages.push(i);

    // Elipsis derecha — si hay un hueco entre el fin del rango y la última página.
    if (end < totalPages - 1) pages.push("ellipsis");

    pages.push(totalPages);
    return pages;
  }, [totalPages, safePage]);

  // ──────────────────────────────────────────────────────────────────────────
  // NÚMERO TOTAL DE COLUMNAS (para colSpan y skeleton)
  // ¿Qué? Suma columnas de datos + columna de acciones (si existe).
  // ──────────────────────────────────────────────────────────────────────────
  const totalCols = columns.length + (actions && actions.length > 0 ? 1 : 0);

  // ──────────────────────────────────────────────────────────────────────────
  // INFORMACIÓN DE RANGO VISIBLE
  // ¿Qué? Texto descriptivo del rango de filas mostradas (ej: "11 - 20 de 45").
  // ¿Para qué? Dar contexto al usuario sobre cuántos datos hay y cuántos ve ahora.
  // ──────────────────────────────────────────────────────────────────────────
  const rangeStart = sortedData.length === 0 ? 0 : (safePage - 1) * rowsPerPage + 1;
  const rangeEnd = Math.min(safePage * rowsPerPage, sortedData.length);

  // ──────────────────────────────────────────────────────────────────────────
  // NOMBRE DE ARCHIVO PARA EXPORTACIÓN
  // ¿Qué? Nombre base del archivo descargado, sin extensión.
  // ¿Para qué? Usar la prop `exportFilename` si se provee; si no, el `caption`
  //            limpio de espacios; si tampoco, el fallback "tabla".
  // ──────────────────────────────────────────────────────────────────────────
  const effectiveFilename =
    exportFilename ?? (caption != null ? caption.trim().replace(/\s+/g, "_") : "tabla");

  // ──────────────────────────────────────────────────────────────────────────
  // MANEJADORES DE EXPORTACIÓN
  // ¿Qué? Callbacks que invocan las funciones de exportación con los datos actuales.
  // ¿Para qué? Memoizar con useCallback evita regenerar funciones en cada render.
  // ¿Impacto? Exportan `sortedData` (filtrado + ordenado, TODAS las páginas),
  //           no solo la página visible — el usuario obtiene el conjunto completo.
  // ──────────────────────────────────────────────────────────────────────────
  const handleExportCSV = useCallback(() => {
    exportToCSV(columns, sortedData, effectiveFilename);
  }, [columns, sortedData, effectiveFilename]);

  const handleExportPDF = useCallback(() => {
    exportToPDF(columns, sortedData, effectiveFilename, caption);
  }, [columns, sortedData, effectiveFilename, caption]);

  // ══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ¿Qué? JSX que describe la estructura visual del componente.
  // ¿Para qué? React usa este JSX para construir/actualizar el DOM real.
  // ¿Impacto? Es lo que el usuario ve — cada cambio de estado re-ejecuta esta
  //           función y React actualiza solo las partes que cambiaron (Virtual DOM).
  // ══════════════════════════════════════════════════════════════════════════
  return (
    // ¿Qué? Contenedor principal con borde y sombra sutil.
    // ¿Para qué? Delimitar visualmente el componente del resto de la página.
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
      {/* ────────────────────────────────────────────────────────────────────
          BARRA SUPERIOR: búsqueda + selector de tamaño de página
          ¿Qué? Controles que modifican qué datos se muestran y cuántos.
          ¿Para qué? Agrupar los controles de tabla en la parte superior,
                     siguiendo patrones UX estándar de datatables.
      ──────────────────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 border-b border-gray-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-gray-700">
        {/* ── Campo de búsqueda global ── */}
        {searchable && (
          <div className="relative w-full sm:max-w-xs">
            {/* Ícono de lupa decorativo, no interactivo */}
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-gray-500"
              aria-hidden="true"
            />
            <input
              type="search"
              value={searchQuery}
              onChange={handleSearch}
              placeholder={searchPlaceholder}
              className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-9 pr-3 text-sm
                placeholder:text-gray-400 transition-colors duration-200
                focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20
                dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100
                dark:placeholder:text-gray-500 dark:focus:border-accent-400 dark:focus:ring-accent-400/20"
              aria-label="Buscar en la tabla"
            />
          </div>
        )}

        {/* ── Selector de filas por página + botones de exportación ── */}
        <div className="flex flex-wrap items-center justify-end gap-3">
          {/* Selector de filas por página */}
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <label htmlFor="dt-page-size" className="whitespace-nowrap">
              Filas por página:
            </label>
            <select
              id="dt-page-size"
              value={rowsPerPage}
              onChange={handlePageSizeChange}
              className="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-sm
                transition-colors duration-200 focus:border-accent-500 focus:outline-none
                focus:ring-2 focus:ring-accent-500/20
                dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100
                dark:focus:border-accent-400 dark:focus:ring-accent-400/20"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>

          {/*
            Botones de exportación CSV y PDF.
            ¿Qué? Solo visibles cuando `exportable={true}`.
            ¿Para qué? No ocupar espacio visual cuando la exportación no es necesaria.
            ¿Impacto? Exportan los datos filtrados y ordenados de TODAS las páginas.
          */}
          {exportable && (
            <div className="flex items-center gap-1">
              {/* Botón exportar CSV */}
              <button
                type="button"
                onClick={handleExportCSV}
                aria-label="Exportar a CSV"
                title="Exportar a CSV"
                className="flex items-center gap-1.5 rounded-lg border border-gray-300
                  bg-white px-3 py-1.5 text-xs font-medium text-gray-700
                  transition-colors duration-200 hover:bg-gray-50 hover:border-gray-400
                  focus:outline-none focus:ring-2 focus:ring-accent-500/20
                  dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300
                  dark:hover:bg-gray-700 dark:hover:border-gray-500"
              >
                <FileDown className="h-3.5 w-3.5" aria-hidden="true" />
                CSV
              </button>

              {/* Botón exportar PDF */}
              <button
                type="button"
                onClick={handleExportPDF}
                aria-label="Exportar a PDF"
                title="Exportar a PDF"
                className="flex items-center gap-1.5 rounded-lg border border-gray-300
                  bg-white px-3 py-1.5 text-xs font-medium text-gray-700
                  transition-colors duration-200 hover:bg-gray-50 hover:border-gray-400
                  focus:outline-none focus:ring-2 focus:ring-accent-500/20
                  dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300
                  dark:hover:bg-gray-700 dark:hover:border-gray-500"
              >
                <FileDown className="h-3.5 w-3.5" aria-hidden="true" />
                PDF
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────────────
          TABLA PRINCIPAL
          ¿Qué? Elemento <table> HTML semántico con encabezados y filas de datos.
          ¿Para qué? Usar <table> real (no divs) garantiza accesibilidad:
                     lectores de pantalla pueden navegar por celdas/columnas.
          ¿Impacto? Tablas hechas con divs son invisibles para tecnologías asistivas.
      ──────────────────────────────────────────────────────────────────── */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          {/* Caption accesible — visible solo para lectores de pantalla si no se quiere mostrar */}
          {caption && (
            <caption className="px-4 py-2 text-left text-base font-semibold text-gray-800 dark:text-gray-200">
              {caption}
            </caption>
          )}

          {/* ── Encabezados de columna ── */}
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
              {columns.map((col) => {
                // ¿Qué? Calcular aria-sort fuera del JSX para evitar ternarios anidados.
                // ¿Para qué? Cumplir las reglas del linter y mejorar legibilidad.
                let ariaSortValue: "ascending" | "descending" | "none" | undefined;
                if (sortKey === col.key) {
                  ariaSortValue = sortDirection === "asc" ? "ascending" : "descending";
                } else if (col.sortable) {
                  ariaSortValue = "none";
                }

                return (
                  <th
                    key={col.key}
                    scope="col"
                    style={col.width ? { width: col.width } : undefined}
                    className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider
                      text-gray-600 dark:text-gray-400
                      ${col.sortable ? "cursor-pointer select-none hover:bg-gray-100 dark:hover:bg-gray-700" : ""}`}
                    onClick={col.sortable ? () => handleSort(col.key) : undefined}
                    aria-sort={ariaSortValue}
                  >
                    <div className="flex items-center gap-1">
                      <span>{col.header}</span>
                      {col.sortable && (
                        <SortIcon direction={sortKey === col.key ? sortDirection : "none"} />
                      )}
                    </div>
                  </th>
                );
              })}

              {/* ── Columna de acciones (solo si se configuraron acciones) ── */}
              {actions && actions.length > 0 && (
                <th
                  scope="col"
                  className="w-16 px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-400"
                >
                  <span className="sr-only">Acciones</span>
                </th>
              )}
            </tr>
          </thead>

          {/* ── Cuerpo de la tabla ── */}
          <tbody>
            {/* ── Estado: cargando ── */}
            {isLoading && <SkeletonRows rows={rowsPerPage} cols={totalCols} />}

            {/* ── Estado: sin resultados ── */}
            {!isLoading && pagedData.length === 0 && (
              <tr>
                <td
                  colSpan={totalCols}
                  className="px-4 py-12 text-center text-sm text-gray-500 dark:text-gray-400"
                >
                  {/* Ícono decorativo de tabla vacía */}
                  <div className="flex flex-col items-center gap-2">
                    <svg
                      className="h-10 w-10 text-gray-300 dark:text-gray-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"
                      />
                    </svg>
                    <span>{emptyMessage}</span>
                  </div>
                </td>
              </tr>
            )}

            {/* ── Filas de datos ──
                ¿Qué? Cada fila corresponde a un elemento del array `pagedData`.
                ¿Para qué? Renderizar exactamente las filas de la página visible.
                ¿Impacto? La clase condicional `even:bg-gray-50` implementa el
                           estilo cebra — filas pares con fondo ligeramente distinto.
            */}
            {!isLoading &&
              pagedData.map((row, rowIndex) => {
                const rowId = `row-${(safePage - 1) * rowsPerPage + rowIndex}`;

                // ¿Qué? Calcular la clase de fondo de la fila fuera del JSX.
                // ¿Para qué? Implementar el estilo cebra sin ternario anidado en className.
                // ¿Impacto? Filas alternadas facilitan al usuario seguir una fila horizontalmente.
                const rowBgClass =
                  rowIndex % 2 === 1
                    ? "bg-gray-50/60 dark:bg-gray-800/40"
                    : "bg-white dark:bg-gray-900";

                return (
                  <tr
                    key={rowId}
                    className={`border-b border-gray-100 transition-colors duration-100
                      last:border-b-0 dark:border-gray-700/50
                      ${rowBgClass}
                      hover:bg-accent-50/40 dark:hover:bg-accent-900/10`}
                  >
                    {/* ── Celdas de datos ── */}
                    {columns.map((col) => {
                      const rawValue = getNestedValue(row, col.key);

                      // ¿Qué? Determinar el contenido de la celda fuera del JSX.
                      // ¿Para qué? Evitar ternarios anidados en el markup.
                      let cellContent: ReactNode;
                      if (col.render) {
                        cellContent = col.render(rawValue, row, rowIndex);
                      } else if (rawValue == null) {
                        cellContent = "—";
                      } else if (typeof rawValue === "object") {
                        cellContent = JSON.stringify(rawValue);
                      } else {
                        cellContent = String(rawValue as string | number | boolean | bigint);
                      }

                      return (
                        <td key={col.key} className="px-4 py-3 text-gray-800 dark:text-gray-200">
                          {cellContent}
                        </td>
                      );
                    })}

                    {/* ── Celda de acciones ── */}
                    {actions && actions.length > 0 && (
                      <td className="px-4 py-3">
                        <ActionsMenu
                          row={row}
                          actions={actions}
                          rowId={rowId}
                          openMenuId={openMenuId}
                          onToggle={setOpenMenuId}
                        />
                      </td>
                    )}
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {/* ────────────────────────────────────────────────────────────────────
          BARRA INFERIOR: información de rango + paginación
          ¿Qué? Pie de la tabla con controles de navegación entre páginas.
          ¿Para qué? Permitir al usuario moverse entre páginas y saber cuántos
                     registros hay en total.
      ──────────────────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 border-t border-gray-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-gray-700">
        {/* ── Información de rango ── */}
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {sortedData.length === 0 ? (
            "Sin resultados"
          ) : (
            <>
              Mostrando{" "}
              <span className="font-medium text-gray-900 dark:text-gray-100">{rangeStart}</span> –{" "}
              <span className="font-medium text-gray-900 dark:text-gray-100">{rangeEnd}</span> de{" "}
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {sortedData.length}
              </span>{" "}
              {sortedData.length !== data.length && (
                <span className="text-gray-500 dark:text-gray-500">
                  (filtrado de {data.length} total)
                </span>
              )}
            </>
          )}
        </p>

        {/* ── Controles de paginación ── */}
        {totalPages > 1 && (
          <nav aria-label="Navegación de páginas" className="flex items-center gap-1">
            {/* Botón "Página anterior" */}
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={safePage === 1}
              aria-label="Página anterior"
              className="flex items-center justify-center rounded-lg border border-gray-300 p-1.5
                text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed
                disabled:opacity-40 dark:border-gray-600 dark:text-gray-400
                dark:hover:bg-gray-700"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </button>

            {/* Números de página con elipsis */}
            {pageNumbers.map((page, idx) => {
              if (page === "ellipsis") {
                // ¿Qué? La key identifica este ellipsis usando el índice dentro del array.
                // ¿Para qué? Los ellipsis no tienen un valor propio — se usa el siguiente
                //            número de página para crear una key estable sin duplicados.
                // ¿Impacto? Evita warns de React por keys duplicadas cuando hay 2 ellipsis.
                const nextPage = pageNumbers[idx + 1];
                const ellipsisKey = `ellipsis-before-${typeof nextPage === "number" ? nextPage : idx}`;
                return (
                  <span
                    key={ellipsisKey}
                    className="px-2 text-sm text-gray-400 dark:text-gray-500"
                    aria-hidden="true"
                  >
                    …
                  </span>
                );
              }

              // ¿Qué? Calcular la clase del botón antes del JSX para evitar ternarios anidados.
              const isActivePage = page === safePage;
              const pageButtonClass = isActivePage
                ? "border-accent-600 bg-accent-600 text-white dark:border-accent-500 dark:bg-accent-500"
                : "border-gray-300 text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700";

              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  aria-label={`Ir a página ${page}`}
                  aria-current={isActivePage ? "page" : undefined}
                  className={`flex h-8 min-w-8 items-center justify-center rounded-lg
                    border px-2 text-sm font-medium transition-colors duration-150
                    ${pageButtonClass}`}
                >
                  {page}
                </button>
              );
            })}

            {/* Botón "Página siguiente" */}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage === totalPages}
              aria-label="Página siguiente"
              className="flex items-center justify-center rounded-lg border border-gray-300 p-1.5
                text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed
                disabled:opacity-40 dark:border-gray-600 dark:text-gray-400
                dark:hover:bg-gray-700"
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </nav>
        )}
      </div>
    </div>
  );
}
