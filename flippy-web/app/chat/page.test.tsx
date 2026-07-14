import { render, screen, waitFor } from "@testing-library/react";
import ChatPage from "./page";
import { apiGet, apiPost } from "../../services/api";

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

jest.mock("../../services/api", () => ({
  apiGet: jest.fn(),
  apiPost: jest.fn(),
  apiStream: jest.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

describe("ChatPage", () => {
  beforeEach(() => {
    pushMock.mockClear();
    (apiGet as jest.Mock).mockReset();
    (apiPost as jest.Mock).mockReset();
  });

  it("loads the user's chats and selects the first one", async () => {
    (apiGet as jest.Mock).mockImplementation((path: string) => {
      if (path === "/api/v1/auth/me") return Promise.resolve({ email: "virgilio@example.com" });
      if (path === "/api/v1/chats") {
        return Promise.resolve([{ id: "c1", title: "Requisitos para escritura", updated_at: "2026-07-10T00:00:00Z" }]);
      }
      if (path === "/api/v1/chats/c1/messages") return Promise.resolve([]);
      throw new Error(`unexpected path ${path}`);
    });

    render(<ChatPage />);

    await waitFor(() => expect(screen.getByText("Requisitos para escritura")).toBeInTheDocument());
    expect(screen.getByText("virgilio")).toBeInTheDocument();
  });

  it("creates a chat when the user has none yet", async () => {
    (apiGet as jest.Mock).mockImplementation((path: string) => {
      if (path === "/api/v1/auth/me") return Promise.resolve({ email: "virgilio@example.com" });
      if (path === "/api/v1/chats") return Promise.resolve([]);
      if (path === "/api/v1/chats/new-1/messages") return Promise.resolve([]);
      throw new Error(`unexpected path ${path}`);
    });
    (apiPost as jest.Mock).mockResolvedValue({ id: "new-1", title: "Nuevo chat", updated_at: "2026-07-10T00:00:00Z" });

    render(<ChatPage />);

    await waitFor(() => expect(apiPost).toHaveBeenCalledWith("/api/v1/chats", {}));
  });

  it("redirects to /login when loading chats fails with 401", async () => {
    const { ApiError } = jest.requireMock("../../services/api");
    (apiGet as jest.Mock).mockRejectedValue(new ApiError(401, "unauthorized"));

    render(<ChatPage />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });
});
