import styles from "./AdminTopBar.module.css";

interface AdminTopBarProps {
  currentFolderName?: string | null;
}

export default function AdminTopBar({ currentFolderName }: AdminTopBarProps) {
  return (
    <header className={styles.header}>
      <h1 className={styles.title}>Documentos</h1>
      {currentFolderName && <span className={styles.folder}>{currentFolderName}</span>}
    </header>
  );
}
