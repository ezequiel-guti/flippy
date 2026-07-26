"use client";

import { useEffect, useState } from "react";
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

function RootIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 11.5 12 4l8 7.5" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 10v8.5a1 1 0 0 0 1 1h3v-5h4v5h3a1 1 0 0 0 1-1V10" />
    </svg>
  );
}

function ChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      width="14"
      height="14"
      aria-hidden
      className={expanded ? styles.chevronIconExpanded : styles.chevronIcon}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6l6 6-6 6" />
    </svg>
  );
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
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [isCreating, setIsCreating] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const byId = new Map(folders.map((f) => [f.id, f]));

  // Auto-expand the ancestry chain of whichever folder is currently open, so
  // navigating deep never leaves the tree looking collapsed around the selection.
  useEffect(() => {
    if (!currentFolderId) return;
    setExpandedIds((prev) => {
      const next = new Set(prev);
      let cursor = byId.get(currentFolderId);
      while (cursor) {
        next.add(cursor.id);
        cursor = cursor.parent_id ? byId.get(cursor.parent_id) : undefined;
      }
      return next;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentFolderId]);

  function toggleExpanded(folderId: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) next.delete(folderId);
      else next.add(folderId);
      return next;
    });
  }

  function childrenOf(parentId: string | null): DocumentFolder[] {
    return folders.filter((f) => f.parent_id === parentId).sort((a, b) => a.name.localeCompare(b.name));
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

  async function handleCreateSubmit(event: React.FormEvent) {
    event.preventDefault();
    const name = newFolderName.trim();
    if (!name) return;
    await onCreate(name, currentFolderId);
    setExpandedIds((prev) => (currentFolderId ? new Set(prev).add(currentFolderId) : prev));
    setNewFolderName("");
    setIsCreating(false);
  }

  function renderNode(folder: DocumentFolder) {
    const kids = childrenOf(folder.id);
    const hasChildren = kids.length > 0;
    const isExpanded = expandedIds.has(folder.id);
    const isActive = currentFolderId === folder.id;

    if (renamingId === folder.id) {
      return (
        <li key={folder.id}>
          <form className={styles.renameForm} onSubmit={(e) => handleRenameSubmit(e, folder.id)}>
            <input
              autoFocus
              className={styles.renameInput}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onBlur={() => setRenamingId(null)}
            />
          </form>
        </li>
      );
    }

    return (
      <li key={folder.id}>
        <div className={`${styles.node} ${isActive ? styles.nodeActive : ""}`}>
          <button type="button" className={styles.nodeLabel} onClick={() => onNavigate(folder.id)}>
            <span className={styles.folderName}>{folder.name}</span>
          </button>
          <div className={styles.nodeActions}>
            <button
              type="button"
              className={styles.nodeActionButton}
              onClick={() => startRename(folder)}
              aria-label={`Renombrar ${folder.name}`}
            >
              ✎
            </button>
            <button
              type="button"
              className={styles.nodeActionButton}
              onClick={() => onDelete(folder.id)}
              aria-label={`Eliminar ${folder.name}`}
            >
              ✕
            </button>
          </div>
          <button
            type="button"
            className={styles.chevron}
            onClick={() => toggleExpanded(folder.id)}
            aria-label={isExpanded ? `Contraer ${folder.name}` : `Expandir ${folder.name}`}
            disabled={!hasChildren}
          >
            {hasChildren && <ChevronIcon expanded={isExpanded} />}
          </button>
        </div>
        {hasChildren && isExpanded && (
          <ul className={styles.subtree}>{kids.map((kid) => renderNode(kid))}</ul>
        )}
      </li>
    );
  }

  const rootFolders = childrenOf(null);

  return (
    <nav className={styles.wrapper} aria-label="Carpetas del corpus">
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <ul className={styles.tree}>
        <li>
          <button
            type="button"
            className={`${styles.node} ${styles.nodeLabel} ${currentFolderId === null ? styles.nodeActive : ""}`}
            onClick={() => onNavigate(null)}
          >
            <span className={styles.folderIcon}>
              <RootIcon />
            </span>
            <span className={styles.folderName}>Raíz</span>
          </button>
          {rootFolders.length > 0 && <ul className={styles.subtree}>{rootFolders.map((folder) => renderNode(folder))}</ul>}
        </li>
      </ul>

      {isCreating ? (
        <form className={styles.createForm} onSubmit={handleCreateSubmit}>
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
    </nav>
  );
}
