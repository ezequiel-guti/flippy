"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import type { ChatSummary } from "@/types/chat";
import { groupChatsByDate } from "@/lib/groupChatsByDate";
import styles from "./ChatSidebar.module.css";

interface ChatSidebarProps {
  chats: ChatSummary[];
  activeChatId?: string;
  userName: string;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onClose?: () => void;
}

export default function ChatSidebar({
  chats,
  activeChatId,
  userName,
  onSelectChat,
  onNewChat,
  onClose,
}: ChatSidebarProps) {
  const [query, setQuery] = useState("");

  const filteredChats = useMemo(
    () => chats.filter((chat) => chat.title.toLowerCase().includes(query.trim().toLowerCase())),
    [chats, query]
  );
  const groups = useMemo(() => groupChatsByDate(filteredChats), [filteredChats]);

  return (
    <nav className={styles.sidebar} aria-label="Historial de chats">
      <div className={styles.top}>
        {onClose && (
          <button type="button" className={styles.backButton} onClick={onClose} aria-label="Volver al chat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
              <path d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}
        <Image src="/icons/logo-shield.png" alt="" width={22} height={26} />
        <span className={styles.brandName}>Flippy</span>
      </div>

      <button className={styles.newChatButton} onClick={onNewChat} type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
          <path d="M12 5v14M5 12h14" />
        </svg>
        Nuevo chat
      </button>

      <label className={styles.search}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4-4" />
        </svg>
        <input
          type="text"
          placeholder="Buscar en tus chats"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Buscar en tus chats"
        />
      </label>

      {groups.length === 0 ? (
        <p className={styles.emptyState}>
          {query ? "No encontramos chats con ese nombre." : "Todavía no tenés conversaciones."}
        </p>
      ) : (
        <div className={styles.groups}>
          {groups.map((group) => (
            <div key={group.label}>
              <div className={styles.sectionLabel}>{group.label}</div>
              <ul className={styles.chatList}>
                {group.chats.map((chat) => (
                  <li key={chat.id}>
                    <button
                      type="button"
                      className={`${styles.chatItem} ${chat.id === activeChatId ? styles.chatItemActive : ""}`}
                      onClick={() => onSelectChat(chat.id)}
                      aria-current={chat.id === activeChatId ? "true" : undefined}
                    >
                      <span className={styles.chatTitle}>{chat.title}</span>
                      <span className={styles.kebab} aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15">
                          <circle cx="12" cy="5" r="1.5" />
                          <circle cx="12" cy="12" r="1.5" />
                          <circle cx="12" cy="19" r="1.5" />
                        </svg>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className={styles.footer}>
        <span className={styles.avatar}>{userName.charAt(0).toUpperCase()}</span>
        <span className={styles.footerLabel}>
          {userName}
          <small>Socio · Flipping Master</small>
        </span>
        <Link href="/admin" className={styles.adminLink} aria-label="Panel de administración">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
          </svg>
        </Link>
      </div>
    </nav>
  );
}
