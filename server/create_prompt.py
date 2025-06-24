from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
from logs.logging_config import log_message

router = APIRouter()

class PromptRequest(BaseModel):
    partner_code: str
    role: str
    goal: str
    backstory: str
    name: str
    task_description: str

@router.post("/create-prompt")
async def create_prompt(request: PromptRequest):
    partner_path = Path(f"knowledge/partners/{request.partner_code}")
    try:
        partner_path.mkdir(parents=True, exist_ok=True)

        for name, value in {
            "role.txt": request.role,
            "goal.txt": request.goal,
            "backstory.txt": request.backstory,
            "name.txt": request.name,
            "task_description.txt": request.task_description
        }.items():
            with (partner_path / name).open("w", encoding="utf-8") as file:
                file.write(value)

        await log_message("info", f"Arquivos criados com sucesso para o parceiro '{request.partner_code}'.")
        return {"message": f"Arquivos criados com sucesso para o parceiro '{request.partner_code}'."}
    except Exception as e:
        await log_message("error", f"Erro ao criar os arquivos para o parceiro '{request.partner_code}': {str(e)}")
        return {"error": f"Erro ao criar os arquivos: {str(e)}"}
