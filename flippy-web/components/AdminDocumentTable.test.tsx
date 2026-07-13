import { render, screen, fireEvent } from "@testing-library/react";
import AdminDocumentTable from "./AdminDocumentTable";
import type { DocumentSummary } from "@/types/document";

const documents: DocumentSummary[] = [
  { id: "1", name: "manual.pdf", type: "pdf", status: "ready", chunk_count: 12, created_at: "2026-07-13T00:00:00Z" },
  { id: "2", name: "notas.txt", type: "txt", status: "processing", chunk_count: 0, created_at: "2026-07-13T00:00:00Z" },
];

describe("AdminDocumentTable", () => {
  it("shows an empty state when there are no documents", () => {
    render(<AdminDocumentTable documents={[]} onDelete={jest.fn()} />);
    expect(screen.getByText(/todavía no hay documentos/i)).toBeInTheDocument();
  });

  it("renders document rows with status labels", () => {
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} />);
    expect(screen.getByText("manual.pdf")).toBeInTheDocument();
    expect(screen.getByText("Listo")).toBeInTheDocument();
    expect(screen.getByText("Procesando")).toBeInTheDocument();
  });

  it("calls onDelete with the document id", () => {
    const onDelete = jest.fn();
    render(<AdminDocumentTable documents={documents} onDelete={onDelete} />);
    fireEvent.click(screen.getAllByText("Eliminar")[0]);
    expect(onDelete).toHaveBeenCalledWith("1");
  });
});
