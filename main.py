from fastapi import FastAPI
from server import webhook, create_knowledge, create_prompt, healthcheck, ask_agent, create_agents, webhook_chat, webhook_import, webhook_campaign, webhook_whatsapp_conect, webhook_agent_config
from logs.logging_config import log_message, start_log_processor
from logs.logs_api import router as logs_router
import uvicorn  # Importando o uvicorn
import os

# Configurações para evitar vazamentos de recursos
os.environ["CHROMA_TELEMETRY"] = "false"

# Importar utilitário de limpeza de recursos
try:
    from utils.resource_cleanup import resource_cleanup
except ImportError:
    print("Aviso: Utilitário de limpeza de recursos não encontrado")
    resource_cleanup = None

# Importar monitor do EC2
try:
    from utils.ec2_monitor import start_ec2_monitoring, get_ec2_info
except ImportError:
    print("Aviso: Monitor do EC2 não encontrado")
    start_ec2_monitoring = None
    get_ec2_info = None

# Importar monitor de memória
try:
    from utils.memory_monitor import memory_monitor
    print("✅ Monitor de memória ativado")
except ImportError:
    print("Aviso: Monitor de memória não encontrado")
    memory_monitor = None

# Função assíncrona para inicializar o log
async def initialize_log():
    await log_message("info", "Servidor iniciado...")
    
    # Logar informações do EC2 se disponível
    if get_ec2_info:
        ec2_info = get_ec2_info()
        await log_message("info", f"EC2_INFO - {ec2_info}")

# Função para limpar recursos no shutdown
async def cleanup_resources():
    await log_message("info", "Limpando recursos...")
    # Forçar limpeza de recursos se o utilitário estiver disponível
    if resource_cleanup:
        resource_cleanup.force_cleanup()

app = FastAPI(
    on_startup=[start_log_processor, initialize_log, start_ec2_monitoring] if start_ec2_monitoring else [start_log_processor, initialize_log],
    on_shutdown=[cleanup_resources]
)

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
    import multiprocessing
    
    # Configurações otimizadas para EC2
    workers = min(multiprocessing.cpu_count(), 1)  # Máximo 1 worker no EC2
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        workers=workers,
        loop="asyncio",
        access_log=True,
        log_level="info"
    )