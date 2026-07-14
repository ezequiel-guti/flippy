"use client";

import { useRef, useState } from "react";
import styles from "./AdminUploadForm.module.css";

interface AdminUploadFormProps {
  onUpload: (file: File) => Promise<void>;
  existingNames?: string[];
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.json,.html,.jpg,.jpeg,.png";

export default function AdminUploadForm({ onUpload, existingNames = [] }: AdminUploadFormProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateName, setDuplicateName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange() {
    const file = fileInputRef.current?.files?.[0];
    setError(null);
    if (file && existingNames.includes(file.name)) {
      setDuplicateName(file.name);
    } else {
      setDuplicateName(null);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    if (existingNames.includes(file.name)) {
      setDuplicateName(file.name);
      return;
    }

    setError(null);
    setIsUploading(true);
    try {
      await onUpload(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setDuplicateName(null);
    } catch {
      setError("No pudimos subir el archivo. Intentá de nuevo.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <label className={styles.field}>
        Subir documento al corpus
        <input
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          ref={fileInputRef}
          disabled={isUploading}
          onChange={handleFileChange}
        />
      </label>
      <button type="submit" className={styles.submit} disabled={isUploading || !!duplicateName}>
        {isUploading ? "Subiendo…" : "Subir"}
      </button>
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
    </form>
  );
}
