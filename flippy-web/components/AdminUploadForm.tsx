"use client";

import { useRef, useState } from "react";
import styles from "./AdminUploadForm.module.css";

interface AdminUploadFormProps {
  onUpload: (file: File) => Promise<void>;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.jpg,.jpeg,.png";

export default function AdminUploadForm({ onUpload }: AdminUploadFormProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;

    setError(null);
    setIsUploading(true);
    try {
      await onUpload(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
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
        <input type="file" accept={ACCEPTED_EXTENSIONS} ref={fileInputRef} disabled={isUploading} />
      </label>
      <button type="submit" className={styles.submit} disabled={isUploading}>
        {isUploading ? "Subiendo…" : "Subir"}
      </button>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
