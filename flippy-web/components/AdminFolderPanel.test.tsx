import { render, screen, fireEvent } from "@testing-library/react";
import AdminFolderPanel from "./AdminFolderPanel";
import type { DocumentFolder } from "@/types/folder";

const folders: DocumentFolder[] = [
  { id: "f1", name: "Presupuestos", parent_id: null, created_at: "2026-07-24T00:00:00Z", updated_at: "2026-07-24T00:00:00Z" },
  { id: "f2", name: "2026", parent_id: "f1", created_at: "2026-07-24T00:00:00Z", updated_at: "2026-07-24T00:00:00Z" },
];

describe("AdminFolderPanel", () => {
  it("shows subfolders of the current folder only", () => {
    render(
      <AdminFolderPanel
        folders={folders}
        currentFolderId={null}
        onNavigate={jest.fn()}
        onCreate={jest.fn()}
        onRename={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    expect(screen.getByText("Presupuestos")).toBeInTheDocument();
    expect(screen.queryByText("2026")).not.toBeInTheDocument();
  });

  it("auto-expands the ancestry chain of the current folder", () => {
    render(
      <AdminFolderPanel
        folders={folders}
        currentFolderId="f2"
        onNavigate={jest.fn()}
        onCreate={jest.fn()}
        onRename={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    expect(screen.getByText("Raíz")).toBeInTheDocument();
    expect(screen.getByText("Presupuestos")).toBeInTheDocument();
    expect(screen.getByText("2026")).toBeInTheDocument();
  });

  it("expands a folder's children via its chevron without navigating", () => {
    const onNavigate = jest.fn();
    render(
      <AdminFolderPanel
        folders={folders}
        currentFolderId={null}
        onNavigate={onNavigate}
        onCreate={jest.fn()}
        onRename={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    expect(screen.queryByText("2026")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/expandir presupuestos/i));
    expect(screen.getByText("2026")).toBeInTheDocument();
    expect(onNavigate).not.toHaveBeenCalled();
  });

  it("navigates when a folder card is clicked", () => {
    const onNavigate = jest.fn();
    render(
      <AdminFolderPanel
        folders={folders}
        currentFolderId={null}
        onNavigate={onNavigate}
        onCreate={jest.fn()}
        onRename={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    fireEvent.click(screen.getByText("Presupuestos"));
    expect(onNavigate).toHaveBeenCalledWith("f1");
  });

  it("creates a new folder under the current folder", async () => {
    const onCreate = jest.fn().mockResolvedValue(undefined);
    render(
      <AdminFolderPanel
        folders={[]}
        currentFolderId={null}
        onNavigate={jest.fn()}
        onCreate={onCreate}
        onRename={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    fireEvent.click(screen.getByText("+ Nueva carpeta"));
    fireEvent.change(screen.getByPlaceholderText(/nombre de la carpeta/i), { target: { value: "Manuales" } });
    fireEvent.submit(screen.getByPlaceholderText(/nombre de la carpeta/i));
    expect(onCreate).toHaveBeenCalledWith("Manuales", null);
  });

  it("shows a folder error message when provided", () => {
    render(
      <AdminFolderPanel
        folders={[]}
        currentFolderId={null}
        onNavigate={jest.fn()}
        onCreate={jest.fn()}
        onRename={jest.fn()}
        onDelete={jest.fn()}
        error="La carpeta no está vacía"
      />
    );
    expect(screen.getByText(/la carpeta no está vacía/i)).toBeInTheDocument();
  });

  it("shows a spinner and disables actions while a folder is being deleted", () => {
    render(
      <AdminFolderPanel
        folders={folders}
        currentFolderId={null}
        onNavigate={jest.fn()}
        onCreate={jest.fn()}
        onRename={jest.fn()}
        onDelete={jest.fn()}
        deletingIds={new Set(["f1"])}
      />
    );
    const deleteButton = screen.getByLabelText("Eliminar Presupuestos");
    expect(deleteButton).toBeDisabled();
    expect(deleteButton.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    expect(screen.getByLabelText("Renombrar Presupuestos")).toBeDisabled();
  });
});
