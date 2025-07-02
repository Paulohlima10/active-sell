from fastapi import APIRouter, Request
from logs.logging_config import log_message

router = APIRouter()

@router.post("/webhook_agent_config")
async def webhook_agent_config(request: Request):
    data = await request.json()
    await log_message("info", f"Dados recebidos: {data}")

    print(data)
    return {"message": "Dados recebidos com sucesso"}