import logging
import asyncio

# Configurar o logger
logger = logging.getLogger("async_logger")
logger.setLevel(logging.INFO)

# Configurar o handler para gravar logs em um arquivo
file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Criar uma fila para logs
log_queue = asyncio.Queue()

# Tarefa assíncrona para processar logs
async def process_logs():
    while True:
        log_level, log_message = await log_queue.get()
        log_method = getattr(logger, log_level, logger.info)
        log_method(log_message)
        log_queue.task_done()

# Função para adicionar logs à fila
async def log_message(level: str, message: str):
    await log_queue.put((level, message))

# Função para iniciar o processamento de logs
async def start_log_processor():
    asyncio.create_task(process_logs())