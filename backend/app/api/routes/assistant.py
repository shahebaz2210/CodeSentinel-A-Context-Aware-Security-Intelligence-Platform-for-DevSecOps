"""AI Security Assistant routes — T-114, T-117 (streaming)."""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db

router = APIRouter()


class AssistantQuery(BaseModel):
    question: str
    scan_id: str | None = None
    finding_id: str | None = None


@router.post("/assistant/query", summary="AI Security Assistant — T-114/T-117")
async def assistant_query(
    payload: AssistantQuery,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Answer a developer security question grounded in real scan data + RAG.
    Returns a streaming text/event-stream response — T-117.
    """
    from app.services.assistant_service import AssistantService

    service = AssistantService(db=db)

    async def event_stream():
        try:
            async for chunk in service.stream_answer(
                question=payload.question,
                scan_id=payload.scan_id,
                finding_id=payload.finding_id,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
