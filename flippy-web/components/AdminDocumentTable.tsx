"use client";

import { useMemo, useState } from "react";
import type { DocumentSummary } from "@/types/document";
import styles from "./AdminDocumentTable.module.css";

interface AdminDocumentTableProps {
  documents: DocumentSummary[];
  onDelete: (id: string) => void;
}

const STATUS_LABEL: Record<DocumentSummary["status"], string> = {
  processing: "Procesando",
  ready: "Listo",
  error: "Error",
};

const PAGE_SIZE_OPTIONS = [10, 50, 100];

export default function AdminDocumentTable({ documents, onDelete }: AdminDocumentTableProps) {
  const [query, setQuery] = useState("");
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0]);
  const [page, setPage] = useState(1);

  const filtered = useMemo(
    () => documents.filter((doc) => doc.name.toLowerCase().includes(query.trim().toLowerCase())),
    [documents, query]
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

  if (documents.length === 0) {
    return <p className={styles.emptyState}>Todavía no hay documentos en el corpus.</p>;
  }

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
            placeholder="Buscar por nombre…"
            value={query}
            onChange={(e) => handleSearchChange(e.target.value)}
            aria-label="Buscar documentos por nombre"
          />
        </label>
      </div>

      {pageItems.length === 0 ? (
        <p className={styles.emptyState}>No encontramos documentos con ese nombre.</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Chunks</th>
              <th aria-label="Acciones" />
            </tr>
          </thead>
          <tbody>
            {pageItems.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.name}</td>
                <td>{doc.type}</td>
                <td>
                  <span className={`${styles.badge} ${styles[`badge_${doc.status}`]}`}>
                    {STATUS_LABEL[doc.status]}
                  </span>
                </td>
                <td>{doc.chunk_count}</td>
                <td>
                  <button type="button" className={styles.deleteButton} onClick={() => onDelete(doc.id)}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className={styles.footer}>
        <span className={styles.showing}>
          Mostrando {pageItems.length === 0 ? 0 : startIndex + 1}-{startIndex + pageItems.length} de{" "}
          {filtered.length}
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
    </div>
  );
}
