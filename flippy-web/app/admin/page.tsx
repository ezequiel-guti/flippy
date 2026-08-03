"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiUpload, apiDelete, apiPost, apiPatch, ApiError } from "@/services/api";
import type { DocumentSummary } from "@/types/document";
import type { DocumentFolder } from "@/types/folder";
import AdminSidebar from "@/components/AdminSidebar";
import AdminTopBar from "@/components/AdminTopBar";
import AdminUploadForm from "@/components/AdminUploadForm";
import AdminDocumentTable from "@/components/AdminDocumentTable";
import AdminFolderPanel from "@/components/AdminFolderPanel";
import styles from "./page.module.css";

const POLL_INTERVAL_MS = 4000;

export default function AdminPage() {
  const router = useRouter();
  const [allDocuments, setAllDocuments] = useState<DocumentSummary[]>([]);
  const [folders, setFolders] = useState<DocumentFolder[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [folderError, setFolderError] = useState<string | null>(null);
  const [isUploadPanelOpen, setIsUploadPanelOpen] = useState(false);
  const [reprocessingIds, setReprocessingIds] = useState<Set<string>>(new Set());

  async function loadFolders() {
    const data = await apiGet<DocumentFolder[]>("/api/v1/admin/folders");
    setFolders(data);
  }

  async function loadDocuments() {
    try {
      const data = await apiGet<DocumentSummary[]>("/api/v1/admin/documents?all=true");
      setAllDocuments(data);
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
    const hasProcessing = allDocuments.some((d) => d.status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(loadDocuments, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allDocuments.some((d) => d.status === "processing")]);

  const documentsInCurrentFolder = useMemo(
    () => allDocuments.filter((d) => (d.folder_id ?? null) === currentFolderId),
    [allDocuments, currentFolderId]
  );

  async function handleUpload(file: File) {
    await apiUpload<DocumentSummary>(
      "/api/v1/admin/documents",
      file,
      currentFolderId ? { folder_id: currentFolderId } : {}
    );
    await loadDocuments();
  }

  async function handleDelete(id: string) {
    setAllDocuments((prev) => prev.filter((d) => d.id !== id));
    try {
      await apiDelete(`/api/v1/admin/documents/${id}`);
    } catch {
      setError("No pudimos eliminar el documento. Refrescá la página.");
      await loadDocuments();
    }
  }

  async function handleReprocess(id: string) {
    setReprocessingIds((prev) => new Set(prev).add(id));
    try {
      const updated = await apiPost<DocumentSummary>(`/api/v1/admin/documents/${id}/reprocess`, {});
      setAllDocuments((prev) =>
        prev.map((d) =>
          d.id === id
            ? { ...d, status: updated.status, chunk_count: updated.chunk_count, error_detail: updated.error_detail }
            : d
        )
      );
    } catch {
      setError("No pudimos reprocesar el documento. Refrescá la página.");
    } finally {
      setReprocessingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
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
      <div className={styles.rightPane}>
        <AdminTopBar currentFolderName={currentFolderName} />
        <div className={styles.contentRow}>
          <AdminFolderPanel
            folders={folders}
            currentFolderId={currentFolderId}
            onNavigate={setCurrentFolderId}
            onCreate={handleCreateFolder}
            onRename={handleRenameFolder}
            onDelete={handleDeleteFolder}
            error={folderError}
          />
          <main className={styles.mainPane}>
            <AdminUploadForm
              onUpload={handleUpload}
              existingNames={allDocuments.map((d) => d.name)}
              folders={folders}
              currentFolderId={currentFolderId}
              onNavigate={setCurrentFolderId}
              onPanelOpenChange={setIsUploadPanelOpen}
            />

            {error && (
              <p className={styles.error} role="alert">
                {error}
              </p>
            )}

            {!isUploadPanelOpen &&
              (isLoading ? (
                <p className={styles.loading}>Cargando documentos…</p>
              ) : (
                <AdminDocumentTable
                  documents={documentsInCurrentFolder}
                  searchScope={allDocuments}
                  onDelete={handleDelete}
                  onReprocess={handleReprocess}
                  reprocessingIds={reprocessingIds}
                  folders={folders}
                  onMove={handleMoveDocument}
                />
              ))}
          </main>
        </div>
      </div>
    </div>
  );
}
