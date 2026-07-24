"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiUpload, apiDelete, apiPost, apiPatch, ApiError } from "@/services/api";
import type { DocumentSummary } from "@/types/document";
import type { DocumentFolder } from "@/types/folder";
import AdminSidebar from "@/components/AdminSidebar";
import AdminUploadForm from "@/components/AdminUploadForm";
import AdminDocumentTable from "@/components/AdminDocumentTable";
import AdminFolderPanel from "@/components/AdminFolderPanel";
import styles from "./page.module.css";

const POLL_INTERVAL_MS = 4000;

export default function AdminPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [folders, setFolders] = useState<DocumentFolder[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [viewAll, setViewAll] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [folderError, setFolderError] = useState<string | null>(null);

  async function loadFolders() {
    const data = await apiGet<DocumentFolder[]>("/api/v1/admin/folders");
    setFolders(data);
  }

  async function loadDocuments() {
    try {
      const path = viewAll
        ? "/api/v1/admin/documents?all=true"
        : `/api/v1/admin/documents${currentFolderId ? `?folder_id=${currentFolderId}` : ""}`;
      const data = await apiGet<DocumentSummary[]>(path);
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
    loadFolders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadDocuments();
    const hasProcessing = documents.some((d) => d.status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(loadDocuments, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentFolderId, viewAll, documents.some((d) => d.status === "processing")]);

  async function handleUpload(file: File) {
    await apiUpload<DocumentSummary>(
      "/api/v1/admin/documents",
      file,
      currentFolderId ? { folder_id: currentFolderId } : {}
    );
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

  async function handleMoveDocument(documentId: string, folderId: string | null) {
    try {
      await apiPatch(`/api/v1/admin/documents/${documentId}/folder`, { folder_id: folderId });
      await loadDocuments();
    } catch {
      setError("No pudimos mover el documento. Refrescá la página.");
    }
  }

  async function handleCreateFolder(name: string, parentId: string | null) {
    try {
      await apiPost("/api/v1/admin/folders", { name, parent_id: parentId });
      setFolderError(null);
      await loadFolders();
    } catch {
      setFolderError("No pudimos crear la carpeta.");
    }
  }

  async function handleRenameFolder(folderId: string, name: string) {
    try {
      await apiPatch(`/api/v1/admin/folders/${folderId}`, { name });
      setFolderError(null);
      await loadFolders();
    } catch {
      setFolderError("No pudimos renombrar la carpeta.");
    }
  }

  async function handleDeleteFolder(folderId: string) {
    try {
      await apiDelete(`/api/v1/admin/folders/${folderId}`);
      setFolderError(null);
      await loadFolders();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFolderError("La carpeta no está vacía — moveé o eliminá su contenido antes de borrarla.");
      } else {
        setFolderError("No pudimos eliminar la carpeta.");
      }
    }
  }

  const currentFolderName = currentFolderId
    ? folders.find((f) => f.id === currentFolderId)?.name ?? null
    : null;

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebarPane}>
        <AdminSidebar activeHref="/admin" />
      </aside>
      <main className={styles.mainPane}>
        <h1 className={styles.title}>Documentos</h1>
        <p className={styles.subtitle}>Corpus documental de Flippy — PDF, Word, texto, JSON, HTML e imágenes.</p>

        <AdminFolderPanel
          folders={folders}
          currentFolderId={currentFolderId}
          onNavigate={setCurrentFolderId}
          onCreate={handleCreateFolder}
          onRename={handleRenameFolder}
          onDelete={handleDeleteFolder}
          error={folderError}
        />

        <AdminUploadForm
          onUpload={handleUpload}
          existingNames={documents.map((d) => d.name)}
          currentFolderName={currentFolderName}
        />

        <label className={styles.viewAllToggle}>
          <input type="checkbox" checked={viewAll} onChange={(e) => setViewAll(e.target.checked)} />
          Ver todo el corpus (sin filtrar por carpeta)
        </label>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        {isLoading ? (
          <p className={styles.loading}>Cargando documentos…</p>
        ) : (
          <AdminDocumentTable
            documents={documents}
            onDelete={handleDelete}
            folders={folders}
            onMove={handleMoveDocument}
          />
        )}
      </main>
    </div>
  );
}
