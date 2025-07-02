import os
import json
from crewai import Agent, Task, Crew
from agents.ChatHistory import ChatHistoryManager
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai import Knowledge
from logs.logging_config import log_queue
import asyncio


class SalesAssistant:
    def __init__(self, partner_code):
        # Configurar chave de API
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is not None:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            print("AVISO: OPENAI_API_KEY não está definida nas variáveis de ambiente.")

        # Inicializar o gerenciador de histórico de chat
        self.chat_history = ChatHistoryManager()

        # Configurar a base de conhecimento inicial
        self.partner_code = partner_code
        self.update_knowledge(partner_code)

        # Carregar os arquivos da base de conhecimento
        self.role = self.load_file(partner_code, "role.txt")
        self.goal = self.load_file(partner_code, "goal.txt")
        self.backstory = self.load_file(partner_code, "backstory.txt")
        self.name = self.load_file(partner_code, "name.txt")
        self.task_description = self.load_file(partner_code, "task_description.txt")

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
            knowledge=self.knowledge,
            verbose=False
        )

    def update_knowledge(self, partner_code):
        """
        Atualiza a base de conhecimento com base no código do parceiro.
        """
        knowledge_path = os.path.join("partners", partner_code)
        document_path = os.path.join(knowledge_path, "document.txt")

        knowledge_path2 = os.path.join("knowledge", "partners", partner_code)
        document_path2 = os.path.join(knowledge_path2, "document.txt")

        if os.path.exists(document_path2):
            asyncio.create_task(log_queue.put(("info", f"Atualizando base de conhecimento com o arquivo: {document_path}")))
            text_source = TextFileKnowledgeSource(file_paths=[document_path])
            self.knowledge = Knowledge(
                collection_name=f"vendas_farmacia_{partner_code}",
                sources=[text_source]
            )
        else:
            asyncio.create_task(log_queue.put(("info", f"O arquivo de conhecimento '{document_path}' não foi encontrado. Usando base de conhecimento vazia.")))
            self.knowledge = Knowledge(
                collection_name=f"vendas_farmacia_{partner_code}",
                sources=[]
            )

    def create_sale_agent(self):
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            knowledge=self.knowledge,
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
            description=self.task_description,
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

    def process_question(self, question, phone_number):
        # Executar a tarefa do CrewAI
        result = self.crew.kickoff(inputs={
            "question": question,
            "historico": self.chat_history.get_history_string(phone_number),
            "contexto": "contexto"
        })

        # Processar a resposta
        resposta_json = json.loads(str(result))
        resposta = resposta_json.get("Resposta", "Erro ao obter resposta")

        # Atualizar o histórico de chat
        self.chat_history.add_message(phone_number, "user", question)
        self.chat_history.add_message(phone_number, "assistant", resposta)

        return resposta
    
    def ask_question(self, question, client_id):
        # Executar a tarefa do CrewAI
        result = self.crew.kickoff(inputs={
            "question": question,
            "historico": self.chat_history.get_history_string(client_id),
            "contexto": "contexto"
        })

        # Processar a resposta
        resposta_json = json.loads(str(result))
        resposta = resposta_json.get("Resposta", "Erro ao obter resposta")

        # Atualizar o histórico de chat
        self.chat_history.add_message(client_id, "user", question)
        self.chat_history.add_message(client_id, "assistant", resposta)

        return resposta
    
    def load_file(self, partner_code, file_name):
        """
        Lê um arquivo específico da base de conhecimento do parceiro e retorna o conteúdo.
        """
        knowledge_path = os.path.join("knowledge", "partners", partner_code)
        file_path = os.path.join(knowledge_path, file_name)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                asyncio.create_task(log_queue.put(("info", f"Conteúdo do arquivo '{file_name}' carregado para o parceiro '{partner_code}'")))
                return content
        else:
            asyncio.create_task(log_queue.put(("info", f"O arquivo '{file_name}' não foi encontrado para o parceiro '{partner_code}'."))) 
            return f"Arquivo padrão: {file_name} não encontrado."


# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    async def main():

        while True:
            assistant = SalesAssistant("00001")
            if assistant:
                question = input("Digite sua pergunta: ")
                resposta = assistant.process_question(question, "1234")
                print("\nResposta:", resposta)
            

    asyncio.run(main())