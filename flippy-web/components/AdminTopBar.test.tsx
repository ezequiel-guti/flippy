import { render, screen } from "@testing-library/react";
import AdminTopBar from "./AdminTopBar";

describe("AdminTopBar", () => {
  it("shows 'Documentos' as the name and a default status when no folder is open", () => {
    render(<AdminTopBar />);
    expect(screen.getByText("Documentos")).toBeInTheDocument();
    expect(screen.getByText("Panel de administración")).toBeInTheDocument();
  });

  it("shows the current folder name in the status line", () => {
    render(<AdminTopBar currentFolderName="Presupuestos" />);
    expect(screen.getByText("Documentos")).toBeInTheDocument();
    expect(screen.getByText("Carpeta: Presupuestos")).toBeInTheDocument();
  });
});
