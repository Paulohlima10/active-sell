from fastapi import APIRouter, Request
from logs.logging_config import log_message
from campaigns.send_campaign_unique import process_campaigns  # Corrija para o nome correto da função

import asyncio

router = APIRouter()

@router.post("/webhook_campaign")
async def webhook_campaign(request: Request):
    data = await request.json()
    # print(data)
    await log_message("info", f"webhook_campaign - Dados: {data}")

    # Extrai o id da campanha do JSON recebido
    campaign_id = data.get("record", {}).get("id")
    if campaign_id:
        # Dispara o processamento da campanha em background
        asyncio.create_task(process_campaigns(campaign_id))
        return {"message": f"Processamento da campanha {campaign_id} iniciado com sucesso"}
    else:
        return {"error": "ID da campanha não encontrado no payload"}, 400