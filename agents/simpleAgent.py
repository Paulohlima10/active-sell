import os
import json
from crewai import Agent, Task, Crew
from agents.ChatHistory import chat_history_global
from agents.knowledgeManager import KnowledgeManager
from agents.promptManager import PromptManager
import asyncio
import atexit
import concurrent.futures

class SalesAssistant:
    def __init__(self, partner_code):
        # Configurar chave de API
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is not None:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            print("AVISO: OPENAI_API_KEY não está definida nas variáveis de ambiente.")

        # Inicializar gerenciadores
        self.chat_history = chat_history_global
        self.knowledge_manager = KnowledgeManager(partner_code)
        self.prompt_manager = PromptManager(partner_code)

        # Configurar agentes
        self.sale_agent = self.create_sale_agent()
        self.classification_agent = self.create_classification_agent()

        # Configurar tarefas
        self.sale_task = self.create_sale_task()
        self.classification_task = self.create_classification_task()

        # Configurar CrewAI
        self.crew = Crew(
            agents=[self.sale_agent, self.classification_agent],
            tasks=[self.sale_task, self.classification_task],
            verbose=False
        )

    def create_sale_agent(self):
        return Agent(
            role=self.prompt_manager.role,
            goal=self.prompt_manager.goal,
            backstory=self.prompt_manager.backstory,
            verbose=False
        )

    def create_classification_agent(self):
        return Agent(
            role="Analisa o histórico da conversa e classifica o cliente no funil de vendas.",
            goal="Determinar se o cliente está na fase de prospecção, consideração ou decisão de compra.",
            backstory="Especialista em analisar comportamento do cliente.",
            verbose=False
        )

    def create_sale_task(self):
        return Task(
            description=self.prompt_manager.task_description,
            expected_output=json.dumps({
                "Resposta": "resposta do agente Vendedor",
                "Classificacao": "Prospecção"
            }),
            agent=self.sale_agent
        )

    def create_classification_task(self):
        return Task(
            description="Receber o histórico da conversa e classificar o estágio do cliente no funil de vendas. Historico: {historico}",
            expected_output=json.dumps({
                "Resposta": "resposta do agente apropriado",
                "Classificacao": "Prospecção"
            }),
            agent=self.classification_agent
        )
    
    def ask_question(self, question, client_id):
        """Versão síncrona mantida para compatibilidade"""
        # Buscar contexto relevante
        contexto = self.knowledge_manager.get_context(question)

        # Executar a tarefa do CrewAI
        result = self.crew.kickoff(inputs={
            "question": question,
            "historico": self.chat_history.get_history_string(client_id),
            "contexto": contexto
        })

        # Processar a resposta
        resposta_json = json.loads(str(result))
        resposta = resposta_json.get("Resposta", "Erro ao obter resposta")

        # Atualizar o histórico de chat
        self.chat_history.add_message(client_id, "user", question)
        self.chat_history.add_message(client_id, "assistant", resposta)

        return resposta

# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    async def main():
        assistant = SalesAssistant("95aed0d0-303e-45cd-a37e-364bff24849f")  # Instancie só uma vez!
        while True:
            question = input("Digite sua pergunta: ")
            resposta = assistant.ask_question(question, "1234")
            print("\nResposta:", resposta)

    asyncio.run(main())