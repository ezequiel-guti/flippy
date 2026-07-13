from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.core.security import TokenData, require_admin

from .model import DocumentResponse
from .services import ALLOWED_TYPES, DocumentsService

router = APIRouter(prefix="/admin/documents", tags=["documents"])

EXTENSION_TO_TYPE = {"pdf": "pdf", "docx": "docx", "txt": "txt", "jpg": "image", "jpeg": "image", "png": "image"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _admin: TokenData = Depends(require_admin),
):
    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    doc_type = EXTENSION_TO_TYPE.get(extension)
    if not doc_type or doc_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no soportado: .{extension}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máximo 20 MB)")
    created = DocumentsService.create_document(file.filename, doc_type, content)
    background_tasks.add_task(DocumentsService.process_document, created["id"], content, doc_type)

    return {
        "id": created["id"],
        "name": created["name"],
        "type": created["type"],
        "status": "processing",
        "chunk_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("", response_model=list[DocumentResponse])
def list_documents(_admin: TokenData = Depends(require_admin)):
    return DocumentsService.list_documents()


@router.delete("/{document_id}")
def delete_document(document_id: str, _admin: TokenData = Depends(require_admin)):
    deleted = DocumentsService.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"success": True}
