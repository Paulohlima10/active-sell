from agents.simpleAgent import SalesAssistant
from logs.logging_config import log_queue
import asyncio
class SalesAssistantManager:
    def __init__(self):
        self.assistants = {}

    def add_assistant(self, partner_code):
        if partner_code not in self.assistants:
            self.assistants[partner_code] = SalesAssistant(partner_code)

            asyncio.create_task(log_queue.put(("info", f"Assistente para o parceiro '{partner_code}' foi adicionado.")))
        else:
            asyncio.create_task(log_queue.put(("info", f"Assistente para o parceiro '{partner_code}' já existe.")))

    def get_assistant(self, partner_code):
        return self.assistants.get(partner_code, None)
    
    def delete_assistant(self, partner_code):
        """
        Remove um assistente da lista com base no partner_code.
        """
        if partner_code in self.assistants:
            del self.assistants[partner_code]
            asyncio.create_task(log_queue.put(("info", f"Assistente para o parceiro '{partner_code}' foi removido.")))
        else:
            asyncio.create_task(log_queue.put(("info", f"Nenhum assistente encontrado para o parceiro '{partner_code}'.")))

    def agent_exists(self, partner_code):
        """
        Verifica se existe um assistente para o partner_code fornecido.
        Retorna True se existir, False caso contrário.
        """
        return partner_code in self.assistants

# Instância global do gerenciador de assistentes
global_manager = SalesAssistantManager()

# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    async def main():
        manager = SalesAssistantManager()

        while True:
            action = input("\nDigite 'add' para adicionar um assistente, 'ask' para fazer uma pergunta, 'delete' para remover um assistente ou 'sair' para encerrar: ").lower()

            if action == "add":
                partner_code = input("Digite o código do parceiro: ")
                manager.add_assistant(partner_code)

            elif action == "ask":
                partner_code = input("Digite o código do parceiro: ")
                assistant = manager.get_assistant(partner_code)
                if assistant:
                    question = input("Digite sua pergunta: ")
                    resposta = assistant.process_question(question, "1234")
                    print("\nResposta:", resposta)
                else:
                    print(f"Nenhum assistente encontrado para o parceiro '{partner_code}'.")

            elif action == "delete":
                partner_code = input("Digite o código do parceiro que deseja remover: ")
                manager.delete_assistant(partner_code)

            elif action == "sair":
                print("Encerrando o programa...")
                break

            else:
                print("Ação inválida. Tente novamente.")

    asyncio.run(main())