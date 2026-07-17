import { render, screen, fireEvent } from "@testing-library/react";
import ChatSidebar from "./ChatSidebar";
import type { ChatSummary } from "@/types/chat";

const chats: ChatSummary[] = [
  { id: "1", title: "Chat uno", updatedAt: "2026-07-10T00:00:00Z" },
  { id: "2", title: "Chat dos", updatedAt: "2026-07-09T00:00:00Z" },
];

describe("ChatSidebar", () => {
  it("renders the chat list", () => {
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    expect(screen.getByText("Chat uno")).toBeInTheDocument();
    expect(screen.getByText("Chat dos")).toBeInTheDocument();
  });

  it("shows an empty state when there are no chats", () => {
    render(
      <ChatSidebar
        chats={[]}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    expect(screen.getByText(/todavía no tenés conversaciones/i)).toBeInTheDocument();
  });

  it("calls onNewChat when the button is clicked", () => {
    const onNewChat = jest.fn();
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={onNewChat}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    fireEvent.click(screen.getByText("Nuevo chat"));
    expect(onNewChat).toHaveBeenCalledTimes(1);
  });

  it("calls onSelectChat with the chat id when a chat is clicked", () => {
    const onSelectChat = jest.fn();
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={onSelectChat}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    fireEvent.click(screen.getByText("Chat dos"));
    expect(onSelectChat).toHaveBeenCalledWith("2");
  });

  it("filters chats by search query", () => {
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    fireEvent.change(screen.getByLabelText("Buscar en tus chats"), { target: { value: "dos" } });
    expect(screen.getByText("Chat dos")).toBeInTheDocument();
    expect(screen.queryByText("Chat uno")).not.toBeInTheDocument();
  });

  it("shows the user's name and membership label in the footer", () => {
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    expect(screen.getByText("Virgilio")).toBeInTheDocument();
    expect(screen.getByText(/socio · flipping master/i)).toBeInTheDocument();
  });

  it("opens a confirmation modal and calls onDeleteChat on confirm", () => {
    const onDeleteChat = jest.fn();
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={onDeleteChat}
      />
    );
    fireEvent.click(screen.getAllByLabelText("Opciones del chat")[0]);
    fireEvent.click(screen.getByText("Eliminar"));
    expect(screen.getByText(/¿eliminar este chat\?/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Eliminar"));
    expect(onDeleteChat).toHaveBeenCalledWith("1");
  });

  it("cancels deletion without calling onDeleteChat", () => {
    const onDeleteChat = jest.fn();
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={onDeleteChat}
      />
    );
    fireEvent.click(screen.getAllByLabelText("Opciones del chat")[0]);
    fireEvent.click(screen.getByText("Eliminar"));
    fireEvent.click(screen.getByText("Cancelar"));
    expect(onDeleteChat).not.toHaveBeenCalled();
  });

  it("renames a chat via the kebab menu", () => {
    const onRenameChat = jest.fn();
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={onRenameChat}
        onDeleteChat={jest.fn()}
      />
    );
    fireEvent.click(screen.getAllByLabelText("Opciones del chat")[0]);
    fireEvent.click(screen.getByText("Renombrar"));
    const input = screen.getByLabelText("Renombrar chat");
    fireEvent.change(input, { target: { value: "Nuevo título" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onRenameChat).toHaveBeenCalledWith("1", "Nuevo título");
  });

  it("closes the kebab menu when clicking outside of it", () => {
    render(
      <ChatSidebar
        chats={chats}
        userName="Virgilio"
        onSelectChat={jest.fn()}
        onNewChat={jest.fn()}
        onRenameChat={jest.fn()}
        onDeleteChat={jest.fn()}
      />
    );
    fireEvent.click(screen.getAllByLabelText("Opciones del chat")[0]);
    expect(screen.getByText("Renombrar")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);
    expect(screen.queryByText("Renombrar")).not.toBeInTheDocument();
  });
});
