import { render, screen, waitFor } from "@testing-library/react";
import AdminPage from "./page";

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

describe("AdminPage", () => {
  beforeEach(() => {
    pushMock.mockClear();
    global.fetch = jest.fn();
  });

  it("renders the document list on successful load", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [
        { id: "1", name: "manual.pdf", type: "pdf", status: "ready", chunk_count: 5, created_at: "2026-07-13T00:00:00Z" },
      ],
    });

    render(<AdminPage />);

    await waitFor(() => expect(screen.getByText("manual.pdf")).toBeInTheDocument());
  });

  it("redirects to /login on 403", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false, status: 403 });

    render(<AdminPage />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });

  it("shows an error message when loading fails for another reason", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false, status: 500 });

    render(<AdminPage />);

    await waitFor(() => expect(screen.getByText(/no pudimos cargar los documentos/i)).toBeInTheDocument());
  });
});
