import os
import asyncio
from logs.logging_config import log_queue

class PromptManager:
    def __init__(self, partner_code):
        self.partner_code = partner_code
        self.role = self.load_file("role.txt")
        self.goal = self.load_file("goal.txt")
        self.backstory = self.load_file("backstory.txt")
        self.task_description = self.load_file("task_description.txt")
        self.name = self.load_file("name.txt")

    def load_file(self, file_name):
        """Lê um arquivo específico da base de conhecimento do parceiro"""
        knowledge_path = os.path.join("knowledge", "partners", self.partner_code)
        file_path = os.path.join(knowledge_path, file_name)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                asyncio.create_task(log_queue.put(("info", f"Conteúdo do arquivo '{file_name}' carregado para o parceiro '{self.partner_code}'")))
                return content
        else:
            asyncio.create_task(log_queue.put(("info", f"O arquivo '{file_name}' não foi encontrado para o parceiro '{self.partner_code}'.")))
            return f"Arquivo padrão: {file_name} não encontrado."