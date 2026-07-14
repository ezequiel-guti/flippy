import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatWindow from "./ChatWindow";
import type { ChatMessageData } from "@/types/chat";
import { apiStream } from "../services/api";

jest.mock("../services/api", () => ({
  apiStream: jest.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

function sseStreamFrom(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text: chunk })}\n\n`));
      }
      controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      controller.close();
    },
  });
}

describe("ChatWindow", () => {
  beforeEach(() => {
    (apiStream as jest.Mock).mockReset();
  });

  it("shows a greeting when there are no messages", () => {
    render(<ChatWindow chatId="chat-1" initialMessages={[]} onOpenHistory={jest.fn()} />);
    expect(screen.getByText(/hola, soy flippy/i)).toBeInTheDocument();
  });

  it("renders initial messages", () => {
    const messages: ChatMessageData[] = [
      { id: "1", role: "user", content: "Hola", createdAt: "2026-07-10T00:00:00Z" },
    ];
    render(<ChatWindow chatId="chat-1" initialMessages={messages} onOpenHistory={jest.fn()} />);
    expect(screen.getByText("Hola")).toBeInTheDocument();
  });

  it("streams the assistant reply and calls onMessageSent", async () => {
    (apiStream as jest.Mock).mockResolvedValue(sseStreamFrom(["Hola ", "mundo"]));
    const onMessageSent = jest.fn();
    render(<ChatWindow chatId="chat-1" initialMessages={[]} onOpenHistory={jest.fn()} onMessageSent={onMessageSent} />);

    const input = screen.getByLabelText(/escribí tu consulta/i);
    fireEvent.change(input, { target: { value: "Consulta de prueba" } });
    fireEvent.click(screen.getByLabelText("Enviar"));

    expect(screen.getByText("Consulta de prueba")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("Hola mundo")).toBeInTheDocument());
    expect(apiStream).toHaveBeenCalledWith("/api/v1/chats/chat-1/messages", { content: "Consulta de prueba" });
    expect(onMessageSent).toHaveBeenCalled();
  });

  it("calls onOpenHistory when the history button is clicked", () => {
    const onOpenHistory = jest.fn();
    render(<ChatWindow chatId="chat-1" initialMessages={[]} onOpenHistory={onOpenHistory} />);
    fireEvent.click(screen.getByLabelText("Ver historial de chats"));
    expect(onOpenHistory).toHaveBeenCalledTimes(1);
  });
});
