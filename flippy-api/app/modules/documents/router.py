from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.core.security import TokenData, require_admin

from .model import (
    DocumentMoveRequest,
    DocumentResponse,
    FolderCreateRequest,
    FolderResponse,
    FolderUpdateRequest,
)
from .services import ALLOWED_TYPES, DocumentsService, FoldersService

router = APIRouter(prefix="/admin/documents", tags=["documents"])
folders_router = APIRouter(prefix="/admin/folders", tags=["document-folders"])

EXTENSION_TO_TYPE = {
    "pdf": "pdf",
    "docx": "docx",
    "txt": "txt",
    "json": "json",
    "html": "html",
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    folder_id: str | None = Form(None),
    _admin: TokenData = Depends(require_admin),
):
    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    doc_type = EXTENSION_TO_TYPE.get(extension)
    if not doc_type or doc_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no soportado: .{extension}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máximo 20 MB)")
    created = DocumentsService.create_document(file.filename, doc_type, content, folder_id)
    background_tasks.add_task(DocumentsService.process_document, created["id"], content, doc_type)

    return {
        "id": created["id"],
        "name": created["name"],
        "type": created["type"],
        "status": "processing",
        "chunk_count": 0,
        "folder_id": created.get("folder_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    folder_id: str | None = None,
    all: bool = False,
    _admin: TokenData = Depends(require_admin),
):
    """By default lists everything. Pass all=false with no folder_id to list
    only root-level documents, or folder_id to list a specific folder's contents."""
    if all:
        return DocumentsService.list_documents()
    return DocumentsService.list_documents(folder_id=folder_id, filter_by_folder=True)


@router.delete("/{document_id}")
def delete_document(document_id: str, _admin: TokenData = Depends(require_admin)):
    deleted = DocumentsService.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"success": True}


@router.patch("/{document_id}/folder", response_model=DocumentResponse)
def move_document(
    document_id: str, payload: DocumentMoveRequest, _admin: TokenData = Depends(require_admin)
):
    moved = DocumentsService.move_document(document_id, payload.folder_id)
    if not moved:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return moved


@folders_router.post("", response_model=FolderResponse)
def create_folder(payload: FolderCreateRequest, _admin: TokenData = Depends(require_admin)):
    return FoldersService.create_folder(payload.name, payload.parent_id)


@folders_router.get("", response_model=list[FolderResponse])
def list_folders(_admin: TokenData = Depends(require_admin)):
    return FoldersService.list_folders()


@folders_router.patch("/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: str, payload: FolderUpdateRequest, _admin: TokenData = Depends(require_admin)
):
    fields_set = payload.model_fields_set
    updated = FoldersService.update_folder(
        folder_id,
        name=payload.name,
        parent_id=payload.parent_id,
        move_to_root="parent_id" in fields_set and payload.parent_id is None,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")
    return updated


@folders_router.delete("/{folder_id}")
def delete_folder(folder_id: str, _admin: TokenData = Depends(require_admin)):
    deleted, error = FoldersService.delete_folder(folder_id)
    if not deleted:
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Carpeta no encontrada")
        raise HTTPException(
            status_code=409,
            detail="La carpeta no está vacía — moveé o eliminá su contenido antes de borrarla",
        )
    return {"success": True}
