from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="แผนการสอน Generator")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "active_model": settings.active_model}
