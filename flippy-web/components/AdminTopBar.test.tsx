import { render, screen } from "@testing-library/react";
import AdminTopBar from "./AdminTopBar";

describe("AdminTopBar", () => {
  it("shows 'Documentos' when no folder is open", () => {
    render(<AdminTopBar />);
    expect(screen.getByText("Documentos")).toBeInTheDocument();
  });

  it("shows the current folder name next to Documentos", () => {
    render(<AdminTopBar currentFolderName="Presupuestos" />);
    expect(screen.getByText("Documentos")).toBeInTheDocument();
    expect(screen.getByText("Presupuestos")).toBeInTheDocument();
  });
});
