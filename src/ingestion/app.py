import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.ingestion.normalizer import normalize_text, text_cache_key
from src.ingestion.cache import get_flag, set_flag, ping as cache_ping
from src.ingestion.queue import enqueue_text


app = FastAPI(title="Agentic Moderation API")


class TextRequest(BaseModel):
    text: str


class TextResponse(BaseModel):
    request_id: str
    status: str
    flag: str | None = None


@app.get("/health")
def health():
    try:
        cache_ping()
        cache_ok = True
    except Exception:
        cache_ok = False
    return {"api": "ok", "cache": cache_ok}


@app.post("/moderate/text", response_model=TextResponse)
def moderate_text(req: TextRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")

    key = text_cache_key(req.text)
    cached = get_flag(key)

    if cached:
        return TextResponse(request_id=str(uuid.uuid4()), status="cached", flag=cached)

    request_id = str(uuid.uuid4())
    enqueue_text({
        "request_id": request_id,
        "cache_key": key,
        "text": req.text,
        "normalized": normalize_text(req.text),
    })
    return TextResponse(request_id=request_id, status="queued", flag=None)