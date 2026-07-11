import type { ChatMessageData } from "@/types/chat";
import styles from "./ChatMessage.module.css";

interface ChatMessageProps {
  message: ChatMessageData;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`${styles.row} ${isUser ? styles.rowUser : styles.rowAssistant}`}>
      <div
        className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant}`}
        role="article"
        aria-label={isUser ? "Tu mensaje" : "Respuesta de Flippy"}
      >
        {message.imageUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={message.imageUrl} alt="Imagen adjunta por el usuario" className={styles.image} />
        )}
        <p>{message.content}</p>
      </div>
    </div>
  );
}
