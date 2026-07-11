import type { ChatMessageData, ChatSummary } from "@/types/chat";

export const mockChats: ChatSummary[] = [
  { id: "1", title: "Requisitos para escritura", updatedAt: "2026-07-10T14:30:00Z" },
  { id: "2", title: "Boleto de compraventa", updatedAt: "2026-07-09T09:15:00Z" },
  { id: "3", title: "Impuestos de transferencia", updatedAt: "2026-07-07T18:00:00Z" },
];

export const mockMessages: ChatMessageData[] = [
  {
    id: "m1",
    role: "user",
    content: "¿Qué documentos necesito para escriturar una propiedad?",
    createdAt: "2026-07-10T14:28:00Z",
  },
  {
    id: "m2",
    role: "assistant",
    content:
      "Para escriturar necesitás el boleto de compraventa firmado, el certificado de dominio vigente, el recibo de pago de impuestos al día y el DNI de todas las partes involucradas.",
    createdAt: "2026-07-10T14:30:00Z",
  },
];
