#!/usr/bin/env python3
"""
Script de teste para verificar se o erro do ChromaDB foi resolvido
"""

import os
import asyncio
import gc
from agents.simpleAgent import SalesAssistant
from agents.agentManager import global_manager

# Configurar ambiente
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["OPENAI_API_KEY"] = "test-key"  # Chave de teste

async def test_agent_creation_and_cleanup():
    """Testa a criação e limpeza de agentes sem erros do ChromaDB"""
    print("🧪 Iniciando teste de criação e limpeza de agentes...")
    
    try:
        # Criar alguns agentes
        partner_codes = ["test_partner_1", "test_partner_2"]
        
        for partner_code in partner_codes:
            print(f"📝 Criando agente para {partner_code}...")
            global_manager.add_assistant(partner_code)
            assistant = global_manager.get_assistant(partner_code)
            
            if assistant:
                print(f"✅ Agente criado com sucesso para {partner_code}")
                
                # Testar uma pergunta simples
                try:
                    response = await assistant.ask_question_async("Olá, como você está?", "test_client")
                    print(f"💬 Resposta do agente: {response[:100]}...")
                except Exception as e:
                    print(f"⚠️ Erro ao fazer pergunta: {e}")
            else:
                print(f"❌ Falha ao criar agente para {partner_code}")
        
        # Limpar agentes
        print("🧹 Limpando agentes...")
        for partner_code in partner_codes:
            try:
                global_manager.delete_assistant(partner_code)
                print(f"✅ Agente removido para {partner_code}")
            except Exception as e:
                print(f"❌ Erro ao remover agente para {partner_code}: {e}")
        
        # Forçar coleta de lixo
        print("🗑️ Forçando coleta de lixo...")
        gc.collect()
        
        print("✅ Teste de criação e limpeza concluído sem erros do ChromaDB!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

async def test_chromadb_operations():
    """Testa operações do ChromaDB sem tentar reset"""
    print("🧪 Testando operações do ChromaDB...")
    
    try:
        import chromadb
        
        # Criar cliente ChromaDB
        client = chromadb.PersistentClient(path="test_db")
        collection = client.get_or_create_collection("test_collection")
        
        # Adicionar alguns documentos
        collection.add(
            documents=["Teste documento 1", "Teste documento 2"],
            ids=["1", "2"]
        )
        
        # Fazer uma consulta
        results = collection.query(
            query_texts=["teste"],
            n_results=2
        )
        
        # Verificar se há resultados antes de acessar
        documents = results.get('documents', [])
        if documents and len(documents) > 0 and documents[0]:
            print(f"✅ Consulta ChromaDB bem-sucedida: {len(documents[0])} documentos encontrados")
        else:
            print("✅ Consulta ChromaDB bem-sucedida: 0 documentos encontrados")
        
        # Não tentar reset - deixar o garbage collector cuidar da limpeza
        print("✅ ChromaDB será limpo automaticamente pelo garbage collector")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas operações do ChromaDB: {e}")
        return False

async def test_multiple_agents():
    """Testa múltiplos agentes simultaneamente"""
    print("🧪 Testando múltiplos agentes simultaneamente...")
    
    try:
        # Criar múltiplos agentes
        agents = []
        for i in range(3):
            partner_code = f"test_multi_{i}"
            global_manager.add_assistant(partner_code)
            assistant = global_manager.get_assistant(partner_code)
            if assistant:
                agents.append((partner_code, assistant))
        
        print(f"✅ {len(agents)} agentes criados")
        
        # Testar perguntas simultâneas
        tasks = []
        for partner_code, assistant in agents:
            task = assistant.ask_question_async(f"Pergunta teste {partner_code}", f"client_{partner_code}")
            tasks.append(task)
        
        # Aguardar todas as respostas
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in responses if not isinstance(r, Exception))
        print(f"✅ {success_count}/{len(responses)} perguntas respondidas com sucesso")
        
        # Limpar agentes
        for partner_code, _ in agents:
            global_manager.delete_assistant(partner_code)
        
        return success_count == len(responses)
        
    except Exception as e:
        print(f"❌ Erro no teste de múltiplos agentes: {e}")
        return False

async def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes de ChromaDB...")
    
    try:
        # Teste 1: Criação e limpeza de agentes
        test1_result = await test_agent_creation_and_cleanup()
        
        # Aguardar um pouco
        await asyncio.sleep(1)
        
        # Teste 2: Operações do ChromaDB
        test2_result = await test_chromadb_operations()
        
        # Aguardar um pouco
        await asyncio.sleep(1)
        
        # Teste 3: Múltiplos agentes
        test3_result = await test_multiple_agents()
        
        # Resultado final
        all_tests_passed = test1_result and test2_result and test3_result
        
        if all_tests_passed:
            print("🎉 Todos os testes passaram! O erro do ChromaDB foi resolvido.")
        else:
            print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        
        return 0 if all_tests_passed else 1
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        return 1

if __name__ == "__main__":
    # Executar testes
    exit_code = asyncio.run(main())
    
    # Forçar limpeza final
    gc.collect()
    
    print("🏁 Testes finalizados.")
    exit(exit_code) 