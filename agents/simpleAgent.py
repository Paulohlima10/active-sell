import os
import json
from crewai import Agent, Task, Crew
from agents.ChatHistory import chat_history_global
from logs.logging_config import log_queue
import asyncio
import chromadb
import atexit
import concurrent.futures

# Desabilitar telemetria do ChromaDB para evitar erros
os.environ["CHROMA_TELEMETRY"] = "false"


class SalesAssistant:
    def __init__(self, partner_code):
        # Configurar chave de API
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is not None:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            print("AVISO: OPENAI_API_KEY não está definida nas variáveis de ambiente.")

        # Inicializar o gerenciador de histórico de chat
        self.chat_history = chat_history_global

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
            verbose=False
        )

        # ChromaDB: indexação única
        self.collection_name = f"vendas_farmacia_{partner_code}"
        self.chroma_client = chromadb.PersistentClient(path="db")
        self.chroma_collection = self.chroma_client.get_or_create_collection(self.collection_name)
        document_path = os.path.join("knowledge", "partners", partner_code, "document.txt")
        if os.path.exists(document_path) and len(self.chroma_collection.get()['ids']) == 0:
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
                docs = [x.strip() for x in content.split("\n") if x.strip()]
                ids = [str(i) for i in range(1, len(docs)+1)]
                if docs:
                    self.chroma_collection.add(documents=docs, ids=ids)
        
        # Registrar função de limpeza para ser executada no shutdown
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        Método para limpar recursos e evitar vazamentos de semáforos
        """
        try:
            if hasattr(self, 'chroma_client'):
                # Tentar limpar recursos do ChromaDB
                if hasattr(self.chroma_client, 'reset'):
                    self.chroma_client.reset()
        except Exception as e:
            print(f"Erro durante limpeza do SalesAssistant: {e}")

    def update_knowledge(self, partner_code):
        """
        Atualiza a base de conhecimento do parceiro no ChromaDB, removendo todos os dados da coleção e inserindo novamente o conteúdo do arquivo document.txt.
        """
        collection_name = f"vendas_farmacia_{partner_code}"
        document_path = os.path.join("knowledge", "partners", partner_code, "document.txt")
        chroma_client = chromadb.PersistentClient(path="db")
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        # Apagar todos os dados da coleção
        ids_existentes = chroma_collection.get()['ids']
        if ids_existentes:
            chroma_collection.delete(ids=ids_existentes)
        # Inserir novamente o conteúdo do arquivo
        if os.path.exists(document_path):
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
                docs = [x.strip() for x in content.split("\n") if x.strip()]
                ids = [str(i) for i in range(1, len(docs)+1)]
                if docs:
                    chroma_collection.add(documents=docs, ids=ids)
        
        # Limpar recursos do ChromaDB temporário
        try:
            if hasattr(chroma_client, 'reset'):
                chroma_client.reset()
        except Exception as e:
            print(f"Erro durante limpeza do ChromaDB temporário: {e}")

    def create_sale_agent(self):
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
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
    
    async def ask_question_async(self, question, client_id):
        """
        Versão assíncrona do ask_question para evitar bloqueios no event loop
        """
        try:
            # Buscar contexto relevante no ChromaDB já indexado
            results = self.chroma_collection.query(
                query_texts=[question],
                n_results=3,
                include=["distances", "documents"]
            )
            docs = []
            if results['documents'] and results['distances']:
                for doc, dist in zip(results['documents'][0], results['distances'][0]):
                    if dist < 0.8:  # ajuste esse valor conforme necessário
                        docs.append(doc)
            contexto = "\n".join(docs)
            if not contexto:
                contexto = "Nenhuma informação relevante encontrada na base de conhecimento."

            # Executar a tarefa do CrewAI em um thread separado para não bloquear o event loop
            def run_crew_kickoff():
                try:
                    return self.crew.kickoff(inputs={
                        "question": question,
                        "historico": self.chat_history.get_history_string(client_id),
                        "contexto": contexto
                    })
                except Exception as e:
                    print(f"Erro no CrewAI kickoff: {e}")
                    # Retornar resposta de fallback
                    return json.dumps({
                        "Resposta": f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}",
                        "Classificacao": "Prospecção"
                    })
            
            # Executar em thread separado com retry
            loop = asyncio.get_event_loop()
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        result = await loop.run_in_executor(executor, run_crew_kickoff)
                    break
                except Exception as e:
                    print(f"Tentativa {attempt + 1} falhou: {e}")
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(1)  # Esperar 1 segundo antes de tentar novamente

            # Processar a resposta
            try:
                resposta_json = json.loads(str(result))
                resposta = resposta_json.get("Resposta", "Erro ao obter resposta")
            except json.JSONDecodeError:
                resposta = f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}"

            # Atualizar o histórico de chat
            self.chat_history.add_message(client_id, "user", question)
            self.chat_history.add_message(client_id, "assistant", resposta)

            return resposta
            
        except Exception as e:
            print(f"Erro no ask_question_async: {e}")
            # Resposta de fallback em caso de erro
            fallback_response = f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}"
            self.chat_history.add_message(client_id, "user", question)
            self.chat_history.add_message(client_id, "assistant", fallback_response)
            return fallback_response
    
    def ask_question(self, question, client_id):
        """
        Versão síncrona mantida para compatibilidade
        """
        # Buscar contexto relevante no ChromaDB já indexado
        results = self.chroma_collection.query(
            query_texts=[question],
            n_results=3,
            include=["distances", "documents"]
        )
        docs = []
        if results['documents'] and results['distances']:
            for doc, dist in zip(results['documents'][0], results['distances'][0]):
                if dist < 0.8:  # ajuste esse valor conforme necessário
                    docs.append(doc)
        contexto = "\n".join(docs)
        if not contexto:
            contexto = "Nenhuma informação relevante encontrada na base de conhecimento."

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
        client = chromadb.PersistentClient(path="db")

        assistant = SalesAssistant("95aed0d0-303e-45cd-a37e-364bff24849f")  # Instancie só uma vez!
        while True:
            question = input("Digite sua pergunta: ")
            resposta = assistant.ask_question(question, "1234")
            print("\nResposta:", resposta)

    asyncio.run(main())