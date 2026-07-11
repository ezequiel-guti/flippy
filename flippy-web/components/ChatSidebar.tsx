"use client";

import type { ChatSummary } from "@/types/chat";
import styles from "./ChatSidebar.module.css";

interface ChatSidebarProps {
  chats: ChatSummary[];
  activeChatId?: string;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
}

export default function ChatSidebar({ chats, activeChatId, onSelectChat, onNewChat }: ChatSidebarProps) {
  return (
    <nav className={styles.sidebar} aria-label="Historial de chats">
      <button className={styles.newChatButton} onClick={onNewChat} type="button">
        + Nuevo chat
      </button>

      {chats.length === 0 ? (
        <p className={styles.emptyState}>Todavía no tenés conversaciones.</p>
      ) : (
        <ul className={styles.chatList}>
          {chats.map((chat) => (
            <li key={chat.id}>
              <button
                type="button"
                className={`${styles.chatItem} ${chat.id === activeChatId ? styles.chatItemActive : ""}`}
                onClick={() => onSelectChat(chat.id)}
                aria-current={chat.id === activeChatId ? "true" : undefined}
              >
                {chat.title}
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
