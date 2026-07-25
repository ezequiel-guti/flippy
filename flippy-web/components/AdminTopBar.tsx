import Image from "next/image";
import styles from "./AdminTopBar.module.css";

interface AdminTopBarProps {
  currentFolderName?: string | null;
}

export default function AdminTopBar({ currentFolderName }: AdminTopBarProps) {
  return (
    <header className={styles.header}>
      <Image src="/icons/logo-shield.png" alt="" width={26} height={31} className={styles.logo} />
      <div className={styles.identity}>
        <span className={styles.name}>Flippy</span>
        <span className={styles.status}>
          <span className={styles.dot} aria-hidden="true" />
          {currentFolderName ? `Documentos · ${currentFolderName}` : "Documentos"}
        </span>
      </div>
    </header>
  );
}
