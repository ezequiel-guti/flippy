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
    render(<AdminDocumentTable documents={[]} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    expect(screen.getByText(/todavía no hay documentos/i)).toBeInTheDocument();
  });

  it("renders document rows with status labels", () => {
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    expect(screen.getByText("manual.pdf")).toBeInTheDocument();
    expect(screen.getByText("Listo")).toBeInTheDocument();
    expect(screen.getByText("Procesando")).toBeInTheDocument();
  });

  it("calls onDelete with the document id", () => {
    const onDelete = jest.fn();
    render(<AdminDocumentTable documents={documents} onDelete={onDelete} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    fireEvent.click(screen.getAllByText("Eliminar")[0]);
    expect(onDelete).toHaveBeenCalledWith("1");
  });

  it("calls onDownload with the document id", () => {
    const onDownload = jest.fn();
    render(
      <AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={onDownload} />
    );
    fireEvent.click(screen.getByLabelText(/descargar manual.pdf/i));
    expect(onDownload).toHaveBeenCalledWith("1");
  });

  it("calls onReprocess with the document id", () => {
    const onReprocess = jest.fn();
    render(
      <AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={onReprocess} onDownload={jest.fn()} />
    );
    fireEvent.click(screen.getByLabelText(/reprocesar manual.pdf/i));
    expect(onReprocess).toHaveBeenCalledWith("1");
  });

  it("enables reprocess for a document stuck processing for over 10 minutes", () => {
    const stuck: DocumentSummary[] = [
      {
        id: "5",
        name: "atascado.pdf",
        type: "pdf",
        status: "processing",
        chunk_count: 0,
        folder_id: null,
        created_at: "2026-08-03T00:00:00Z",
        processing_started_at: new Date(Date.now() - 11 * 60 * 1000).toISOString(),
      },
    ];
    render(<AdminDocumentTable documents={stuck} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    const button = screen.getByLabelText(/reprocesar atascado.pdf/i);
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute("title", "Lleva más de 10 minutos procesando");
  });

  it("keeps reprocess disabled for a document processing for under 10 minutes", () => {
    const recent: DocumentSummary[] = [
      {
        id: "6",
        name: "reciente.pdf",
        type: "pdf",
        status: "processing",
        chunk_count: 0,
        folder_id: null,
        created_at: "2026-08-03T00:00:00Z",
        processing_started_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
      },
    ];
    render(<AdminDocumentTable documents={recent} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    expect(screen.getByLabelText(/reprocesar reciente.pdf/i)).toBeDisabled();
  });

  it("shows error_detail as a tooltip on the Error badge", () => {
    const withError: DocumentSummary[] = [
      {
        id: "4",
        name: "roto.pdf",
        type: "pdf",
        status: "error",
        chunk_count: 0,
        folder_id: null,
        created_at: "2026-08-02T00:00:00Z",
        error_detail: "Timeout llamando a OpenAI",
      },
    ];
    render(<AdminDocumentTable documents={withError} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    expect(screen.getByText("Error")).toHaveAttribute("title", "Timeout llamando a OpenAI");
  });

  it("disables the reprocess button while the document is processing", () => {
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
    expect(screen.getByLabelText(/reprocesar notas.txt/i)).toBeDisabled();
    expect(screen.getByLabelText(/reprocesar manual.pdf/i)).not.toBeDisabled();
  });

  it("shows a spinner and disables the button while reprocessing is in flight", () => {
    render(
      <AdminDocumentTable
        documents={documents}
        onDelete={jest.fn()}
        onReprocess={jest.fn()} onDownload={jest.fn()}
        reprocessingIds={new Set(["1"])}
      />
    );
    const button = screen.getByLabelText(/reprocesar manual.pdf/i);
    expect(button).toBeDisabled();
    expect(button.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
  });

  it("filters documents by name", () => {
    render(<AdminDocumentTable documents={documents} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);
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
    render(<AdminDocumentTable documents={manyDocuments} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} />);

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
        onReprocess={jest.fn()} onDownload={jest.fn()}
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
        onReprocess={jest.fn()} onDownload={jest.fn()}
        searchScope={[...documents, inAnotherFolder]}
      />
    );

    expect(screen.queryByText("presupuesto-cocina.pdf")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/buscar documentos por nombre/i), { target: { value: "presupuesto" } });
    expect(screen.getByText("presupuesto-cocina.pdf")).toBeInTheDocument();
    expect(screen.getByText(/buscando en todo el corpus/i)).toBeInTheDocument();
  });

  it("shows the search box even when the current folder is empty, if there's a search scope", () => {
    render(<AdminDocumentTable documents={[]} onDelete={jest.fn()} onReprocess={jest.fn()} onDownload={jest.fn()} searchScope={documents} />);
    expect(screen.getByLabelText(/buscar documentos por nombre/i)).toBeInTheDocument();
    expect(screen.getByText(/esta carpeta no tiene documentos/i)).toBeInTheDocument();
  });
});
