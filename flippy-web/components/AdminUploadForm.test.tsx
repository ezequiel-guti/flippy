import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AdminUploadForm from "./AdminUploadForm";

function openPanel() {
  fireEvent.click(screen.getByText("Subir archivo"));
}

function selectFiles(files: File[]) {
  const input = screen.getByLabelText(/subir documentos al corpus/i) as HTMLInputElement;
  fireEvent.change(input, { target: { files } });
}

describe("AdminUploadForm", () => {
  it("queues a selected file and uploads it only when the process button is clicked", async () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    selectFiles([file]);

    expect(screen.getByText("documento.txt")).toBeInTheDocument();
    expect(onUpload).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText("Subir 1 archivo"));
    await waitFor(() => expect(onUpload).toHaveBeenCalledWith(file));
  });

  it("queues and uploads multiple files at once", async () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file1 = new File(["a"], "uno.txt", { type: "text/plain" });
    const file2 = new File(["b"], "dos.txt", { type: "text/plain" });
    selectFiles([file1, file2]);

    expect(screen.getByText("uno.txt")).toBeInTheDocument();
    expect(screen.getByText("dos.txt")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Subir 2 archivos"));

    await waitFor(() => expect(onUpload).toHaveBeenCalledTimes(2));
    expect(onUpload).toHaveBeenCalledWith(file1);
    expect(onUpload).toHaveBeenCalledWith(file2);
  });

  it("allows removing a queued file before uploading", async () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file1 = new File(["a"], "uno.txt", { type: "text/plain" });
    const file2 = new File(["b"], "dos.txt", { type: "text/plain" });
    selectFiles([file1, file2]);

    fireEvent.click(screen.getByLabelText("Quitar uno.txt"));
    expect(screen.queryByText("uno.txt")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Subir 1 archivo"));
    await waitFor(() => expect(onUpload).toHaveBeenCalledTimes(1));
    expect(onUpload).toHaveBeenCalledWith(file2);
  });

  it("shows an error message when the upload fails", async () => {
    const onUpload = jest.fn().mockRejectedValue(new Error("fail"));
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    selectFiles([file]);
    fireEvent.click(screen.getByText("Subir 1 archivo"));

    await waitFor(() => expect(screen.getByText(/no pudimos subir/i)).toBeInTheDocument());
  });

  it("warns and blocks queuing when the file name already exists", () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} existingNames={["documento.txt"]} />);
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    selectFiles([file]);

    expect(screen.getByText(/ya existe un archivo/i)).toBeInTheDocument();
    expect(screen.queryByText(/subir \d archivo/i)).not.toBeInTheDocument();
    expect(onUpload).not.toHaveBeenCalled();
  });

  it("closes the panel via the close button", () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    const onPanelOpenChange = jest.fn();
    render(<AdminUploadForm onUpload={onUpload} onPanelOpenChange={onPanelOpenChange} />);
    openPanel();

    expect(screen.getByText("Subir archivos")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Cerrar subida de archivos"));

    expect(screen.queryByText("Subir archivos")).not.toBeInTheDocument();
    expect(onPanelOpenChange).toHaveBeenLastCalledWith(false);
  });

  it("closes the panel and clears the queue when navigating to a different folder", () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    const onPanelOpenChange = jest.fn();
    const { rerender } = render(
      <AdminUploadForm onUpload={onUpload} onPanelOpenChange={onPanelOpenChange} currentFolderId={null} />
    );
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    selectFiles([file]);
    expect(screen.getByText("documento.txt")).toBeInTheDocument();

    rerender(<AdminUploadForm onUpload={onUpload} onPanelOpenChange={onPanelOpenChange} currentFolderId="f1" />);

    expect(screen.queryByText("Subir archivos")).not.toBeInTheDocument();
    expect(screen.queryByText("documento.txt")).not.toBeInTheDocument();
    expect(onPanelOpenChange).toHaveBeenLastCalledWith(false);
  });

  it("shows the folder path as a breadcrumb and navigates on click", () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    const onNavigate = jest.fn();
    const folders = [
      { id: "f1", name: "Presupuestos", parent_id: null, created_at: "", updated_at: "" },
      { id: "f2", name: "2026", parent_id: "f1", created_at: "", updated_at: "" },
    ];
    render(
      <AdminUploadForm
        onUpload={onUpload}
        folders={folders}
        currentFolderId="f2"
        onNavigate={onNavigate}
      />
    );

    expect(screen.getByText("Raíz")).toBeInTheDocument();
    expect(screen.getByText("Presupuestos")).toBeInTheDocument();
    expect(screen.getByText("2026")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Presupuestos"));
    expect(onNavigate).toHaveBeenCalledWith("f1");
  });
});
