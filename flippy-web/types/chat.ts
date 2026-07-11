export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  imageUrl?: string;
  createdAt: string;
}

export interface ChatSummary {
  id: string;
  title: string;
  updatedAt: string;
}
