"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessageData } from "@/types/chat";
import { apiStream, apiStreamUpload } from "@/services/api";
import ChatMessage from "./ChatMessage";
import ChatChips from "./ChatChips";
import ChatInput from "./ChatInput";
import ChatHeader from "./ChatHeader";
import styles from "./ChatWindow.module.css";

const STARTER_SUGGESTIONS = ["¿Cómo calculo el ROI de un flip?", "Ideas para remodelar"];

interface ChatWindowProps {
  chatId: string;
  initialMessages: ChatMessageData[];
  onOpenHistory: () => void;
  onMessageSent?: () => void;
}

export default function ChatWindow({ chatId, initialMessages, onOpenHistory, onMessageSent }: ChatWindowProps) {
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

  async function consumeStream(stream: ReadableStream<Uint8Array>, assistantId: string) {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let accumulated = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const line = event.trim();
        if (!line.startsWith("data: ")) continue;
        const data = line.slice("data: ".length);
        if (data === "[DONE]") continue;

        const parsed = JSON.parse(data) as { text?: string; error?: string };
        if (parsed.error) {
          setError(parsed.error);
        } else if (parsed.text) {
          accumulated += parsed.text;
          const snapshot = accumulated;
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: snapshot } : m)));
        }
      }
    }
  }

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

    if (!text && !imageFile) return;

    setIsSending(true);
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", createdAt: new Date().toISOString() },
    ]);

    try {
      const stream = imageFile
        ? await apiStreamUpload(`/api/v1/chats/${chatId}/messages/image`, imageFile, { content: text })
        : await apiStream(`/api/v1/chats/${chatId}/messages`, { content: text });
      await consumeStream(stream, assistantId);
      onMessageSent?.();
    } catch {
      setError(
        imageFile ? "No pudimos analizar la imagen. Intentá de nuevo." : "No pudimos enviar tu mensaje. Intentá de nuevo."
      );
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setIsSending(false);
    }
  }

  const showStarterChips = messages.length === 0;

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
