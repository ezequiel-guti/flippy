from pydantic import BaseModel


class ChatSummary(BaseModel):
    id: str
    title: str
    updated_at: str


class ChatRename(BaseModel):
    title: str


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    image_url: str | None = None
    created_at: str
