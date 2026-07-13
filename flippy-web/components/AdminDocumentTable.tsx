import type { DocumentSummary } from "@/types/document";
import styles from "./AdminDocumentTable.module.css";

interface AdminDocumentTableProps {
  documents: DocumentSummary[];
  onDelete: (id: string) => void;
}

const STATUS_LABEL: Record<DocumentSummary["status"], string> = {
  processing: "Procesando",
  ready: "Listo",
  error: "Error",
};

export default function AdminDocumentTable({ documents, onDelete }: AdminDocumentTableProps) {
  if (documents.length === 0) {
    return <p className={styles.emptyState}>Todavía no hay documentos en el corpus.</p>;
  }

  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Tipo</th>
          <th>Estado</th>
          <th>Chunks</th>
          <th aria-label="Acciones" />
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <tr key={doc.id}>
            <td>{doc.name}</td>
            <td>{doc.type}</td>
            <td>
              <span className={`${styles.badge} ${styles[`badge_${doc.status}`]}`}>
                {STATUS_LABEL[doc.status]}
              </span>
            </td>
            <td>{doc.chunk_count}</td>
            <td>
              <button type="button" className={styles.deleteButton} onClick={() => onDelete(doc.id)}>
                Eliminar
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
