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

export default function AdminUploadForm({
  onUpload,
  existingNames = [],
  folders = [],
  currentFolderId = null,
  onNavigate,
}: AdminUploadFormProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateName, setDuplicateName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const chain = ancestorChain(folders, currentFolderId);

  async function handleFileChange() {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setError(null);

    if (existingNames.includes(file.name)) {
      setDuplicateName(file.name);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setDuplicateName(null);
    setIsUploading(true);
    try {
      await onUpload(file);
    } catch {
      setError("No pudimos subir el archivo. Intentá de nuevo.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
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
        <button
          type="button"
          className={styles.addButton}
          disabled={isUploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {isUploading ? "Subiendo…" : "Subir archivo"}
        </button>
        <input
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          ref={fileInputRef}
          disabled={isUploading}
          onChange={handleFileChange}
          className={styles.hiddenInput}
          aria-label="Subir documento al corpus"
        />
      </div>

      {duplicateName && (
        <p className={styles.warning} role="alert">
          Ya existe un archivo llamado &quot;{duplicateName}&quot; en el corpus. Eliminalo primero si querés
          reemplazarlo.
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
