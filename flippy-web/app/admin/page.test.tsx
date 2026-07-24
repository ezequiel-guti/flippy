import { render, screen, waitFor } from "@testing-library/react";
import AdminPage from "./page";

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function mockFetchByUrl(responses: Record<string, { ok: boolean; status: number; json?: () => Promise<unknown> }>) {
  global.fetch = jest.fn((input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input.toString();
    const match = Object.keys(responses).find((key) => url.includes(key));
    const response = match ? responses[match] : { ok: false, status: 404, json: async () => [] };
    return Promise.resolve(response as Response);
  }) as jest.Mock;
}

describe("AdminPage", () => {
  beforeEach(() => {
    pushMock.mockClear();
  });

  it("renders the document list on successful load", async () => {
    mockFetchByUrl({
      "/admin/folders": { ok: true, status: 200, json: async () => [] },
      "/admin/documents": {
        ok: true,
        status: 200,
        json: async () => [
          {
            id: "1",
            name: "manual.pdf",
            type: "pdf",
            status: "ready",
            chunk_count: 5,
            folder_id: null,
            created_at: "2026-07-13T00:00:00Z",
          },
        ],
      },
    });

    render(<AdminPage />);

    await waitFor(() => expect(screen.getByText("manual.pdf")).toBeInTheDocument());
  });

  it("redirects to /login on 403", async () => {
    mockFetchByUrl({
      "/admin/folders": { ok: true, status: 200, json: async () => [] },
      "/admin/documents": { ok: false, status: 403 },
    });

    render(<AdminPage />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });

  it("shows an error message when loading fails for another reason", async () => {
    mockFetchByUrl({
      "/admin/folders": { ok: true, status: 200, json: async () => [] },
      "/admin/documents": { ok: false, status: 500 },
    });

    render(<AdminPage />);

    await waitFor(() => expect(screen.getByText(/no pudimos cargar los documentos/i)).toBeInTheDocument());
  });
});
