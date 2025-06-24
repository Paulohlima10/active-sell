from fastapi import APIRouter
from pydantic import BaseModel
from logs.logging_config import log_message
from agents.agentManager import global_manager

router = APIRouter()

class CreateAgentRequest(BaseModel):
    partner_code: str

@router.post("/create-agent")
async def create_agent(request: CreateAgentRequest):
    try:
        # Adiciona o assistente usando a instância global
        global_manager.add_assistant(request.partner_code)
        await log_message("info", f"Assistente para o parceiro '{request.partner_code}' foi criado com sucesso.")
        return {"message": f"Assistente para o parceiro '{request.partner_code}' foi criado com sucesso."}
    except Exception as e:
        await log_message("error", f"Erro ao criar o assistente para o parceiro '{request.partner_code}': {str(e)}")
        return {"error": f"Erro ao criar o assistente: {str(e)}"}