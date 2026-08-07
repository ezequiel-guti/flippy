import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessageData } from "@/types/chat";
import styles from "./ChatMessage.module.css";

interface ChatMessageProps {
  message: ChatMessageData;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isPendingAssistantReply = !isUser && message.content === "";

  return (
    <div
      className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant}`}
      role="article"
      aria-label={isUser ? "Tu mensaje" : "Respuesta de Flippy"}
    >
      {message.imageUrl && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={message.imageUrl} alt="Imagen adjunta por el usuario" className={styles.image} />
      )}
      {isPendingAssistantReply ? (
        <span className={styles.spinner} aria-hidden="true" />
      ) : isUser ? (
        <p>{message.content}</p>
      ) : (
        <div className={styles.markdown}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
