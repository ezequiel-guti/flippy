import { render, screen, fireEvent } from "@testing-library/react";
import AdminDocumentTable from "./AdminDocumentTable";
import type { DocumentSummary } from "@/types/document";
import type { DocumentFolder } from "@/types/folder";

const documents: DocumentSummary[] = [
  {
    id: "1",
    name: "manual.pdf",
    type: "pdf",
    status: "ready",
    chunk_count: 12,
    folder_id: null,
    created_at: "2026-07-13T00:00:00Z",
  },
  {
    id: "2",
    name: "notas.txt",
    type: "txt",
    status: "processing",
    chunk_count: 0,
    folder_id: null,
    created_at: "2026-07-13T00:00:00Z",
  },
];

describe("AdminDocumentTable", () => {
  it("shows an empty state when there are no documents", () => {
    render(<AdminDocumentTable documents={[]} onDelete={jest.fn()} onReprocess={jest.fn()} />);
    expect(screen.getByText(/todavía no hay documentos/i)).toBeInTheDocument();
  });

  it("renders document rows with status labels", () => {
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={jest.fn()} />);
    expect(screen.getByText("manual.pdf")).toBeInTheDocument();
    expect(screen.getByText("Listo")).toBeInTheDocument();
    expect(screen.getByText("Procesando")).toBeInTheDocument();
  });

  it("calls onDelete with the document id", () => {
    const onDelete = jest.fn();
    render(<AdminDocumentTable documents={documents} onDelete={onDelete} onReprocess={jest.fn()} />);
    fireEvent.click(screen.getAllByText("Eliminar")[0]);
    expect(onDelete).toHaveBeenCalledWith("1");
  });

  it("calls onReprocess with the document id", () => {
    const onReprocess = jest.fn();
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={onReprocess} />);
    fireEvent.click(screen.getByLabelText(/reprocesar manual.pdf/i));
    expect(onReprocess).toHaveBeenCalledWith("1");
  });

  it("filters documents by name", () => {
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={jest.fn()} />);
    fireEvent.change(screen.getByLabelText(/buscar documentos por nombre/i), { target: { value: "notas" } });
    expect(screen.getByText("notas.txt")).toBeInTheDocument();
    expect(screen.queryByText("manual.pdf")).not.toBeInTheDocument();
  });

  it("paginates results according to the selected page size", () => {
    const manyDocuments: DocumentSummary[] = Array.from({ length: 12 }, (_, i) => ({
      id: String(i),
      name: `doc-${i}.txt`,
      type: "txt",
      status: "ready",
      chunk_count: 1,
      folder_id: null,
      created_at: "2026-07-13T00:00:00Z",
    }));
    render(<AdminDocumentTable documents={manyDocuments} onDelete={jest.fn()} onReprocess={jest.fn()} />);

    expect(screen.getByText("doc-0.txt")).toBeInTheDocument();
    expect(screen.queryByText("doc-10.txt")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("2"));
    expect(screen.getByText("doc-10.txt")).toBeInTheDocument();
    expect(screen.queryByText("doc-0.txt")).not.toBeInTheDocument();
  });

  it("shows a folder column with move select when onMove is provided", () => {
    const folders: DocumentFolder[] = [
      { id: "f1", name: "Presupuestos", parent_id: null, created_at: "2026-07-24T00:00:00Z", updated_at: "2026-07-24T00:00:00Z" },
    ];
    const onMove = jest.fn();
    render(
      <AdminDocumentTable
        documents={documents}
        onDelete={jest.fn()}
        onReprocess={jest.fn()}
        folders={folders}
        onMove={onMove}
      />
    );

    const select = screen.getByLabelText(/mover manual.pdf/i);
    fireEvent.change(select, { target: { value: "f1" } });
    expect(onMove).toHaveBeenCalledWith("1", "f1");
  });

  it("searches across the whole corpus when searchScope is provided", () => {
    const inAnotherFolder: DocumentSummary = {
      id: "3",
      name: "presupuesto-cocina.pdf",
      type: "pdf",
      status: "ready",
      chunk_count: 4,
      folder_id: "f1",
      created_at: "2026-07-24T00:00:00Z",
    };
    render(
      <AdminDocumentTable
        documents={documents}
        onDelete={jest.fn()}
        onReprocess={jest.fn()}
        searchScope={[...documents, inAnotherFolder]}
      />
    );

    expect(screen.queryByText("presupuesto-cocina.pdf")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/buscar documentos por nombre/i), { target: { value: "presupuesto" } });
    expect(screen.getByText("presupuesto-cocina.pdf")).toBeInTheDocument();
    expect(screen.getByText(/buscando en todo el corpus/i)).toBeInTheDocument();
  });

  it("shows the search box even when the current folder is empty, if there's a search scope", () => {
    render(<AdminDocumentTable documents={[]} onDelete={jest.fn()} onReprocess={jest.fn()} searchScope={documents} />);
    expect(screen.getByLabelText(/buscar documentos por nombre/i)).toBeInTheDocument();
    expect(screen.getByText(/esta carpeta no tiene documentos/i)).toBeInTheDocument();
  });
});
