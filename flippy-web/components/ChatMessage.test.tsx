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

  it("shows a spinner instead of an empty paragraph for a pending assistant reply", () => {
    const message: ChatMessageData = {
      id: "3",
      role: "assistant",
      content: "",
      createdAt: "2026-07-10T00:00:00Z",
    };
    render(<ChatMessage message={message} />);
    const bubble = screen.getByLabelText("Respuesta de Flippy");
    expect(bubble.querySelector("p")).not.toBeInTheDocument();
    expect(bubble.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
  });
});
