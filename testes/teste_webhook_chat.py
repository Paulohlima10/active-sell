#!/usr/bin/env python3
"""
Script de teste para verificar se o webhook_chat não está mais travando
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timezone

# Configurações
WEBHOOK_URL = "http://localhost:8000/webhook_chat"
TEST_PHONE = "5511999999999"
TEST_CLIENT_NAME = "Teste Cliente"

async def test_webhook_response():
    """Testa se o webhook responde corretamente sem travar"""
    print("🧪 Iniciando teste do webhook_chat...")
    
    # Simular payload do WhatsApp
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": f"{TEST_PHONE}@s.whatsapp.net",
                "fromMe": False
            },
            "pushName": TEST_CLIENT_NAME,
            "messageType": "conversation",
            "messageTimestamp": int(time.time()),
            "message": {
                "conversation": "Olá, como você está?"
            }
        }
    }
    
    try:
        print(f"📤 Enviando payload para {WEBHOOK_URL}")
        start_time = time.time()
        
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 segundos de timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Tempo de resposta: {duration:.2f} segundos")
        print(f"📊 Status code: {response.status_code}")
        print(f"📄 Resposta: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook respondeu corretamente!")
            return True
        else:
            print("❌ Webhook retornou erro!")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - Webhook travou!")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar webhook: {e}")
        return False

async def test_multiple_requests():
    """Testa múltiplas requisições simultâneas"""
    print("🧪 Testando múltiplas requisições simultâneas...")
    
    async def send_request(request_id):
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": f"{TEST_PHONE}{request_id}@s.whatsapp.net",
                    "fromMe": False
                },
                "pushName": f"{TEST_CLIENT_NAME} {request_id}",
                "messageType": "conversation",
                "messageTimestamp": int(time.time()),
                "message": {
                    "conversation": f"Teste mensagem {request_id}"
                }
            }
        }
        
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"✅ Requisição {request_id}: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Requisição {request_id} falhou: {e}")
            return False
    
    # Enviar 3 requisições simultâneas
    tasks = [send_request(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    print(f"📊 Resultado: {success_count}/3 requisições bem-sucedidas")
    
    return success_count == 3

async def test_health_endpoint():
    """Testa se outros endpoints ainda funcionam"""
    print("🧪 Testando endpoint de health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint funcionando!")
            return True
        else:
            print("❌ Health endpoint com erro!")
            return False
    except Exception as e:
        print(f"❌ Erro no health endpoint: {e}")
        return False

async def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes de webhook_chat...")
    
    try:
        # Teste 1: Resposta básica
        test1_result = await test_webhook_response()
        
        # Aguardar um pouco
        await asyncio.sleep(2)
        
        # Teste 2: Múltiplas requisições
        test2_result = await test_multiple_requests()
        
        # Aguardar um pouco
        await asyncio.sleep(2)
        
        # Teste 3: Health endpoint
        test3_result = await test_health_endpoint()
        
        # Resultado final
        all_tests_passed = test1_result and test2_result and test3_result
        
        if all_tests_passed:
            print("🎉 Todos os testes passaram! O webhook não está mais travando.")
        else:
            print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        
        return 0 if all_tests_passed else 1
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        return 1

if __name__ == "__main__":
    # Executar testes
    exit_code = asyncio.run(main())
    
    print("🏁 Testes finalizados.")
    exit(exit_code) 