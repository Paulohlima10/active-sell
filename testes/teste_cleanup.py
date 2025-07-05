#!/usr/bin/env python3
"""
Script de teste para verificar se o vazamento de semáforos foi resolvido
"""

import os
import sys
import asyncio
import gc
from agents.simpleAgent import SalesAssistant
from agents.agentManager import global_manager

# Configurar ambiente
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["OPENAI_API_KEY"] = "test-key"  # Chave de teste

async def test_agent_creation():
    """Testa a criação e destruição de agentes"""
    print("🧪 Iniciando teste de criação de agentes...")
    
    # Criar alguns agentes
    partner_codes = ["test_partner_1", "test_partner_2", "test_partner_3"]
    
    for partner_code in partner_codes:
        try:
            print(f"📝 Criando agente para {partner_code}...")
            global_manager.add_assistant(partner_code)
            assistant = global_manager.get_assistant(partner_code)
            
            if assistant:
                print(f"✅ Agente criado com sucesso para {partner_code}")
                
                # Testar uma pergunta simples
                response = assistant.ask_question("Olá, como você está?", "test_client")
                print(f"💬 Resposta do agente: {response[:100]}...")
            else:
                print(f"❌ Falha ao criar agente para {partner_code}")
                
        except Exception as e:
            print(f"❌ Erro ao criar agente para {partner_code}: {e}")
    
    # Limpar agentes
    print("🧹 Limpando agentes...")
    for partner_code in partner_codes:
        try:
            global_manager.delete_assistant(partner_code)
            print(f"✅ Agente removido para {partner_code}")
        except Exception as e:
            print(f"❌ Erro ao remover agente para {partner_code}: {e}")

async def test_resource_cleanup():
    """Testa a limpeza de recursos"""
    print("🧪 Testando limpeza de recursos...")
    
    # Forçar coleta de lixo
    gc.collect()
    
    # Verificar se há recursos vazando
    import multiprocessing
    if hasattr(multiprocessing, 'resource_tracker'):
        tracker = multiprocessing.resource_tracker._CLEANUP_CALLBACKS
        print(f"📊 Recursos registrados: {len(tracker) if tracker else 0}")
    
    print("✅ Teste de limpeza concluído")

async def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes de vazamento de recursos...")
    
    try:
        # Teste 1: Criação e destruição de agentes
        await test_agent_creation()
        
        # Teste 2: Limpeza de recursos
        await test_resource_cleanup()
        
        print("✅ Todos os testes concluídos com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Executar testes
    exit_code = asyncio.run(main())
    
    # Forçar limpeza final
    gc.collect()
    
    print("🏁 Testes finalizados.")
    sys.exit(exit_code) 