import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatWindow from "./ChatWindow";
import type { ChatMessageData } from "@/types/chat";
import { apiStream, apiStreamUpload } from "../services/api";

jest.mock("../services/api", () => ({
  apiStream: jest.fn(),
  apiStreamUpload: jest.fn(),
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
    (apiStreamUpload as jest.Mock).mockReset();
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

  it("sends an attached image via apiStreamUpload and streams the analysis", async () => {
    URL.createObjectURL = jest.fn(() => "blob:mock-url");
    (apiStreamUpload as jest.Mock).mockResolvedValue(sseStreamFrom(["Parece ", "una cocina remodelada"]));
    render(<ChatWindow chatId="chat-1" initialMessages={[]} onOpenHistory={jest.fn()} />);

    const file = new File(["fake-image-bytes"], "cocina.png", { type: "image/png" });
    const fileInput = screen.getByLabelText("Seleccionar imagen para adjuntar");
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText(/escribí tu consulta/i), { target: { value: "¿Qué opinas?" } });
    fireEvent.click(screen.getByLabelText("Enviar"));

    await waitFor(() => expect(screen.getByText("Parece una cocina remodelada")).toBeInTheDocument());
    expect(apiStreamUpload).toHaveBeenCalledWith("/api/v1/chats/chat-1/messages/image", file, {
      content: "¿Qué opinas?",
    });
    expect(apiStream).not.toHaveBeenCalled();
  });

  it("calls onOpenHistory when the history button is clicked", () => {
    const onOpenHistory = jest.fn();
    render(<ChatWindow chatId="chat-1" initialMessages={[]} onOpenHistory={onOpenHistory} />);
    fireEvent.click(screen.getByLabelText("Ver historial de chats"));
    expect(onOpenHistory).toHaveBeenCalledTimes(1);
  });

  it("shows a spinner in the assistant bubble before the first streamed chunk arrives", async () => {
    let pushChunk: (chunk: string) => void = () => {};
    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        pushChunk = (chunk: string) => controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text: chunk })}\n\n`));
      },
    });
    (apiStream as jest.Mock).mockResolvedValue(stream);
    render(<ChatWindow chatId="chat-1" initialMessages={[]} onOpenHistory={jest.fn()} />);

    fireEvent.change(screen.getByLabelText(/escribí tu consulta/i), { target: { value: "Hola" } });
    fireEvent.click(screen.getByLabelText("Enviar"));

    const assistantBubble = await waitFor(() => screen.getByLabelText("Respuesta de Flippy"));
    expect(assistantBubble.querySelector('[aria-hidden="true"]')).toBeInTheDocument();

    pushChunk("Hola de vuelta");
    await waitFor(() => expect(screen.getByText("Hola de vuelta")).toBeInTheDocument());
    expect(assistantBubble.querySelector('[aria-hidden="true"]')).not.toBeInTheDocument();
  });

  it("shows a loading spinner instead of messages while isLoadingMessages is true", () => {
    render(<ChatWindow chatId="chat-1" initialMessages={[]} isLoadingMessages onOpenHistory={jest.fn()} />);
    expect(screen.getByText(/cargando mensajes/i)).toBeInTheDocument();
    expect(screen.queryByText(/hola, soy flippy/i)).not.toBeInTheDocument();
  });
});
