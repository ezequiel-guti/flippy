import { render, screen } from "@testing-library/react";
import ChatMessage from "./ChatMessage";
import type { ChatMessageData } from "@/types/chat";

describe("ChatMessage", () => {
  it("renders a user message", () => {
    const message: ChatMessageData = {
      id: "1",
      role: "user",
      content: "Hola Flippy",
      createdAt: "2026-07-10T00:00:00Z",
    };
    render(<ChatMessage message={message} />);
    expect(screen.getByText("Hola Flippy")).toBeInTheDocument();
    expect(screen.getByLabelText("Tu mensaje")).toBeInTheDocument();
  });

  it("renders an assistant message", () => {
    const message: ChatMessageData = {
      id: "2",
      role: "assistant",
      content: "Hola, ¿en qué te ayudo?",
      createdAt: "2026-07-10T00:00:00Z",
    };
    render(<ChatMessage message={message} />);
    expect(screen.getByLabelText("Respuesta de Flippy")).toBeInTheDocument();
  });
});
