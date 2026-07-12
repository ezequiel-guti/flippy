"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessageData } from "@/types/chat";
import ChatMessage from "./ChatMessage";
import ChatChips from "./ChatChips";
import ChatInput from "./ChatInput";
import ChatHeader from "./ChatHeader";
import styles from "./ChatWindow.module.css";

const STARTER_SUGGESTIONS = ["¿Cómo calculo el ROI de un flip?", "Ideas para remodelar"];

interface ChatWindowProps {
  initialMessages: ChatMessageData[];
  onOpenHistory: () => void;
}

export default function ChatWindow({ initialMessages, onOpenHistory }: ChatWindowProps) {
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

  async function sendMessage(text: string, imageFile: File | null) {
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

  const showStarterChips = messages.length <= 1 && messages.every((m) => m.role === "assistant");

  return (
    <div className={styles.window}>
      <ChatHeader onOpenHistory={onOpenHistory} />
      <div className={styles.messages} role="log" aria-live="polite">
        {messages.length === 0 ? (
          <p className={styles.emptyState}>Hola, soy Flippy. Te ayudo en lo que necesites.</p>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} message={message} />)
        )}
        {showStarterChips && <ChatChips suggestions={STARTER_SUGGESTIONS} onSelect={(s) => sendMessage(s, null)} />}
        {isSending && <p className={styles.loadingIndicator}>Flippy está escribiendo…</p>}
        {error && (
          <p className={styles.errorMessage} role="alert">
            {error}
          </p>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={sendMessage} disabled={isSending} />
    </div>
  );
}
