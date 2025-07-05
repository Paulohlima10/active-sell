#!/usr/bin/env python3
"""
Monitoramento específico para EC2 AWS
"""

import os
import psutil
import asyncio
import time
from datetime import datetime
from logs.logging_config import log_message

class EC2Monitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    async def log_system_resources(self):
        """Loga recursos do sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            await log_message("info", f"EC2_MONITOR - CPU: {cpu_percent}%, RAM: {memory.percent}%, DISK: {disk.percent}%")
            
            # Alertas se recursos estiverem altos
            if cpu_percent > 80:
                await log_message("warning", f"EC2_MONITOR - CPU alta: {cpu_percent}%")
            if memory.percent > 80:
                await log_message("warning", f"EC2_MONITOR - RAM alta: {memory.percent}%")
            if disk.percent > 80:
                await log_message("warning", f"EC2_MONITOR - DISK alta: {disk.percent}%")
                
        except Exception as e:
            await log_message("error", f"EC2_MONITOR - Erro ao monitorar recursos: {e}")
    
    async def log_network_status(self):
        """Loga status da rede"""
        try:
            # Testar conectividade com APIs externas
            import requests
            
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
            
            await log_message("info", f"EC2_MONITOR - OpenAI: {openai_status}, Supabase: {supabase_status}")
            
        except Exception as e:
            await log_message("error", f"EC2_MONITOR - Erro ao testar rede: {e}")
    
    async def log_performance_metrics(self):
        """Loga métricas de performance"""
        uptime = time.time() - self.start_time
        avg_response_time = 0  # Implementar cálculo de tempo médio
        
        await log_message("info", f"EC2_MONITOR - Uptime: {uptime:.0f}s, Requests: {self.request_count}, Errors: {self.error_count}")
    
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
                await log_message("error", f"EC2_MONITOR - Erro no loop de monitoramento: {e}")
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
    await log_message("info", "EC2_MONITOR - Iniciando monitoramento do EC2")
    asyncio.create_task(ec2_monitor.monitor_loop())

def get_ec2_info():
    """Retorna informações do EC2"""
    try:
        # Verificar se está rodando no EC2
        import requests
        response = requests.get("http://169.254.169.254/latest/meta-data/instance-type", timeout=2)
        instance_type = response.text
        return {
            "is_ec2": True,
            "instance_type": instance_type,
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3)
        }
    except:
        return {
            "is_ec2": False,
            "instance_type": "local",
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3)
        }

if __name__ == "__main__":
    # Teste do monitor
    async def test_monitor():
        await start_ec2_monitoring()
        await asyncio.sleep(60)  # Rodar por 1 minuto
    
    print("Iniciando teste do monitor EC2...")
    asyncio.run(test_monitor()) 