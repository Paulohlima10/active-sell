from fastapi import APIRouter, Request
from logs.logging_config import log_message
import asyncio
from supabase import create_client

router = APIRouter()

def get_supabase_client():
    url = "https://gzzvydiznhwaxrahzkjt.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6enZ5ZGl6bmh3YXhyYWh6a2p0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2NTY0NTAsImV4cCI6MjA2MzIzMjQ1MH0.q2WE3ct6Gf2K6mmxe8ioPhgnkXkdQLjlNHW3bQARsJc"
    if not url or not key:
        raise ValueError("Credenciais do Supabase não encontradas nas variáveis de ambiente.")
    return create_client(url, key)

async def update_import_configuration(record_id, **fields):
    supabase = get_supabase_client()
    # O método .update retorna um objeto Response, mas não é async
    supabase.table("import_configurations").update(fields).eq("id", record_id).execute()

@router.post("/webhook_import")
async def webhook_import(request: Request):
    data = await request.json()
    await log_message("info", f"webhook_import - Dados recebidos: {data}")

    if data.get("type") != "INSERT":
        await log_message("info", "webhook_import - Tipo não é INSERT, ignorando processamento sequencial.")
        return {"message": "Tipo não é INSERT, nada a fazer."}

    record = data.get("record")
    if not record or "id" not in record:
        return {"error": "ID não encontrado no payload"}

    record_id = record["id"]

    await asyncio.sleep(3)
    await update_import_configuration(
        record_id,
        validation_completed=True,
        progress=15
    )

    await asyncio.sleep(5)
    await update_import_configuration(
        record_id,
        clients_data_processed=True,
        progress=35
    )

    await asyncio.sleep(8)
    await update_import_configuration(
        record_id,
        purchases_data_processed=True,
        progress=70
    )

    await asyncio.sleep(5)
    await update_import_configuration(
        record_id,
        products_data_processed=True,
        progress=100,
        processing_completed=True,
        status="Processamento completo"
    )

    return {"message": "Processamento simulado concluído"}