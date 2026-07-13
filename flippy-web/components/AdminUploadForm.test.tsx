import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AdminUploadForm from "./AdminUploadForm";

describe("AdminUploadForm", () => {
  it("calls onUpload with the selected file", async () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(<AdminUploadForm onUpload={onUpload} />);

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/subir documento al corpus/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByText("Subir"));

    await waitFor(() => expect(onUpload).toHaveBeenCalledWith(file));
  });

  it("shows an error message when the upload fails", async () => {
    const onUpload = jest.fn().mockRejectedValue(new Error("fail"));
    render(<AdminUploadForm onUpload={onUpload} />);

    const file = new File(["contenido"], "documento.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/subir documento al corpus/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByText("Subir"));

    await waitFor(() => expect(screen.getByText(/no pudimos subir el archivo/i)).toBeInTheDocument());
  });
});
