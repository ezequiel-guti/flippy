from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    chunk_count: int
    created_at: str
