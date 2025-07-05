#!/usr/bin/env python3
"""
Teste específico para verificar se o CrewAI está funcionando no EC2
"""

import requests
import json
import time
import psutil
import os

def test_crewai_response():
    """Testa se o CrewAI está respondendo corretamente"""
    try:
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False
                },
                "pushName": "Teste CrewAI",
                "messageType": "conversation",
                "message": {
                    "conversation": "Quais são os produtos mais vendidos da farmácia?"
                }
            }
        }
        
        print("🤖 Testando resposta do CrewAI...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/webhook_chat",
            json=payload,
            timeout=15  # 15 segundos para CrewAI
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ CrewAI respondeu em {processing_time:.2f} segundos")
            print(f"📝 Resposta: {response.text[:200]}...")
            return True
        else:
            print(f"❌ CrewAI falhou: {response.status_code}")
            print(f"📝 Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro no teste CrewAI: {e}")
        return False

def test_simple_response():
    """Testa resposta simples para comparar"""
    try:
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False
                },
                "pushName": "Teste Simples",
                "messageType": "conversation",
                "message": {
                    "conversation": "Olá"
                }
            }
        }
        
        print("👋 Testando resposta simples...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/webhook_chat",
            json=payload,
            timeout=10
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ Resposta simples em {processing_time:.2f} segundos")
            return True
        else:
            print(f"❌ Resposta simples falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no teste simples: {e}")
        return False

def check_memory_usage():
    """Verifica uso de memória durante os testes"""
    try:
        # Encontrar processo Python
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if python_processes:
            print(f"\n📊 Processos Python encontrados: {len(python_processes)}")
            total_memory = 0
            for proc in python_processes:
                mem_mb = proc['memory_info'].rss // 1024 // 1024
                total_memory += mem_mb
                print(f"   PID {proc['pid']}: {mem_mb}MB")
            print(f"   Total: {total_memory}MB")
            
            if total_memory > 500:  # Mais de 500MB
                print("⚠️ ALERTA: Uso de memória alto!")
            else:
                print("✅ Uso de memória OK")
        else:
            print("❌ Nenhum processo Python encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao verificar memória: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 Teste específico do CrewAI no EC2")
    print("=" * 50)
    
    # Verificar se servidor está rodando
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Servidor não está respondendo")
            return
        print("✅ Servidor está rodando")
    except Exception as e:
        print(f"❌ Erro ao conectar com servidor: {e}")
        return
    
    # Verificar memória antes dos testes
    print("\n📊 Memória antes dos testes:")
    check_memory_usage()
    
    # Teste simples
    print("\n" + "=" * 30)
    simple_ok = test_simple_response()
    
    # Aguardar um pouco
    time.sleep(2)
    
    # Teste CrewAI
    print("\n" + "=" * 30)
    crewai_ok = test_crewai_response()
    
    # Verificar memória após os testes
    print("\n📊 Memória após os testes:")
    check_memory_usage()
    
    # Resultado final
    print("\n" + "=" * 50)
    if simple_ok and crewai_ok:
        print("✅ CREWAI FUNCIONANDO CORRETAMENTE!")
        print("   - Resposta simples: OK")
        print("   - Resposta CrewAI: OK")
    else:
        print("❌ PROBLEMAS DETECTADOS!")
        if not simple_ok:
            print("   - Resposta simples falhou")
        if not crewai_ok:
            print("   - Resposta CrewAI falhou")
    
    print("\n📋 Para ver logs em tempo real:")
    print("   tail -f app.log")
    print("\n📋 Para parar o servidor:")
    print("   pkill -f 'python3 main.py'")

if __name__ == "__main__":
    main() 