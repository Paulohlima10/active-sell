from fastapi import APIRouter, Request
from logs.logging_config import log_message
from agents.agentManager import global_manager
from pathlib import Path

router = APIRouter()

@router.post("/webhook_agent_config")
async def webhook_agent_config(request: Request):
    data = await request.json()
    await log_message("info", f"webhook_agent_config: Dados recebidos: {data}")
    partner = data.get("record", {}).get("empresa_id")
    name = data.get("record", {}).get("name")
    role = data.get("record", {}).get("role")
    goal = data.get("record", {}).get("goal")
    backstory = data.get("record", {}).get("backstory")
    task_description = data.get("record", {}).get("task_description")
    content = data.get("record", {}).get("knowledge_base")

    # Cria o assistente se não existir
    try:
        # Adiciona o assistente usando a instância global
        if global_manager.agent_exists(partner):
            await log_message("info", f"webhook_agent_config: Assistente para o parceiro '{partner}' já existe.")
        else:
            global_manager.add_assistant(partner)
            await log_message("info", f"webhook_agent_config: Assistente para o parceiro '{partner}' foi criado com sucesso.")
    except Exception as e:
        await log_message("error", f"Erro ao criar o assistente para o parceiro '{partner}': {str(e)}")
        return {"error": f"Erro ao criar o assistente: {str(e)}"}

    # Criar o prompt do assistente
    partner_path = Path(f"knowledge/partners/{partner}")
    try:
        partner_path.mkdir(parents=True, exist_ok=True)

        for name, value in {
            "role.txt": role,
            "goal.txt": goal,
            "backstory.txt": backstory,
            "name.txt": name,
            "task_description.txt": task_description
        }.items():
            with (partner_path / name).open("w", encoding="utf-8") as file:
                file.write(value)

        await log_message("info", f"webhook_agent_config: Arquivos criados com sucesso para o parceiro '{partner}'.")
    except Exception as e:
        await log_message("error", f"webhook_agent_config: Erro ao criar os arquivos para o parceiro '{partner}': {str(e)}")
        return {"error": f"Erro ao criar os arquivos: {str(e)}"}

    # Criar base de conhecimento
    document_path = partner_path / "document.txt"
    try:
        partner_path.mkdir(parents=True, exist_ok=True)
        with document_path.open("w", encoding="utf-8") as file:
            file.write(content)

        await log_message("info", f"webhook_agent_config: Arquivo document.txt criado com sucesso para o parceiro '{partner}'.")
    except Exception as e:
        await log_message("error", f"webhook_agent_config: Erro ao criar o arquivo para o parceiro '{partner}': {str(e)}")
        return {"error": f"Erro ao criar o arquivo: {str(e)}"}

    return {"message": "Dados recebidos com sucesso"}