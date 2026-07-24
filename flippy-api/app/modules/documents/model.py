from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    chunk_count: int
    folder_id: str | None = None
    created_at: str


class FolderResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    created_at: str
    updated_at: str


class FolderCreateRequest(BaseModel):
    name: str
    parent_id: str | None = None


class FolderUpdateRequest(BaseModel):
    name: str | None = None
    parent_id: str | None = None


class DocumentMoveRequest(BaseModel):
    folder_id: str | None = None
