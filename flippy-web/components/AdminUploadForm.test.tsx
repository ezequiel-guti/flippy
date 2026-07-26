import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AdminUploadForm from "./AdminUploadForm";

function openPanel() {
  fireEvent.click(screen.getByText("Subir archivo"));
}

describe("AdminUploadForm", () => {
  it("uploads the file as soon as it's selected", async () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/subir documentos al corpus/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(onUpload).toHaveBeenCalledWith(file));
  });

  it("uploads multiple files selected at once", async () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file1 = new File(["a"], "uno.txt", { type: "text/plain" });
    const file2 = new File(["b"], "dos.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/subir documentos al corpus/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file1, file2] } });

    await waitFor(() => expect(onUpload).toHaveBeenCalledTimes(2));
    expect(onUpload).toHaveBeenCalledWith(file1);
    expect(onUpload).toHaveBeenCalledWith(file2);
  });

  it("shows an error message when the upload fails", async () => {
    const onUpload = jest.fn().mockRejectedValue(new Error("fail"));
    render(<AdminUploadForm onUpload={onUpload} />);
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/subir documentos al corpus/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(screen.getByText(/no pudimos subir/i)).toBeInTheDocument());
  });

  it("warns and blocks upload when the file name already exists", () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} existingNames={["documento.txt"]} />);
    openPanel();

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/subir documentos al corpus/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/ya existe un archivo/i)).toBeInTheDocument();
    expect(onUpload).not.toHaveBeenCalled();
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
