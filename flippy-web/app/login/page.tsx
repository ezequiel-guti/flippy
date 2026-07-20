"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost, ApiError } from "@/services/api";
import styles from "./page.module.css";

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleMode() {
    setMode((prev) => (prev === "login" ? "register" : "login"));
    setError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const path = mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register";
      const tokens = await apiPost<TokenResponse>(path, { email, password });
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      router.push("/chat");
    } catch (err) {
      if (mode === "login" && err instanceof ApiError && err.status === 401) {
        setError("Email o contraseña incorrectos.");
      } else if (mode === "register" && err instanceof ApiError && err.status === 422) {
        setError("Ese email ya está registrado. Probá iniciar sesión.");
      } else if (mode === "register") {
        setError("No pudimos crear la cuenta. Verificá los datos e intentá de nuevo.");
      } else {
        setError("No pudimos iniciar sesión. Intentá de nuevo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <h1 className={styles.title}>Flippy</h1>
        <p className={styles.subtitle}>
          {mode === "login" ? "Ingresá con tu cuenta de socio" : "Creá tu cuenta de socio"}
        </p>

        <label className={styles.field}>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isSubmitting}
          />
        </label>

        <label className={styles.field}>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={mode === "register" ? 6 : undefined}
            disabled={isSubmitting}
          />
        </label>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        <button type="submit" className={styles.submit} disabled={isSubmitting}>
          {isSubmitting ? (mode === "login" ? "Ingresando…" : "Creando cuenta…") : mode === "login" ? "Ingresar" : "Crear cuenta"}
        </button>

        <button type="button" className={styles.toggleMode} onClick={toggleMode} disabled={isSubmitting}>
          {mode === "login" ? "¿No tenés cuenta? Registrate" : "¿Ya tenés cuenta? Ingresá"}
        </button>
      </form>
    </main>
  );
}
