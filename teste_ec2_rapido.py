#!/usr/bin/env python3
"""
Teste rápido para verificar se o sistema está funcionando no EC2
"""

import requests
import json
import time
import psutil
import os

def test_health():
    """Testa endpoint de health"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check OK")
            return True
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_webhook():
    """Testa webhook de chat"""
    try:
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False
                },
                "pushName": "Teste EC2",
                "messageType": "conversation",
                "message": {
                    "conversation": "Olá, teste rápido"
                }
            }
        }
        
        response = requests.post(
            "http://localhost:8000/webhook_chat",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Webhook test OK")
            return True
        else:
            print(f"❌ Webhook test falhou: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro no webhook test: {e}")
        return False

def check_resources():
    """Verifica recursos do sistema"""
    try:
        # Memória
        memory = psutil.virtual_memory()
        print(f"📊 Memória: {memory.percent}% usado ({memory.available // 1024 // 1024}MB livre)")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"📊 CPU: {cpu_percent}%")
        
        # Disco
        disk = psutil.disk_usage('/')
        print(f"📊 Disco: {disk.percent}% usado ({disk.free // 1024 // 1024}MB livre)")
        
        # Processo Python
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if python_processes:
            print(f"📊 Processos Python: {len(python_processes)}")
            for proc in python_processes:
                mem_mb = proc['memory_info'].rss // 1024 // 1024
                print(f"   PID {proc['pid']}: {mem_mb}MB")
        else:
            print("❌ Nenhum processo Python encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao verificar recursos: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando teste rápido do EC2...")
    print("=" * 50)
    
    # Verificar recursos
    print("\n📊 Verificando recursos:")
    check_resources()
    
    # Testar health
    print("\n🏥 Testando health check:")
    health_ok = test_health()
    
    # Testar webhook
    print("\n💬 Testando webhook:")
    webhook_ok = test_webhook()
    
    # Resultado final
    print("\n" + "=" * 50)
    if health_ok and webhook_ok:
        print("✅ SISTEMA FUNCIONANDO CORRETAMENTE!")
    else:
        print("❌ PROBLEMAS DETECTADOS!")
        if not health_ok:
            print("   - Health check falhou")
        if not webhook_ok:
            print("   - Webhook falhou")
    
    print("\n📋 Para ver logs em tempo real:")
    print("   tail -f app.log")
    print("\n📋 Para parar o servidor:")
    print("   pkill -f 'python3 main.py'")

if __name__ == "__main__":
    main() 