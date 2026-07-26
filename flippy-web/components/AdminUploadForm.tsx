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

function FileIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="28" height="28" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2v6h6" />
    </svg>
  );
}

export default function AdminUploadForm({
  onUpload,
  existingNames = [],
  folders = [],
  currentFolderId = null,
  onNavigate,
}: AdminUploadFormProps) {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [duplicateNames, setDuplicateNames] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const chain = ancestorChain(folders, currentFolderId);

  async function handleFiles(fileList: FileList | File[]) {
    const files = Array.from(fileList);
    if (files.length === 0) return;

    const known = new Set(existingNames);
    const duplicates: string[] = [];
    const toUpload: File[] = [];
    for (const file of files) {
      if (known.has(file.name)) {
        duplicates.push(file.name);
      } else {
        known.add(file.name);
        toUpload.push(file);
      }
    }

    setError(null);
    setDuplicateNames(duplicates);

    if (toUpload.length === 0) return;

    setIsUploading(true);
    let hadFailure = false;
    for (let i = 0; i < toUpload.length; i++) {
      setProgress(toUpload.length > 1 ? `Subiendo ${i + 1} de ${toUpload.length}: ${toUpload[i].name}` : "Subiendo…");
      try {
        await onUpload(toUpload[i]);
      } catch {
        hadFailure = true;
      }
    }
    setIsUploading(false);
    setProgress(null);

    if (hadFailure) {
      setError("No pudimos subir uno o más archivos. Intentá de nuevo.");
    } else if (duplicates.length === 0) {
      setIsPanelOpen(false);
    }
  }

  function handleInputChange() {
    if (fileInputRef.current?.files) {
      handleFiles(fileInputRef.current.files);
      fileInputRef.current.value = "";
    }
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
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
          <button type="button" className={styles.addButton} onClick={() => setIsPanelOpen((open) => !open)}>
            Subir archivo
          </button>
        </div>
      </div>

      {isPanelOpen && (
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
          <p className={styles.dropzoneText}>Arrastrá archivos acá para agregarlos al corpus</p>
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
          {isUploading && progress && <p className={styles.progress}>{progress}</p>}
        </div>
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
