from fastapi import APIRouter, Response
import os

router = APIRouter()

LOG_FILE_PATH = "app.log"

@router.get("/logs")
async def get_logs():
    if not os.path.exists(LOG_FILE_PATH):
        return Response(content="Log file not found.", status_code=404)
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content=content, media_type="text/plain")