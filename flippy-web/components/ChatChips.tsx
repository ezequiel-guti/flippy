import styles from "./ChatChips.module.css";

interface ChatChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
}

export default function ChatChips({ suggestions, onSelect }: ChatChipsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className={styles.chips} role="group" aria-label="Sugerencias de consulta">
      {suggestions.map((suggestion) => (
        <button key={suggestion} type="button" className={styles.chip} onClick={() => onSelect(suggestion)}>
          {suggestion}
        </button>
      ))}
    </div>
  );
}
