import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.schemas.assistant import AssistantRequest
from creditflow.services.dependencies import RuntimeDep

router = APIRouter(tags=["evidence assistant"])


@router.post("/applications/{application_id}/assistant/stream")
async def stream_assistant(
    application_id: UUID,
    request: AssistantRequest,
    principal: PrincipalDep,
    runtime: RuntimeDep,
) -> StreamingResponse:
    principal.require("analyst", "underwriter")
    analysis = await runtime.get_analysis(principal.tenant_id, application_id)
    evidence = [
        str(item.get("source_id"))
        for item in analysis.get("supporting_evidence", [])
        if isinstance(item, dict) and item.get("source_id")
    ]
    summary = (
        f"Question: {request.question}\n"
        f"The validated recommendation is {analysis.get('recommendation', 'unavailable')} "
        f"with risk level {analysis.get('risk_level', 'unavailable')}. "
        "This is an evidence summary, not a lending decision."
    )

    async def events() -> AsyncIterator[str]:
        for token in summary.split():
            yield f"data: {json.dumps({'type': 'token', 'text': token + ' '})}\n\n"
            await asyncio.sleep(0)
        yield f"data: {json.dumps({'type': 'citations', 'source_ids': evidence})}\n\n"
        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
