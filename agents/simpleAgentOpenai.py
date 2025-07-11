import os
import json
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
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
            self.client = OpenAI(api_key=api_key)
        else:
            print("AVISO: OPENAI_API_KEY não está definida nas variáveis de ambiente.")
            self.client = None
        
        # Configurações otimizadas para EC2
        os.environ["OMP_NUM_THREADS"] = "1"
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"
        os.environ["NUMEXPR_NUM_THREADS"] = "1"

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
                # ChromaDB não precisa de limpeza explícita
                # O garbage collector cuidará da limpeza
                pass
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
        
        # ChromaDB temporário será limpo automaticamente pelo garbage collector
        # Não é necessário limpeza explícita

    def create_system_prompt(self):
        """
        Cria o prompt do sistema com base nos arquivos carregados
        """
        return f"""Você é {self.name}, {self.role}

{self.backstory}

Seu objetivo: {self.goal}

{self.task_description}

Você deve responder de forma natural e conversacional, sempre em português brasileiro.
Sua resposta deve ser útil, precisa e focada no cliente."""

    def process_question(self, question, phone_number):
        # Executar a pergunta usando OpenAI
        if not self.client:
            return "Erro: API key não configurada"
        
        try:
            # Buscar contexto relevante no ChromaDB
            results = self.chroma_collection.query(
                query_texts=[question],
                n_results=2,
                include=["distances", "documents"]
            )
            docs = []
            if results.get('documents') and results.get('distances'):
                documents = results['documents']
                distances = results['distances']
                if documents and distances and len(documents) > 0 and len(distances) > 0:
                    for doc, dist in zip(documents[0], distances[0]):
                        if dist < 0.8:
                            docs.append(doc)
            contexto = "\n".join(docs) if docs else "Informações básicas disponíveis."

            # Obter histórico de chat
            historico = self.chat_history.get_history_string(phone_number)
            
            # Criar mensagens para o chat
            messages: list = [
                ChatCompletionSystemMessageParam(role="system", content=self.create_system_prompt()),
                ChatCompletionUserMessageParam(role="user", content=f"Contexto: {contexto}\n\nHistórico da conversa: {historico}\n\nPergunta do cliente: {question}")
            ]

            # Fazer chamada para OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            resposta = response.choices[0].message.content or "Erro ao obter resposta"

            # Atualizar o histórico de chat
            self.chat_history.add_message(phone_number, "user", question)
            self.chat_history.add_message(phone_number, "assistant", resposta)

            return resposta

        except Exception as e:
            print(f"Erro no process_question: {e}")
            return f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}"
    
    async def ask_question_async(self, question, client_id):
        """
        Versão assíncrona otimizada para EC2 com OpenAI
        """
        try:
            if not self.client:
                return "Erro: API key não configurada"

            # Buscar contexto relevante no ChromaDB (limitado a 1 resultado para economizar)
            try:
                results = self.chroma_collection.query(
                    query_texts=[question],
                    n_results=1,  # Limitado a 1 resultado para economizar memória
                    include=["distances", "documents"]
                )
                docs = []
                if results.get('documents') and results.get('distances'):
                    documents = results['documents']
                    distances = results['distances']
                    if documents and distances and len(documents) > 0 and len(distances) > 0:
                        for doc, dist in zip(documents[0], distances[0]):
                            if dist < 0.8:
                                docs.append(doc)
                contexto = "\n".join(docs) if docs else "Informações básicas disponíveis."
            except Exception as e:
                print(f"Erro ao buscar contexto: {e}")
                contexto = "Informações básicas disponíveis."

            # Executar OpenAI em thread separada com timeout e retry
            def run_openai_request():
                try:
                    if not self.client:
                        return "Erro: API key não configurada"
                        
                    # Limitar histórico para economizar memória (muito conservador)
                    historico_limitado = self.chat_history.get_history_string(client_id)
                    if len(historico_limitado) > 500:  # Limitar a 500 caracteres
                        historico_limitado = historico_limitado[-500:]
                    
                    # Criar mensagens para o chat
                    messages = [
                        ChatCompletionSystemMessageParam(role="system", content=self.create_system_prompt()),
                        ChatCompletionUserMessageParam(role="user", content=f"Contexto: {contexto}\n\nHistórico da conversa: {historico_limitado}\n\nPergunta do cliente: {question}")
                    ]

                    # Fazer chamada para OpenAI
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        max_tokens=500,
                        temperature=0.7
                    )

                    return response.choices[0].message.content or "Erro ao obter resposta"
                except Exception as e:
                    print(f"Erro no OpenAI request: {e}")
                    # Retornar resposta de fallback
                    return f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}"
            
            # Executar em thread separada com timeout muito conservador
            loop = asyncio.get_event_loop()
            max_retries = 1  # Apenas 1 retry para economizar recursos
            for attempt in range(max_retries + 1):
                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        result = await loop.run_in_executor(executor, run_openai_request)
                    break
                except Exception as e:
                    print(f"Tentativa {attempt + 1} falhou: {e}")
                    if attempt == max_retries:
                        raise e
                    await asyncio.sleep(0.5)  # Esperar 0.5 segundos antes de tentar novamente

            # Atualizar o histórico de chat
            try:
                self.chat_history.add_message(client_id, "user", question)
                self.chat_history.add_message(client_id, "assistant", result)
            except Exception as e:
                print(f"Erro ao atualizar histórico: {e}")

            return result
            
        except Exception as e:
            print(f"Erro no ask_question_async: {e}")
            # Resposta de fallback em caso de erro
            fallback_response = f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}"
            try:
                self.chat_history.add_message(client_id, "user", question)
                self.chat_history.add_message(client_id, "assistant", fallback_response)
            except:
                pass
            return fallback_response
    
    def ask_question(self, question, client_id):
        """
        Versão síncrona mantida para compatibilidade
        """
        return self.process_question(question, client_id)
    
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