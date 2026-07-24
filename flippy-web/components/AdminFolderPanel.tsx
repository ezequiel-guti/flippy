"use client";

import { useState } from "react";
import type { DocumentFolder } from "@/types/folder";
import styles from "./AdminFolderPanel.module.css";

interface AdminFolderPanelProps {
  folders: DocumentFolder[];
  currentFolderId: string | null;
  onNavigate: (folderId: string | null) => void;
  onCreate: (name: string, parentId: string | null) => Promise<void>;
  onRename: (folderId: string, name: string) => Promise<void>;
  onDelete: (folderId: string) => Promise<void>;
  error?: string | null;
}

export default function AdminFolderPanel({
  folders,
  currentFolderId,
  onNavigate,
  onCreate,
  onRename,
  onDelete,
  error,
}: AdminFolderPanelProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const byId = new Map(folders.map((f) => [f.id, f]));
  const breadcrumb: DocumentFolder[] = [];
  let cursor = currentFolderId ? byId.get(currentFolderId) : undefined;
  while (cursor) {
    breadcrumb.unshift(cursor);
    cursor = cursor.parent_id ? byId.get(cursor.parent_id) : undefined;
  }

  const subfolders = folders
    .filter((f) => f.parent_id === currentFolderId)
    .sort((a, b) => a.name.localeCompare(b.name));

  async function handleCreateSubmit(event: React.FormEvent) {
    event.preventDefault();
    const name = newFolderName.trim();
    if (!name) return;
    await onCreate(name, currentFolderId);
    setNewFolderName("");
    setIsCreating(false);
  }

  function startRename(folder: DocumentFolder) {
    setRenamingId(folder.id);
    setRenameValue(folder.name);
  }

  async function handleRenameSubmit(event: React.FormEvent, folderId: string) {
    event.preventDefault();
    const name = renameValue.trim();
    if (!name) return;
    await onRename(folderId, name);
    setRenamingId(null);
  }

  return (
    <div className={styles.wrapper}>
      <nav className={styles.breadcrumb} aria-label="Ubicación actual">
        <button type="button" className={styles.breadcrumbItem} onClick={() => onNavigate(null)}>
          Raíz
        </button>
        {breadcrumb.map((folder) => (
          <span key={folder.id} className={styles.breadcrumbSegment}>
            <span className={styles.breadcrumbSeparator}>/</span>
            <button type="button" className={styles.breadcrumbItem} onClick={() => onNavigate(folder.id)}>
              {folder.name}
            </button>
          </span>
        ))}
      </nav>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <div className={styles.folderGrid}>
        {subfolders.map((folder) =>
          renamingId === folder.id ? (
            <form
              key={folder.id}
              className={styles.folderCardEditing}
              onSubmit={(e) => handleRenameSubmit(e, folder.id)}
            >
              <input
                autoFocus
                className={styles.renameInput}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={() => setRenamingId(null)}
              />
            </form>
          ) : (
            <div key={folder.id} className={styles.folderCard}>
              <button
                type="button"
                className={styles.folderCardButton}
                onClick={() => onNavigate(folder.id)}
              >
                <span className={styles.folderIcon} aria-hidden>
                  📁
                </span>
                <span className={styles.folderName}>{folder.name}</span>
              </button>
              <div className={styles.folderActions}>
                <button
                  type="button"
                  className={styles.folderActionButton}
                  onClick={() => startRename(folder)}
                  aria-label={`Renombrar ${folder.name}`}
                >
                  ✎
                </button>
                <button
                  type="button"
                  className={styles.folderActionButton}
                  onClick={() => onDelete(folder.id)}
                  aria-label={`Eliminar ${folder.name}`}
                >
                  ✕
                </button>
              </div>
            </div>
          )
        )}

        {isCreating ? (
          <form className={styles.folderCardEditing} onSubmit={handleCreateSubmit}>
            <input
              autoFocus
              className={styles.renameInput}
              placeholder="Nombre de la carpeta"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onBlur={() => !newFolderName.trim() && setIsCreating(false)}
            />
          </form>
        ) : (
          <button type="button" className={styles.newFolderButton} onClick={() => setIsCreating(true)}>
            + Nueva carpeta
          </button>
        )}
      </div>
    </div>
  );
}
