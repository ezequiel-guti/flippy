import Image from "next/image";
import Link from "next/link";
import styles from "./AdminSidebar.module.css";

interface AdminNavItem {
  href: string;
  label: string;
}

const NAV_ITEMS: AdminNavItem[] = [{ href: "/admin", label: "Documentos" }];

interface AdminSidebarProps {
  activeHref: string;
}

export default function AdminSidebar({ activeHref }: AdminSidebarProps) {
  return (
    <nav className={styles.sidebar} aria-label="Menú de administración">
      <div className={styles.top}>
        <Image src="/icons/logo-shield.png" alt="" width={22} height={26} />
        <span className={styles.brandName}>Flippy Admin</span>
      </div>

      <ul className={styles.navList}>
        {NAV_ITEMS.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={`${styles.navItem} ${item.href === activeHref ? styles.navItemActive : ""}`}
              aria-current={item.href === activeHref ? "page" : undefined}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>

      <div className={styles.footer}>
        <Link href="/chat" className={styles.backLink}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M15 19l-7-7 7-7" />
          </svg>
          Volver al chat
        </Link>
      </div>
    </nav>
  );
}
