import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "./page";

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    pushMock.mockClear();
    localStorage.clear();
    global.fetch = jest.fn();
  });

  it("logs in successfully and redirects to /chat", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ access_token: "abc", refresh_token: "def", token_type: "bearer" }),
    });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password123" } });
    fireEvent.click(screen.getByText("Ingresar"));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/chat"));
    expect(localStorage.getItem("access_token")).toBe("abc");
  });

  it("shows an error message on invalid credentials", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false, status: 401 });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByText("Ingresar"));

    await waitFor(() => expect(screen.getByText(/email o contraseña incorrectos/i)).toBeInTheDocument());
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("switches to register mode and creates an account", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ access_token: "new-user-token", refresh_token: "def", token_type: "bearer" }),
    });

    render(<LoginPage />);
    fireEvent.click(screen.getByText("¿No tenés cuenta? Registrate"));
    expect(screen.getByText("Creá tu cuenta de socio")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "nuevo@example.com" } });
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password123" } });
    fireEvent.click(screen.getByText("Crear cuenta"));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/chat"));
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/register"),
      expect.objectContaining({ method: "POST" })
    );
    expect(localStorage.getItem("access_token")).toBe("new-user-token");
  });

  it("shows a specific error when the email is already registered", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false, status: 422 });

    render(<LoginPage />);
    fireEvent.click(screen.getByText("¿No tenés cuenta? Registrate"));
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ya@example.com" } });
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password123" } });
    fireEvent.click(screen.getByText("Crear cuenta"));

    await waitFor(() => expect(screen.getByText(/ese email ya está registrado/i)).toBeInTheDocument());
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("switches back to login mode", () => {
    render(<LoginPage />);
    fireEvent.click(screen.getByText("¿No tenés cuenta? Registrate"));
    fireEvent.click(screen.getByText("¿Ya tenés cuenta? Ingresá"));
    expect(screen.getByText("Ingresá con tu cuenta de socio")).toBeInTheDocument();
  });
});
