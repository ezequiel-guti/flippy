"use client";

import { useEffect, useState } from "react";
import styles from "./IOSInstallBanner.module.css";

const DISMISSED_KEY = "flippy-ios-install-dismissed";

function isIOSSafari(): boolean {
  const ua = window.navigator.userAgent;
  const isIOS = /iPad|iPhone|iPod/.test(ua) || (ua.includes("Macintosh") && navigator.maxTouchPoints > 1);
  const isStandalone =
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true ||
    window.matchMedia("(display-mode: standalone)").matches;
  return isIOS && !isStandalone;
}

export default function IOSInstallBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (localStorage.getItem(DISMISSED_KEY)) return;
    if (isIOSSafari()) setVisible(true);
  }, []);

  function dismiss() {
    localStorage.setItem(DISMISSED_KEY, "1");
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className={styles.banner} role="status">
      <p className={styles.text}>
        Instalá Flippy: tocá <strong>Compartir</strong>{" "}
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="15" height="15" className={styles.icon}>
          <path d="M12 3v13M8 7l4-4 4 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
        </svg>{" "}
        y luego <strong>&quot;Agregar a pantalla de inicio&quot;</strong>
      </p>
      <button type="button" className={styles.close} onClick={dismiss} aria-label="Cerrar aviso de instalación">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
