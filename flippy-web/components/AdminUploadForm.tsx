"use client";

import { useRef, useState } from "react";
import type { DocumentFolder } from "@/types/folder";
import styles from "./AdminUploadForm.module.css";

interface AdminUploadFormProps {
  onUpload: (file: File) => Promise<void>;
  existingNames?: string[];
  folders?: DocumentFolder[];
  currentFolderId?: string | null;
  onNavigate?: (folderId: string | null) => void;
  onPanelOpenChange?: (isOpen: boolean) => void;
}

interface QueuedFile {
  id: string;
  file: File;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.json,.html,.jpg,.jpeg,.png";

function ancestorChain(folders: DocumentFolder[], currentFolderId: string | null): DocumentFolder[] {
  const byId = new Map(folders.map((f) => [f.id, f]));
  const chain: DocumentFolder[] = [];
  let cursor = currentFolderId ? byId.get(currentFolderId) : undefined;
  while (cursor) {
    chain.unshift(cursor);
    cursor = cursor.parent_id ? byId.get(cursor.parent_id) : undefined;
  }
  return chain;
}

function FileIcon({ size = 28 }: { size?: number }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width={size} height={size} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2v6h6" />
    </svg>
  );
}

function queueId(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2)}`;
}

export default function AdminUploadForm({
  onUpload,
  existingNames = [],
  folders = [],
  currentFolderId = null,
  onNavigate,
  onPanelOpenChange,
}: AdminUploadFormProps) {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<QueuedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [duplicateNames, setDuplicateNames] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const chain = ancestorChain(folders, currentFolderId);

  function updatePanelOpen(isOpen: boolean) {
    setIsPanelOpen(isOpen);
    onPanelOpenChange?.(isOpen);
  }

  function addFiles(fileList: FileList | File[]) {
    const files = Array.from(fileList);
    if (files.length === 0) return;

    setError(null);
    const known = new Set([...existingNames, ...pendingFiles.map((pf) => pf.file.name)]);
    const duplicates: string[] = [];
    const accepted: QueuedFile[] = [];
    for (const file of files) {
      if (known.has(file.name)) {
        duplicates.push(file.name);
      } else {
        known.add(file.name);
        accepted.push({ id: queueId(file), file });
      }
    }

    setDuplicateNames(duplicates);
    if (accepted.length > 0) setPendingFiles((prev) => [...prev, ...accepted]);
  }

  function removeFromQueue(id: string) {
    setPendingFiles((prev) => prev.filter((pf) => pf.id !== id));
  }

  async function handleUploadQueue() {
    if (pendingFiles.length === 0) return;
    const toUpload = pendingFiles;

    setError(null);
    setIsUploading(true);
    const failed: QueuedFile[] = [];
    for (let i = 0; i < toUpload.length; i++) {
      setProgress(
        toUpload.length > 1 ? `Subiendo ${i + 1} de ${toUpload.length}: ${toUpload[i].file.name}` : "Subiendo…"
      );
      try {
        await onUpload(toUpload[i].file);
      } catch {
        failed.push(toUpload[i]);
      }
    }
    setIsUploading(false);
    setProgress(null);
    setPendingFiles(failed);

    if (failed.length > 0) {
      setError("No pudimos subir uno o más archivos. Intentá de nuevo.");
    } else {
      updatePanelOpen(false);
    }
  }

  function handleInputChange() {
    if (fileInputRef.current?.files) {
      addFiles(fileInputRef.current.files);
      fileInputRef.current.value = "";
    }
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    addFiles(event.dataTransfer.files);
  }

  const duplicateMessage =
    duplicateNames.length === 1
      ? `Ya existe un archivo llamado "${duplicateNames[0]}" en el corpus. Eliminalo primero si querés reemplazarlo.`
      : duplicateNames.length > 1
        ? `Ya existen archivos con estos nombres en el corpus: "${duplicateNames.join('", "')}". Eliminalos primero si querés reemplazarlos.`
        : null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.bar}>
        <nav className={styles.breadcrumb} aria-label="Ubicación actual">
          <button type="button" className={styles.breadcrumbRoot} onClick={() => onNavigate?.(null)}>
            Raíz
          </button>
          <span className={styles.breadcrumbSep}>/</span>
          {chain.map((folder, index) => {
            const isLast = index === chain.length - 1;
            return (
              <span key={folder.id} className={styles.breadcrumbSegment}>
                {isLast ? (
                  <span className={styles.breadcrumbCurrent}>{folder.name}</span>
                ) : (
                  <button type="button" className={styles.breadcrumbLink} onClick={() => onNavigate?.(folder.id)}>
                    {folder.name}
                  </button>
                )}
                <span className={styles.breadcrumbSep}>/</span>
              </span>
            );
          })}
        </nav>

        <div className={styles.actions}>
          <button type="button" className={styles.addButton} onClick={() => updatePanelOpen(!isPanelOpen)}>
            Subir archivo
          </button>
        </div>
      </div>

      {isPanelOpen && (
        <>
          <div
            className={`${styles.dropzone} ${isDragging ? styles.dropzoneDragging : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <span className={styles.dropzoneIcon}>
              <FileIcon />
            </span>
            <p className={styles.dropzoneText}>
              {pendingFiles.length > 0
                ? "Arrastrá más archivos acá para agregarlos al corpus"
                : "Arrastrá archivos acá para agregarlos al corpus"}
            </p>
            <p className={styles.dropzoneSub}>
              O{" "}
              <button type="button" className={styles.chooseLink} onClick={() => fileInputRef.current?.click()}>
                elegí tus archivos
              </button>
            </p>
            <input
              type="file"
              multiple
              accept={ACCEPTED_EXTENSIONS}
              ref={fileInputRef}
              disabled={isUploading}
              onChange={handleInputChange}
              className={styles.hiddenInput}
              aria-label="Subir documentos al corpus"
            />
          </div>

          {pendingFiles.length > 0 && (
            <ul className={styles.queueList}>
              {pendingFiles.map((pf) => (
                <li key={pf.id} className={styles.queueRow}>
                  <span className={styles.queueIcon}>
                    <FileIcon size={16} />
                  </span>
                  <span className={styles.queueName}>{pf.file.name}</span>
                  <button
                    type="button"
                    className={styles.queueRemove}
                    onClick={() => removeFromQueue(pf.id)}
                    disabled={isUploading}
                    aria-label={`Quitar ${pf.file.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}

          {pendingFiles.length > 0 && (
            <button type="button" className={styles.processButton} onClick={handleUploadQueue} disabled={isUploading}>
              {isUploading
                ? progress ?? "Subiendo…"
                : `Subir ${pendingFiles.length} archivo${pendingFiles.length > 1 ? "s" : ""}`}
            </button>
          )}
        </>
      )}

      {duplicateMessage && (
        <p className={styles.warning} role="alert">
          {duplicateMessage}
        </p>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
