import { render, screen, fireEvent } from "@testing-library/react";
import ChatSidebar from "./ChatSidebar";
import type { ChatSummary } from "@/types/chat";

const chats: ChatSummary[] = [
  { id: "1", title: "Chat uno", updatedAt: "2026-07-10T00:00:00Z" },
  { id: "2", title: "Chat dos", updatedAt: "2026-07-09T00:00:00Z" },
];

describe("ChatSidebar", () => {
  it("renders the chat list", () => {
    render(<ChatSidebar chats={chats} userName="Virgilio" onSelectChat={jest.fn()} onNewChat={jest.fn()} />);
    expect(screen.getByText("Chat uno")).toBeInTheDocument();
    expect(screen.getByText("Chat dos")).toBeInTheDocument();
  });

  it("shows an empty state when there are no chats", () => {
    render(<ChatSidebar chats={[]} userName="Virgilio" onSelectChat={jest.fn()} onNewChat={jest.fn()} />);
    expect(screen.getByText(/todavía no tenés conversaciones/i)).toBeInTheDocument();
  });

  it("calls onNewChat when the button is clicked", () => {
    const onNewChat = jest.fn();
    render(<ChatSidebar chats={chats} userName="Virgilio" onSelectChat={jest.fn()} onNewChat={onNewChat} />);
    fireEvent.click(screen.getByText("Nuevo chat"));
    expect(onNewChat).toHaveBeenCalledTimes(1);
  });

  it("calls onSelectChat with the chat id when a chat is clicked", () => {
    const onSelectChat = jest.fn();
    render(<ChatSidebar chats={chats} userName="Virgilio" onSelectChat={onSelectChat} onNewChat={jest.fn()} />);
    fireEvent.click(screen.getByText("Chat dos"));
    expect(onSelectChat).toHaveBeenCalledWith("2");
  });

  it("filters chats by search query", () => {
    render(<ChatSidebar chats={chats} userName="Virgilio" onSelectChat={jest.fn()} onNewChat={jest.fn()} />);
    fireEvent.change(screen.getByLabelText("Buscar en tus chats"), { target: { value: "dos" } });
    expect(screen.getByText("Chat dos")).toBeInTheDocument();
    expect(screen.queryByText("Chat uno")).not.toBeInTheDocument();
  });

  it("shows the user's name and membership label in the footer", () => {
    render(<ChatSidebar chats={chats} userName="Virgilio" onSelectChat={jest.fn()} onNewChat={jest.fn()} />);
    expect(screen.getByText("Virgilio")).toBeInTheDocument();
    expect(screen.getByText(/socio · flipping master/i)).toBeInTheDocument();
  });
});
