"use client";

import { useRef, useState } from "react";
import styles from "./ChatInput.module.css";

interface ChatInputProps {
  onSend: (text: string, imageFile: File | null) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!text.trim() && !imageFile) return;
    onSend(text.trim(), imageFile);
    setText("");
    setImageFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <form className={styles.inputbar} onSubmit={handleSubmit}>
      <label htmlFor="chat-message-input" className={styles.visuallyHidden}>
        Escribí tu consulta
      </label>
      <button
        type="button"
        className={styles.attachButton}
        aria-label="Adjuntar imagen"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
      >
        📎
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className={styles.visuallyHidden}
        onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
        aria-label="Seleccionar imagen para adjuntar"
      />
      <input
        id="chat-message-input"
        type="text"
        className={styles.field}
        placeholder={imageFile ? `Imagen adjunta: ${imageFile.name}` : "Escribí tu mensaje…"}
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
      />
      <button
        type="submit"
        className={styles.send}
        aria-label="Enviar"
        disabled={disabled || (!text.trim() && !imageFile)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" width="20" height="20">
          <path d="M12 19V5M6 11l6-6 6 6" />
        </svg>
      </button>
    </form>
  );
}
