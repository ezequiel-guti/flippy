import type { ChatSummary } from "@/types/chat";

export interface ChatGroup {
  label: string;
  chats: ChatSummary[];
}

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

export function groupChatsByDate(chats: ChatSummary[], now: Date = new Date()): ChatGroup[] {
  const today = startOfDay(now);
  const yesterday = today - 86_400_000;
  const weekAgo = today - 7 * 86_400_000;

  const buckets: Record<string, ChatSummary[]> = {
    Hoy: [],
    Ayer: [],
    "Esta semana": [],
    Anteriores: [],
  };

  for (const chat of chats) {
    const updatedAt = startOfDay(new Date(chat.updatedAt));
    if (updatedAt === today) buckets["Hoy"].push(chat);
    else if (updatedAt === yesterday) buckets["Ayer"].push(chat);
    else if (updatedAt >= weekAgo) buckets["Esta semana"].push(chat);
    else buckets["Anteriores"].push(chat);
  }

  return Object.entries(buckets)
    .filter(([, chats]) => chats.length > 0)
    .map(([label, chats]) => ({ label, chats }));
}
