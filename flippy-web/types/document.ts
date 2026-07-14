export interface DocumentSummary {
  id: string;
  name: string;
  type: "pdf" | "docx" | "txt" | "json" | "html" | "image";
  status: "processing" | "ready" | "error";
  chunk_count: number;
  created_at: string;
}
