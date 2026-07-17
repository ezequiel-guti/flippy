"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ChatSidebar from "@/components/ChatSidebar";
import ChatWindow from "@/components/ChatWindow";
import { apiGet, apiPost, apiPatch, apiDelete, ApiError } from "@/services/api";
import type { ChatMessageData, ChatSummary } from "@/types/chat";
import styles from "./page.module.css";

interface RawChatSummary {
  id: string;
  title: string;
  updated_at: string;
}

interface RawMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  image_url: string | null;
  created_at: string;
}

interface UserProfile {
  email: string;
}

function toChatSummary(raw: RawChatSummary): ChatSummary {
  return { id: raw.id, title: raw.title, updatedAt: raw.updated_at };
}

function toChatMessage(raw: RawMessage): ChatMessageData {
  return {
    id: raw.id,
    role: raw.role,
    content: raw.content,
    imageUrl: raw.image_url ?? undefined,
    createdAt: raw.created_at,
  };
}

export default function ChatPage() {
  const router = useRouter();
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [userName, setUserName] = useState("Vos");
  const [isLoading, setIsLoading] = useState(true);
  const [showHistoryOnMobile, setShowHistoryOnMobile] = useState(false);

  function redirectOnAuthError(err: unknown): boolean {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      router.push("/login");
      return true;
    }
    return false;
  }

  useEffect(() => {
    async function init() {
      try {
        const profile = await apiGet<UserProfile>("/api/v1/auth/me");
        setUserName(profile.email.split("@")[0]);

        const rawChats = await apiGet<RawChatSummary[]>("/api/v1/chats");
        let list = rawChats.map(toChatSummary);
        if (list.length === 0) {
          const created = await apiPost<RawChatSummary>("/api/v1/chats", {});
          list = [toChatSummary(created)];
        }
        setChats(list);
        setActiveChatId(list[0].id);
      } catch (err) {
        redirectOnAuthError(err);
      } finally {
        setIsLoading(false);
      }
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!activeChatId) return;
    apiGet<RawMessage[]>(`/api/v1/chats/${activeChatId}/messages`)
      .then((raw) => setMessages(raw.map(toChatMessage)))
      .catch(redirectOnAuthError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChatId]);

  async function refreshChats() {
    try {
      const rawChats = await apiGet<RawChatSummary[]>("/api/v1/chats");
      setChats(rawChats.map(toChatSummary));
    } catch (err) {
      redirectOnAuthError(err);
    }
  }

  async function handleNewChat() {
    try {
      const created = await apiPost<RawChatSummary>("/api/v1/chats", {});
      const summary = toChatSummary(created);
      setChats((prev) => [summary, ...prev]);
      setActiveChatId(summary.id);
      setMessages([]);
      setShowHistoryOnMobile(false);
    } catch (err) {
      redirectOnAuthError(err);
    }
  }

  function handleSelectChat(chatId: string) {
    setActiveChatId(chatId);
    setShowHistoryOnMobile(false);
  }

  async function handleRenameChat(chatId: string, title: string) {
    try {
      await apiPatch<RawChatSummary>(`/api/v1/chats/${chatId}`, { title });
      setChats((prev) => prev.map((chat) => (chat.id === chatId ? { ...chat, title } : chat)));
    } catch (err) {
      redirectOnAuthError(err);
    }
  }

  async function handleDeleteChat(chatId: string) {
    try {
      await apiDelete(`/api/v1/chats/${chatId}`);
      setChats((prev) => prev.filter((chat) => chat.id !== chatId));
      if (activeChatId === chatId) {
        setActiveChatId(undefined);
        setMessages([]);
      }
    } catch (err) {
      redirectOnAuthError(err);
    }
  }

  if (isLoading) {
    return <main className={styles.loadingPage}>Cargando…</main>;
  }

  return (
    <div className={`${styles.layout} ${showHistoryOnMobile ? styles.showHistory : ""}`}>
      <aside className={styles.sidebarPane}>
        <ChatSidebar
          chats={chats}
          activeChatId={activeChatId}
          userName={userName}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onRenameChat={handleRenameChat}
          onDeleteChat={handleDeleteChat}
          onClose={showHistoryOnMobile ? () => setShowHistoryOnMobile(false) : undefined}
        />
      </aside>
      <main className={styles.mainPane}>
        {activeChatId && (
          <ChatWindow
            key={activeChatId}
            chatId={activeChatId}
            initialMessages={messages}
            onOpenHistory={() => setShowHistoryOnMobile(true)}
            onMessageSent={refreshChats}
          />
        )}
      </main>
    </div>
  );
}
