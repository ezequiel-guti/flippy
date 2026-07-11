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

  function handleNewChat() {
    const id = crypto.randomUUID();
    const newChat = { id, title: "Nuevo chat", updatedAt: new Date().toISOString() };
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(id);
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebarPane}>
        <ChatSidebar
          chats={chats}
          activeChatId={activeChatId}
          onSelectChat={setActiveChatId}
          onNewChat={handleNewChat}
        />
      </aside>
      <main className={styles.mainPane}>
        <ChatWindow initialMessages={activeChatId ? messagesByChat[activeChatId] ?? [] : []} />
      </main>
    </div>
  );
}
