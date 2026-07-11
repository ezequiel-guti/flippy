import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatWindow from "./ChatWindow";
import type { ChatMessageData } from "@/types/chat";

describe("ChatWindow", () => {
  it("shows an empty state when there are no messages", () => {
    render(<ChatWindow initialMessages={[]} />);
    expect(screen.getByText(/empezá la conversación/i)).toBeInTheDocument();
  });

  it("renders initial messages", () => {
    const messages: ChatMessageData[] = [
      { id: "1", role: "user", content: "Hola", createdAt: "2026-07-10T00:00:00Z" },
    ];
    render(<ChatWindow initialMessages={messages} />);
    expect(screen.getByText("Hola")).toBeInTheDocument();
  });

  it("appends the user message and a mock reply on send", async () => {
    render(<ChatWindow initialMessages={[]} />);

    const input = screen.getByLabelText(/escribí tu consulta/i);
    fireEvent.change(input, { target: { value: "Consulta de prueba" } });
    fireEvent.click(screen.getByText("Enviar"));

    expect(screen.getByText("Consulta de prueba")).toBeInTheDocument();
    expect(screen.getByText(/flippy está escribiendo/i)).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.getByText(/integración con el backend rag llega en el hito 2/i)).toBeInTheDocument()
    );
  });
});
