from typing import List, Dict, Optional

class ChatHistoryManager:
    def __init__(self):
        """
        Inicializa o gerenciador de histórico de chat.
        O histórico será armazenado em um dicionário onde a chave é a thread_id.
        """
        self.chat_histories: Dict[str, List[Dict[str, str]]] = {}

    def add_message(self, thread_id: str, role: str, content: str):
        """
        Adiciona uma mensagem ao histórico da thread.

        :param thread_id: Identificador único da conversa.
        :param role: Papel da mensagem ('system', 'user' ou 'assistant').
        :param content: Conteúdo da mensagem.
        """
        if role not in {"system", "user", "assistant"}:
            raise ValueError("O 'role' deve ser 'system', 'user' ou 'assistant'.")

        if thread_id not in self.chat_histories:
            self.chat_histories[thread_id] = []

        self.chat_histories[thread_id].append({"role": role, "content": content})

    def get_history(self, thread_id: str) -> List[Dict[str, str]]:
        """
        Retorna o histórico completo de uma thread específica.

        :param thread_id: Identificador único da conversa.
        :return: Lista de mensagens no formato [{"role": "user", "content": "texto"}].
        """
        return self.chat_histories.get(thread_id, [])

    def clear_history(self, thread_id: str):
        """
        Remove o histórico de uma thread específica.

        :param thread_id: Identificador único da conversa.
        """
        if thread_id in self.chat_histories:
            del self.chat_histories[thread_id]

    def get_history_string(self, thread_id: str) -> str:
        """
        Retorna o histórico de uma thread como uma string legível.

        :param thread_id: Identificador único da conversa.
        :return: String formatada com o histórico da thread.
        """
        history = self.get_history(thread_id)

        # Verifica se há histórico válido
        if not history or not isinstance(history, list):
            return "⚠️ Nenhum histórico encontrado para esta thread."

        formatted_history = []
        for msg in history:
            # Validação para evitar KeyError
            role = msg.get("role", "Desconhecido").capitalize()
            content = msg.get("content", "[Mensagem sem conteúdo]")

            formatted_history.append(f"🔹 {role}: {content}")

        return "\n".join(formatted_history)

# Exemplo de Uso
if __name__ == "__main__":
    chat_manager = ChatHistoryManager()

    # Criando uma thread e adicionando mensagens
    thread_id = "12345"
    chat_manager.add_message(thread_id, "system", "Você é um assistente de IA.")
    chat_manager.add_message(thread_id, "user", "Qual é a capital da França?")
    chat_manager.add_message(thread_id, "assistant", "A capital da França é Paris.")

    # Exibindo o histórico formatado
    print("📜 Histórico da Conversa:")
    print(chat_manager.get_history_string(thread_id))

    # Limpando a conversa e verificando se foi apagada
    chat_manager.clear_history(thread_id)
    print("\n🔄 Histórico após limpeza:")
    print(chat_manager.get_history_string(thread_id))
