"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiUpload, apiDelete, ApiError } from "@/services/api";
import type { DocumentSummary } from "@/types/document";
import AdminUploadForm from "@/components/AdminUploadForm";
import AdminDocumentTable from "@/components/AdminDocumentTable";
import styles from "./page.module.css";

const POLL_INTERVAL_MS = 4000;

export default function AdminPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments() {
    try {
      const data = await apiGet<DocumentSummary[]>("/api/v1/admin/documents");
      setDocuments(data);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        router.push("/login");
        return;
      }
      setError("No pudimos cargar los documentos.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
    const hasProcessing = documents.some((d) => d.status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(loadDocuments, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents.some((d) => d.status === "processing")]);

  async function handleUpload(file: File) {
    await apiUpload<DocumentSummary>("/api/v1/admin/documents", file);
    await loadDocuments();
  }

  async function handleDelete(id: string) {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    try {
      await apiDelete(`/api/v1/admin/documents/${id}`);
    } catch {
      setError("No pudimos eliminar el documento. Refrescá la página.");
      await loadDocuments();
    }
  }

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Administración de documentos</h1>
      <p className={styles.subtitle}>Corpus documental de Flippy — PDF, Word, texto e imágenes.</p>

      <AdminUploadForm onUpload={handleUpload} existingNames={documents.map((d) => d.name)} />

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      {isLoading ? (
        <p className={styles.loading}>Cargando documentos…</p>
      ) : (
        <AdminDocumentTable documents={documents} onDelete={handleDelete} />
      )}
    </main>
  );
}
