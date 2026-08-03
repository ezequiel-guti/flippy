import Image from "next/image";
import styles from "./LoadingSpinner.module.css";

interface LoadingSpinnerProps {
  label?: string;
}

export default function LoadingSpinner({ label }: LoadingSpinnerProps) {
  return (
    <div className={styles.wrapper} role="status" aria-live="polite">
      <div className={styles.ring}>
        <Image src="/icons/logo-shield.png" alt="" width={22} height={26} className={styles.logo} />
      </div>
      {label && <span className={styles.label}>{label}</span>}
    </div>
  );
}
