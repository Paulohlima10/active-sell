from fastapi import FastAPI
from server import webhook, create_knowledge, create_prompt, healthcheck, ask_agent, create_agents, webhook_chat, webhook_import, webhook_campaign, webhook_whatsapp_conect, webhook_agent_config
from logs.logging_config import log_message, start_log_processor
from logs.logs_api import router as logs_router
import uvicorn  # Importando o uvicorn

# Função assíncrona para inicializar o log
async def initialize_log():
    await log_message("info", "Servidor iniciado...")

app = FastAPI(on_startup=[start_log_processor, initialize_log])

# Incluindo os endpoints
app.include_router(webhook.router)
app.include_router(create_knowledge.router)
app.include_router(create_prompt.router)
app.include_router(healthcheck.router)
app.include_router(ask_agent.router) 
app.include_router(create_agents.router)
app.include_router(webhook_chat.router)
app.include_router(logs_router)
app.include_router(webhook_import.router)
app.include_router(webhook_campaign.router)
app.include_router(webhook_whatsapp_conect.router)
app.include_router(webhook_agent_config.router)

# Adicionando o bloco para rodar o servidor
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)