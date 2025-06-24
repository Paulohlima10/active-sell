import re
from fastapi import APIRouter, Request
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from agents.agentManager import SalesAssistantManager
from logs.logging_config import log_queue

router = APIRouter()

manager = SalesAssistantManager()
client = EvolutionClient(
    base_url="http://localhost:8080",
    api_token="429683C4C977415CAAFCCE10F7D57E11"
)

@router.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    await log_queue.put(f"Dados recebidos: {data}") 

    conversation = None

    if data.get("event") == "messages.upsert":
        if isinstance(data.get("data"), dict):
            event_type = data.get("event", "desconhecido")
            instanceid = data.get("instance", "desconhecido")
            
            conversation = data["data"].get("message", {}).get("conversation")
            if conversation:
                remote_jid = data["data"].get("key", {}).get("remoteJid", "")
                phone_number = re.sub(r"@s\.whatsapp\.net$", "", remote_jid)
                manager.add_assistant(instanceid)
                msg = manager.get_assistant(instanceid).process_question(conversation, phone_number)
                message = TextMessage(number=phone_number, text=msg, delay=1000)
                apikey = data.get("apikey")
                response = client.messages.send_text(instance_id=instanceid, message=message, instance_token=apikey)

                await log_queue.put(f"Evento: {event_type}, Instance: {instanceid}, Cliente: {phone_number}, Conversation: {conversation}")
                await log_queue.put(f"Resposta AI: {msg}")
                await log_queue.put(f"Retorno EvolutionAPI: {response}")
        else:
            await log_queue.put("Erro: JSON recebido não tem o formato esperado.")

    return {"message": "Dados recebidos com sucesso"}
