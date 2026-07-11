"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessageData } from "@/types/chat";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import styles from "./ChatWindow.module.css";

interface ChatWindowProps {
  initialMessages: ChatMessageData[];
}

export default function ChatWindow({ initialMessages }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessageData[]>(initialMessages);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text: string, imageFile: File | null) {
    const userMessage: ChatMessageData = {
      id: crypto.randomUUID(),
      role: "user",
      content: text || "Imagen adjunta",
      imageUrl: imageFile ? URL.createObjectURL(imageFile) : undefined,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setError(null);
    setIsSending(true);

    // TODO(Hito 2): reemplazar por llamada real a flippy-api (SSE) via services/api.ts
    try {
      await new Promise((resolve) => setTimeout(resolve, 600));
      const assistantMessage: ChatMessageData = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Esta es una respuesta de ejemplo — la integración con el backend RAG llega en el Hito 2.",
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setError("No pudimos enviar tu mensaje. Intentá de nuevo.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className={styles.window}>
      <div className={styles.messages} role="log" aria-live="polite">
        {messages.length === 0 ? (
          <p className={styles.emptyState}>Empezá la conversación escribiendo tu consulta.</p>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} message={message} />)
        )}
        {isSending && <p className={styles.loadingIndicator}>Flippy está escribiendo…</p>}
        {error && (
          <p className={styles.errorMessage} role="alert">
            {error}
          </p>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={isSending} />
    </div>
  );
}
