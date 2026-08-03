"use client";

import { useMemo, useState } from "react";
import type { DocumentSummary } from "@/types/document";
import type { DocumentFolder } from "@/types/folder";
import styles from "./AdminDocumentTable.module.css";

interface FolderOption {
  id: string | null;
  label: string;
}

function buildFolderOptions(folders: DocumentFolder[]): FolderOption[] {
  const byId = new Map(folders.map((f) => [f.id, f]));
  function pathOf(folder: DocumentFolder): string {
    const parent = folder.parent_id ? byId.get(folder.parent_id) : undefined;
    return parent ? `${pathOf(parent)} / ${folder.name}` : folder.name;
  }
  return [
    { id: null, label: "Raíz" },
    ...folders
      .map((f) => ({ id: f.id, label: pathOf(f) }))
      .sort((a, b) => a.label.localeCompare(b.label)),
  ];
}

interface AdminDocumentTableProps {
  documents: DocumentSummary[];
  onDelete: (id: string) => void;
  onReprocess: (id: string) => void;
  reprocessingIds?: Set<string>;
  folders?: DocumentFolder[];
  onMove?: (documentId: string, folderId: string | null) => void;
  /** Full corpus to search across when the query is non-empty — lets search
   * reach documents outside the currently open folder instead of being
   * limited to `documents` (the current folder's scope). */
  searchScope?: DocumentSummary[];
}

const STATUS_LABEL: Record<DocumentSummary["status"], string> = {
  processing: "Procesando",
  ready: "Listo",
  error: "Error",
};

const PAGE_SIZE_OPTIONS = [10, 50, 100];
const STUCK_PROCESSING_MS = 10 * 60 * 1000;

function isStuckProcessing(doc: DocumentSummary): boolean {
  if (doc.status !== "processing" || !doc.processing_started_at) return false;
  return Date.now() - new Date(doc.processing_started_at).getTime() > STUCK_PROCESSING_MS;
}

export default function AdminDocumentTable({
  documents,
  onDelete,
  onReprocess,
  reprocessingIds,
  folders = [],
  onMove,
  searchScope,
}: AdminDocumentTableProps) {
  const [query, setQuery] = useState("");
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0]);
  const [page, setPage] = useState(1);
  const folderOptions = useMemo(() => buildFolderOptions(folders), [folders]);

  const trimmedQuery = query.trim().toLowerCase();
  const isSearchingEverywhere = trimmedQuery.length > 0 && !!searchScope;
  const baseList = isSearchingEverywhere ? (searchScope as DocumentSummary[]) : documents;

  const filtered = useMemo(
    () => baseList.filter((doc) => doc.name.toLowerCase().includes(trimmedQuery)),
    [baseList, trimmedQuery]
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const pageItems = filtered.slice(startIndex, startIndex + pageSize);

  function handleSearchChange(value: string) {
    setQuery(value);
    setPage(1);
  }

  function handlePageSizeChange(size: number) {
    setPageSize(size);
    setPage(1);
  }

  const nothingToSearch = documents.length === 0 && !searchScope?.length;

  return (
    <div className={styles.wrapper}>
      <div className={styles.toolbar}>
        <div className={styles.toolbarLeft}>
          <span className={styles.count}>{filtered.length} documentos</span>
          <span className={styles.pageSizeLabel}>Por página:</span>
          <div className={styles.pageSizeOptions}>
            {PAGE_SIZE_OPTIONS.map((size) => (
              <button
                key={size}
                type="button"
                className={`${styles.pageSizeButton} ${size === pageSize ? styles.pageSizeButtonActive : ""}`}
                onClick={() => handlePageSizeChange(size)}
              >
                {size}
              </button>
            ))}
          </div>
        </div>
        <label className={styles.search}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4-4" />
          </svg>
          <input
            type="text"
            placeholder={searchScope ? "Buscar en todas las carpetas…" : "Buscar por nombre…"}
            value={query}
            onChange={(e) => handleSearchChange(e.target.value)}
            aria-label="Buscar documentos por nombre"
          />
        </label>
      </div>

      {isSearchingEverywhere && (
        <p className={styles.searchScopeNote}>Buscando en todo el corpus, no solo en esta carpeta.</p>
      )}

      {nothingToSearch ? (
        <p className={styles.emptyState}>Todavía no hay documentos en el corpus.</p>
      ) : pageItems.length === 0 ? (
        <p className={styles.emptyState}>
          {trimmedQuery ? "No encontramos documentos con ese nombre." : "Esta carpeta no tiene documentos."}
        </p>
      ) : (
        <div className={styles.tableScroll}>
        <table className={styles.table}>
          <colgroup>
            <col />
            <col className={styles.colType} />
            <col className={styles.colStatus} />
            <col className={styles.colChunks} />
            {onMove && <col className={styles.colFolder} />}
            <col className={styles.colActions} />
          </colgroup>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Chunks</th>
              {onMove && <th>Carpeta</th>}
              <th aria-label="Acciones" />
            </tr>
          </thead>
          <tbody>
            {pageItems.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.name}</td>
                <td>{doc.type}</td>
                <td>
                  <span
                    className={`${styles.badge} ${styles[`badge_${doc.status}`]}`}
                    title={doc.status === "error" && doc.error_detail ? doc.error_detail : undefined}
                  >
                    {STATUS_LABEL[doc.status]}
                  </span>
                </td>
                <td>{doc.chunk_count}</td>
                {onMove && (
                  <td>
                    <select
                      className={styles.folderSelect}
                      value={doc.folder_id ?? ""}
                      onChange={(e) => onMove(doc.id, e.target.value || null)}
                      aria-label={`Mover ${doc.name}`}
                    >
                      {folderOptions.map((option) => (
                        <option key={option.id ?? "root"} value={option.id ?? ""}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </td>
                )}
                <td>
                  <div className={styles.actions}>
                    <button
                      type="button"
                      className={styles.reprocessButton}
                      onClick={() => onReprocess(doc.id)}
                      disabled={
                        reprocessingIds?.has(doc.id) ||
                        (doc.status === "processing" && !isStuckProcessing(doc))
                      }
                      title={
                        doc.status === "processing" && isStuckProcessing(doc)
                          ? "Lleva más de 10 minutos procesando"
                          : undefined
                      }
                      aria-label={`Reprocesar ${doc.name}`}
                    >
                      {reprocessingIds?.has(doc.id) && <span className={styles.spinner} aria-hidden="true" />}
                      Reprocesar
                    </button>
                    <button type="button" className={styles.deleteButton} onClick={() => onDelete(doc.id)}>
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}

      {!nothingToSearch && pageItems.length > 0 && (
        <div className={styles.footer}>
          <span className={styles.showing}>
            Mostrando {startIndex + 1}-{startIndex + pageItems.length} de {filtered.length}
          </span>
          <div className={styles.pagination}>
            <button
              type="button"
              className={styles.pageNavButton}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage === 1}
              aria-label="Página anterior"
            >
              ‹
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                type="button"
                className={`${styles.pageButton} ${p === safePage ? styles.pageButtonActive : ""}`}
                onClick={() => setPage(p)}
                aria-current={p === safePage ? "page" : undefined}
              >
                {p}
              </button>
            ))}
            <button
              type="button"
              className={styles.pageNavButton}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage === totalPages}
              aria-label="Página siguiente"
            >
              ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
