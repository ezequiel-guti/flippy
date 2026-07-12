import { groupChatsByDate } from "./groupChatsByDate";
import type { ChatSummary } from "@/types/chat";

describe("groupChatsByDate", () => {
  const now = new Date("2026-07-12T12:00:00Z");

  const chats: ChatSummary[] = [
    { id: "1", title: "Today chat", updatedAt: "2026-07-12T09:00:00Z" },
    { id: "2", title: "Yesterday chat", updatedAt: "2026-07-11T09:00:00Z" },
    { id: "3", title: "This week chat", updatedAt: "2026-07-08T09:00:00Z" },
    { id: "4", title: "Old chat", updatedAt: "2026-05-01T09:00:00Z" },
  ];

  it("groups chats into Hoy / Ayer / Esta semana / Anteriores", () => {
    const groups = groupChatsByDate(chats, now);
    const labels = groups.map((g) => g.label);
    expect(labels).toEqual(["Hoy", "Ayer", "Esta semana", "Anteriores"]);
    expect(groups[0].chats).toHaveLength(1);
    expect(groups[0].chats[0].title).toBe("Today chat");
  });

  it("omits empty groups", () => {
    const groups = groupChatsByDate([chats[0]], now);
    expect(groups).toHaveLength(1);
    expect(groups[0].label).toBe("Hoy");
  });

  it("returns no groups for an empty list", () => {
    expect(groupChatsByDate([], now)).toEqual([]);
  });
});
