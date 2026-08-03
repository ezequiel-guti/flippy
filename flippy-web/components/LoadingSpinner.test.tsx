import { render, screen } from "@testing-library/react";
import LoadingSpinner from "./LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders the Flippy shield logo", () => {
    render(<LoadingSpinner />);
    const img = screen.getByRole("status").querySelector("img");
    expect(img).toHaveAttribute("src", expect.stringContaining("logo-shield"));
  });

  it("renders the label when provided", () => {
    render(<LoadingSpinner label="Cargando…" />);
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
  });

  it("omits the label when not provided", () => {
    render(<LoadingSpinner />);
    expect(screen.queryByText(/./)).not.toBeInTheDocument();
  });
});
