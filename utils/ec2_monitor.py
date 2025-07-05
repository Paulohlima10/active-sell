#!/usr/bin/env python3
"""
Monitoramento específico para EC2 AWS
"""

import os
import asyncio
import time
from datetime import datetime

# Importações opcionais para evitar falhas
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Aviso: psutil não disponível - monitoramento de recursos limitado")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Aviso: requests não disponível - monitoramento de rede limitado")

try:
    from logs.logging_config import log_message
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    print("Aviso: logging não disponível - logs limitados")

class EC2Monitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    async def log_system_resources(self):
        """Loga recursos do sistema"""
        if not PSUTIL_AVAILABLE:
            print("EC2_MONITOR - psutil não disponível, pulando monitoramento de recursos")
            return
            
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            message = f"EC2_MONITOR - CPU: {cpu_percent}%, RAM: {memory.percent}%, DISK: {disk.percent}%"
            
            if LOGGING_AVAILABLE:
                await log_message("info", message)
            else:
                print(message)
            
            # Alertas se recursos estiverem altos
            if cpu_percent > 80:
                alert = f"EC2_MONITOR - CPU alta: {cpu_percent}%"
                if LOGGING_AVAILABLE:
                    await log_message("warning", alert)
                else:
                    print(f"⚠️ {alert}")
            if memory.percent > 80:
                alert = f"EC2_MONITOR - RAM alta: {memory.percent}%"
                if LOGGING_AVAILABLE:
                    await log_message("warning", alert)
                else:
                    print(f"⚠️ {alert}")
            if disk.percent > 80:
                alert = f"EC2_MONITOR - DISK alta: {disk.percent}%"
                if LOGGING_AVAILABLE:
                    await log_message("warning", alert)
                else:
                    print(f"⚠️ {alert}")
                
        except Exception as e:
            error_msg = f"EC2_MONITOR - Erro ao monitorar recursos: {e}"
            if LOGGING_AVAILABLE:
                await log_message("error", error_msg)
            else:
                print(f"❌ {error_msg}")
    
    async def log_network_status(self):
        """Loga status da rede"""
        if not REQUESTS_AVAILABLE:
            print("EC2_MONITOR - requests não disponível, pulando monitoramento de rede")
            return
            
        try:
            # Teste OpenAI
            try:
                response = requests.get("https://api.openai.com", timeout=5)
                openai_status = "OK" if response.status_code < 500 else "ERRO"
            except:
                openai_status = "TIMEOUT"
            
            # Teste Supabase
            try:
                response = requests.get("https://supabase.com", timeout=5)
                supabase_status = "OK" if response.status_code < 500 else "ERRO"
            except:
                supabase_status = "TIMEOUT"
            
            message = f"EC2_MONITOR - OpenAI: {openai_status}, Supabase: {supabase_status}"
            if LOGGING_AVAILABLE:
                await log_message("info", message)
            else:
                print(message)
            
        except Exception as e:
            error_msg = f"EC2_MONITOR - Erro ao testar rede: {e}"
            if LOGGING_AVAILABLE:
                await log_message("error", error_msg)
            else:
                print(f"❌ {error_msg}")
    
    async def log_performance_metrics(self):
        """Loga métricas de performance"""
        uptime = time.time() - self.start_time
        avg_response_time = 0  # Implementar cálculo de tempo médio
        
        message = f"EC2_MONITOR - Uptime: {uptime:.0f}s, Requests: {self.request_count}, Errors: {self.error_count}"
        if LOGGING_AVAILABLE:
            await log_message("info", message)
        else:
            print(message)
    
    async def monitor_loop(self):
        """Loop principal de monitoramento"""
        while True:
            try:
                await self.log_system_resources()
                await self.log_network_status()
                await self.log_performance_metrics()
                
                # Aguardar 30 segundos antes do próximo monitoramento
                await asyncio.sleep(30)
                
            except Exception as e:
                error_msg = f"EC2_MONITOR - Erro no loop de monitoramento: {e}"
                if LOGGING_AVAILABLE:
                    await log_message("error", error_msg)
                else:
                    print(f"❌ {error_msg}")
                await asyncio.sleep(30)
    
    def increment_request(self):
        """Incrementa contador de requisições"""
        self.request_count += 1
    
    def increment_error(self):
        """Incrementa contador de erros"""
        self.error_count += 1

# Instância global do monitor
ec2_monitor = EC2Monitor()

async def start_ec2_monitoring():
    """Inicia o monitoramento do EC2"""
    message = "EC2_MONITOR - Iniciando monitoramento do EC2"
    if LOGGING_AVAILABLE:
        await log_message("info", message)
    else:
        print(message)
    asyncio.create_task(ec2_monitor.monitor_loop())

def get_ec2_info():
    """Retorna informações do EC2"""
    try:
        # Verificar se está rodando no EC2
        if not REQUESTS_AVAILABLE:
            return {
                "is_ec2": False,
                "instance_type": "unknown",
                "cpu_count": psutil.cpu_count() if PSUTIL_AVAILABLE else "unknown",
                "memory_gb": psutil.virtual_memory().total / (1024**3) if PSUTIL_AVAILABLE else "unknown"
            }
        
        response = requests.get("http://169.254.169.254/latest/meta-data/instance-type", timeout=2)
        instance_type = response.text
        return {
            "is_ec2": True,
            "instance_type": instance_type,
            "cpu_count": psutil.cpu_count() if PSUTIL_AVAILABLE else "unknown",
            "memory_gb": psutil.virtual_memory().total / (1024**3) if PSUTIL_AVAILABLE else "unknown"
        }
    except:
        return {
            "is_ec2": False,
            "instance_type": "local",
            "cpu_count": psutil.cpu_count() if PSUTIL_AVAILABLE else "unknown",
            "memory_gb": psutil.virtual_memory().total / (1024**3) if PSUTIL_AVAILABLE else "unknown"
        }

if __name__ == "__main__":
    # Teste do monitor
    async def test_monitor():
        await start_ec2_monitoring()
        await asyncio.sleep(60)  # Rodar por 1 minuto
    
    print("Iniciando teste do monitor EC2...")
    asyncio.run(test_monitor()) 