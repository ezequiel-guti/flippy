"use client";

import { useState } from "react";
import ChatSidebar from "@/components/ChatSidebar";
import ChatWindow from "@/components/ChatWindow";
import { mockChats, mockMessages } from "@/lib/mockChatData";
import type { ChatMessageData } from "@/types/chat";
import styles from "./page.module.css";

export default function ChatPage() {
  const [chats, setChats] = useState(mockChats);
  const [activeChatId, setActiveChatId] = useState(mockChats[0]?.id);
  const [messagesByChat] = useState<Record<string, ChatMessageData[]>>({
    [mockChats[0]?.id]: mockMessages,
  });
  const [showHistoryOnMobile, setShowHistoryOnMobile] = useState(false);

  function handleNewChat() {
    const id = crypto.randomUUID();
    const newChat = { id, title: "Nuevo chat", updatedAt: new Date().toISOString() };
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(id);
    setShowHistoryOnMobile(false);
  }

  function handleSelectChat(chatId: string) {
    setActiveChatId(chatId);
    setShowHistoryOnMobile(false);
  }

  return (
    <div className={`${styles.layout} ${showHistoryOnMobile ? styles.showHistory : ""}`}>
      <aside className={styles.sidebarPane}>
        <ChatSidebar
          chats={chats}
          activeChatId={activeChatId}
          userName="Virgilio"
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onClose={showHistoryOnMobile ? () => setShowHistoryOnMobile(false) : undefined}
        />
      </aside>
      <main className={styles.mainPane}>
        <ChatWindow
          initialMessages={activeChatId ? messagesByChat[activeChatId] ?? [] : []}
          onOpenHistory={() => setShowHistoryOnMobile(true)}
        />
      </main>
    </div>
  );
}
