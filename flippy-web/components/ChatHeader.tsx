import Image from "next/image";
import styles from "./ChatHeader.module.css";

interface ChatHeaderProps {
  onOpenHistory: () => void;
}

export default function ChatHeader({ onOpenHistory }: ChatHeaderProps) {
  return (
    <header className={styles.header}>
      <button type="button" className={styles.historyButton} onClick={onOpenHistory} aria-label="Ver historial de chats">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="22" height="22">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M9 4v16" />
        </svg>
      </button>
      <Image src="/icons/logo-shield.png" alt="" width={26} height={31} className={styles.logo} />
      <div className={styles.identity}>
        <span className={styles.name}>Flippy</span>
        <span className={styles.status}>
          <span className={styles.dot} aria-hidden="true" />
          Asistente · activo
        </span>
      </div>
    </header>
  );
}
