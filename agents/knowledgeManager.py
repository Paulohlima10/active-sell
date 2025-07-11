import os
import chromadb

class KnowledgeManager:
    def __init__(self, partner_code):
        # Configurar ChromaDB
        os.environ["CHROMA_TELEMETRY"] = "false"
        self.partner_code = partner_code
        self.collection_name = f"knowledge_collection_{partner_code}"
        self.chroma_client = chromadb.PersistentClient(path="db")
        self.chroma_collection = self.chroma_client.get_or_create_collection(self.collection_name)
        
        # Inicializar a base de conhecimento
        self.initialize_knowledge()

    def initialize_knowledge(self):
        """Inicializa a base de conhecimento no ChromaDB"""
        document_path = os.path.join("knowledge", "partners", self.partner_code, "document.txt")
        if os.path.exists(document_path) and len(self.chroma_collection.get()['ids']) == 0:
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
                docs = [x.strip() for x in content.split("\n") if x.strip()]
                ids = [str(i) for i in range(1, len(docs)+1)]
                if docs:
                    self.chroma_collection.add(documents=docs, ids=ids)

    def update_knowledge(self):
        """Atualiza a base de conhecimento do parceiro no ChromaDB"""
        document_path = os.path.join("knowledge", "partners", self.partner_code, "document.txt")
        
        # Apagar todos os dados da coleção
        ids_existentes = self.chroma_collection.get()['ids']
        if ids_existentes:
            self.chroma_collection.delete(ids=ids_existentes)
            
        # Inserir novamente o conteúdo do arquivo
        if os.path.exists(document_path):
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
                docs = [x.strip() for x in content.split("\n") if x.strip()]
                ids = [str(i) for i in range(1, len(docs)+1)]
                if docs:
                    self.chroma_collection.add(documents=docs, ids=ids)

    def get_context(self, question, max_results=3, distance_threshold=0.8):
        """Busca contexto relevante para uma pergunta"""
        try:
            results = self.chroma_collection.query(
                query_texts=[question],
                n_results=max_results,
                include=["distances", "documents"]
            )
            docs = []
            if results.get('documents') and results.get('distances'):
                for doc, dist in zip(results['documents'][0], results['distances'][0]):
                    if dist < distance_threshold:
                        docs.append(doc)
            return "\n".join(docs) if docs else "Informações básicas disponíveis."
        except Exception as e:
            print(f"Erro ao buscar contexto: {e}")
            return "Informações básicas disponíveis."