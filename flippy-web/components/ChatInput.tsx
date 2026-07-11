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
    <form className={styles.form} onSubmit={handleSubmit}>
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
        className={styles.textInput}
        placeholder={imageFile ? `Imagen adjunta: ${imageFile.name}` : "Escribí tu consulta..."}
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
      />
      <button type="submit" className={styles.sendButton} disabled={disabled || (!text.trim() && !imageFile)}>
        Enviar
      </button>
    </form>
  );
}
