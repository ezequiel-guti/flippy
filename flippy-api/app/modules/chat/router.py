import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import TokenData, get_current_user
from app.integrations import gemini
from app.integrations.openai_embeddings import embed_text

from .model import ChatSummary, MessageCreate, MessageResponse
from .services import SYSTEM_PROMPT, ChatService, build_contents

router = APIRouter(prefix="/chats", tags=["chat"])


@router.get("", response_model=list[ChatSummary])
def list_chats(current_user: TokenData = Depends(get_current_user)):
    return ChatService.list_chats(current_user.user_id)


@router.post("", response_model=ChatSummary)
def create_chat(current_user: TokenData = Depends(get_current_user)):
    return ChatService.create_chat(current_user.user_id)


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
def list_messages(chat_id: str, current_user: TokenData = Depends(get_current_user)):
    chat = ChatService.get_chat(chat_id, current_user.user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    return ChatService.list_messages(chat_id)


@router.post("/{chat_id}/messages")
def send_message(chat_id: str, body: MessageCreate, current_user: TokenData = Depends(get_current_user)):
    chat = ChatService.get_chat(chat_id, current_user.user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    ChatService.save_message(chat_id, "user", body.content)
    ChatService.maybe_set_title_from_first_message(chat_id, body.content)

    history = ChatService.list_messages(chat_id)[:-1]
    query_embedding = embed_text(body.content)
    context_chunks = ChatService.search_context(query_embedding)
    contents = build_contents(history, context_chunks, body.content)

    def event_stream():
        full_text: list[str] = []
        try:
            for piece in gemini.stream_chat(SYSTEM_PROMPT, contents):
                full_text.append(piece)
                yield f"data: {json.dumps({'text': piece})}\n\n"
        except gemini.GeminiError:
            yield f"data: {json.dumps({'error': 'No pudimos generar una respuesta. Intenta de nuevo.'})}\n\n"
        finally:
            if full_text:
                ChatService.save_message(chat_id, "assistant", "".join(full_text))
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
