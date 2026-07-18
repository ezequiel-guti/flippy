import base64
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.security import TokenData, get_current_user
from app.integrations import anthropic_vision, gemini
from app.integrations.openai_embeddings import embed_text

from .model import ChatRename, ChatSummary, MessageCreate, MessageResponse
from .services import (
    DEFAULT_IMAGE_CAPTION,
    SYSTEM_PROMPT,
    VISION_SYSTEM_PROMPT,
    ChatService,
    build_contents,
    build_vision_messages,
)

router = APIRouter(prefix="/chats", tags=["chat"])

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB — limite de imagenes base64 de la API de Anthropic


@router.get("", response_model=list[ChatSummary])
def list_chats(current_user: TokenData = Depends(get_current_user)):
    return ChatService.list_chats(current_user.user_id)


@router.post("", response_model=ChatSummary)
def create_chat(current_user: TokenData = Depends(get_current_user)):
    return ChatService.create_chat(current_user.user_id)


@router.patch("/{chat_id}", response_model=ChatSummary)
def rename_chat(chat_id: str, body: ChatRename, current_user: TokenData = Depends(get_current_user)):
    chat = ChatService.rename_chat(chat_id, current_user.user_id, body.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    return chat


@router.delete("/{chat_id}", status_code=204)
def delete_chat(chat_id: str, current_user: TokenData = Depends(get_current_user)):
    deleted = ChatService.delete_chat(chat_id, current_user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat no encontrado")


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


@router.post("/{chat_id}/messages/image")
async def send_image_message(
    chat_id: str,
    file: UploadFile = File(...),
    content: str = Form(""),
    current_user: TokenData = Depends(get_current_user),
):
    chat = ChatService.get_chat(chat_id, current_user.user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo adjunto debe ser una imagen")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Imagen demasiado grande (máximo 5 MB)")

    caption = content.strip()
    storage_path = ChatService.upload_chat_image(chat_id, file.filename or "imagen", image_bytes, file.content_type)
    ChatService.save_message(chat_id, "user", caption or DEFAULT_IMAGE_CAPTION, image_url=storage_path)
    ChatService.maybe_set_title_from_first_message(chat_id, caption or DEFAULT_IMAGE_CAPTION)

    history = ChatService.list_messages(chat_id)[:-1]
    if caption:
        query_embedding = embed_text(caption)
        context_chunks = ChatService.search_context(query_embedding)
    else:
        context_chunks = []

    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    messages = build_vision_messages(history, context_chunks, caption or DEFAULT_IMAGE_CAPTION, image_base64, file.content_type)

    def event_stream():
        full_text: list[str] = []
        try:
            for piece in anthropic_vision.stream_vision(VISION_SYSTEM_PROMPT, messages):
                full_text.append(piece)
                yield f"data: {json.dumps({'text': piece})}\n\n"
        except anthropic_vision.AnthropicError:
            yield f"data: {json.dumps({'error': 'No pudimos analizar la imagen. Intenta de nuevo.'})}\n\n"
        finally:
            if full_text:
                ChatService.save_message(chat_id, "assistant", "".join(full_text))
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
