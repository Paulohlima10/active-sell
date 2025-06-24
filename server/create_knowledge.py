from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
from logs.logging_config import log_message

router = APIRouter()

class KnowledgeRequest(BaseModel):
    partner_code: str
    content: str

@router.post("/create-knowledge")
async def create_knowledge(request: KnowledgeRequest):
    partner_path = Path(f"knowledge/partners/{request.partner_code}")
    document_path = partner_path / "document.txt"

    try:
        partner_path.mkdir(parents=True, exist_ok=True)
        with document_path.open("w", encoding="utf-8") as file:
            file.write(request.content)

        await log_message("info", f"Arquivo document.txt criado com sucesso para o parceiro '{request.partner_code}'.")
        return {"message": f"Arquivo document.txt criado com sucesso para o parceiro '{request.partner_code}'."}
    except Exception as e:
        await log_message("error", f"Erro ao criar o arquivo para o parceiro '{request.partner_code}': {str(e)}")
        return {"error": f"Erro ao criar o arquivo: {str(e)}"}
