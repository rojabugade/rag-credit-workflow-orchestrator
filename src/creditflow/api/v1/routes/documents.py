from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.core.config import Settings, get_settings
from creditflow.services.dependencies import RuntimeDep

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: UUID,
    principal: PrincipalDep,
    settings: Annotated[Settings, Depends(get_settings)],
    runtime: RuntimeDep,
    file: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    principal.require("analyst", "underwriter")
    content = await file.read(settings.max_upload_bytes + 1)
    try:
        return await runtime.add_document(
            principal.tenant_id,
            case_id,
            principal.subject,
            file.filename or "",
            file.content_type or "",
            content,
            settings.max_upload_bytes,
        )
    finally:
        await file.close()


@router.get("")
async def list_documents(
    case_id: UUID, principal: PrincipalDep, runtime: RuntimeDep
) -> dict[str, Any]:
    documents = await runtime.list_documents(principal.tenant_id, case_id)
    return {"items": documents, "total": len(documents)}
