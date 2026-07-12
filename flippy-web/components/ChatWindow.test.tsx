import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatWindow from "./ChatWindow";
import type { ChatMessageData } from "@/types/chat";

describe("ChatWindow", () => {
  it("shows a greeting when there are no messages", () => {
    render(<ChatWindow initialMessages={[]} onOpenHistory={jest.fn()} />);
    expect(screen.getByText(/hola, soy flippy/i)).toBeInTheDocument();
  });

  it("renders initial messages", () => {
    const messages: ChatMessageData[] = [
      { id: "1", role: "user", content: "Hola", createdAt: "2026-07-10T00:00:00Z" },
    ];
    render(<ChatWindow initialMessages={messages} onOpenHistory={jest.fn()} />);
    expect(screen.getByText("Hola")).toBeInTheDocument();
  });

  it("appends the user message and a mock reply on send", async () => {
    render(<ChatWindow initialMessages={[]} onOpenHistory={jest.fn()} />);

    const input = screen.getByLabelText(/escribí tu consulta/i);
    fireEvent.change(input, { target: { value: "Consulta de prueba" } });
    fireEvent.click(screen.getByLabelText("Enviar"));

    expect(screen.getByText("Consulta de prueba")).toBeInTheDocument();
    expect(screen.getByText(/flippy está escribiendo/i)).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.getByText(/integración con el backend rag llega en el hito 2/i)).toBeInTheDocument()
    );
  });

  it("calls onOpenHistory when the history button is clicked", () => {
    const onOpenHistory = jest.fn();
    render(<ChatWindow initialMessages={[]} onOpenHistory={onOpenHistory} />);
    fireEvent.click(screen.getByLabelText("Ver historial de chats"));
    expect(onOpenHistory).toHaveBeenCalledTimes(1);
  });
});
