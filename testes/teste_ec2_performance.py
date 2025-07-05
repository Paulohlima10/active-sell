#!/usr/bin/env python3
"""
Script de teste específico para verificar performance no EC2
"""

import asyncio
import time
import psutil
import requests
import json
from datetime import datetime

# Configurações
WEBHOOK_URL = "http://localhost:8000/webhook_chat"
TEST_PHONE = "5511999999999"

async def test_ec2_resources():
    """Testa recursos do EC2"""
    print("🧪 Verificando recursos do EC2...")
    
    # Informações do sistema
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print(f"📊 CPU: {cpu_count} cores")
    print(f"📊 RAM: {memory.total / (1024**3):.1f}GB total, {memory.percent}% usado")
    print(f"📊 DISK: {disk.total / (1024**3):.1f}GB total, {disk.percent}% usado")
    
    # Verificar se é EC2
    try:
        response = requests.get("http://169.254.169.254/latest/meta-data/instance-type", timeout=2)
        instance_type = response.text
        print(f"☁️ EC2 Instance Type: {instance_type}")
        return True
    except:
        print("🏠 Executando localmente (não é EC2)")
        return False

async def test_webhook_performance():
    """Testa performance do webhook"""
    print("🧪 Testando performance do webhook...")
    
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": f"{TEST_PHONE}@s.whatsapp.net",
                "fromMe": False
            },
            "pushName": "Teste Performance",
            "messageType": "conversation",
            "messageTimestamp": int(time.time()),
            "message": {
                "conversation": "Teste de performance"
            }
        }
    }
    
    # Medir tempo de resposta
    start_time = time.time()
    start_memory = psutil.virtual_memory().percent
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        end_memory = psutil.virtual_memory().percent
        
        duration = end_time - start_time
        memory_diff = end_memory - start_memory
        
        print(f"⏱️ Tempo de resposta: {duration:.2f}s")
        print(f"💾 Mudança de RAM: {memory_diff:+.1f}%")
        print(f"📊 Status: {response.status_code}")
        
        if duration < 20:
            print("✅ Performance OK")
            return True
        else:
            print("⚠️ Performance lenta")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def test_concurrent_requests():
    """Testa requisições simultâneas"""
    print("🧪 Testando requisições simultâneas...")
    
    async def send_request(request_id):
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": f"{TEST_PHONE}{request_id}@s.whatsapp.net",
                    "fromMe": False
                },
                "pushName": f"Teste {request_id}",
                "messageType": "conversation",
                "messageTimestamp": int(time.time()),
                "message": {
                    "conversation": f"Teste simultâneo {request_id}"
                }
            }
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            duration = time.time() - start_time
            print(f"✅ Requisição {request_id}: {response.status_code} ({duration:.2f}s)")
            return True
        except Exception as e:
            print(f"❌ Requisição {request_id} falhou: {e}")
            return False
    
    # Enviar 3 requisições simultâneas
    tasks = [send_request(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    print(f"📊 Resultado: {success_count}/3 requisições bem-sucedidas")
    
    return success_count >= 2  # Pelo menos 2 devem funcionar

async def test_health_endpoint():
    """Testa endpoint de health"""
    print("🧪 Testando endpoint de health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint funcionando")
            return True
        else:
            print(f"❌ Health endpoint com erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no health endpoint: {e}")
        return False

async def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes de performance para EC2...")
    
    try:
        # Teste 1: Recursos do EC2
        test1_result = await test_ec2_resources()
        
        # Aguardar um pouco
        await asyncio.sleep(2)
        
        # Teste 2: Performance do webhook
        test2_result = await test_webhook_performance()
        
        # Aguardar um pouco
        await asyncio.sleep(2)
        
        # Teste 3: Requisições simultâneas
        test3_result = await test_concurrent_requests()
        
        # Aguardar um pouco
        await asyncio.sleep(2)
        
        # Teste 4: Health endpoint
        test4_result = await test_health_endpoint()
        
        # Resultado final
        all_tests_passed = test2_result and test3_result and test4_result
        
        if all_tests_passed:
            print("🎉 Todos os testes de performance passaram!")
        else:
            print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        
        return 0 if all_tests_passed else 1
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        return 1

if __name__ == "__main__":
    # Executar testes
    exit_code = asyncio.run(main())
    
    print("🏁 Testes de performance finalizados.")
    exit(exit_code) 