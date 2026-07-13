export interface DocumentSummary {
  id: string;
  name: string;
  type: "pdf" | "docx" | "txt" | "image";
  status: "processing" | "ready" | "error";
  chunk_count: number;
  created_at: string;
}
