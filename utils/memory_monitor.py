#!/usr/bin/env python3
"""
Monitor de memória para evitar OOM no EC2
"""

import os
import psutil
import signal
import sys
import time
from datetime import datetime

class MemoryMonitor:
    def __init__(self, max_memory_percent=85):
        self.max_memory_percent = max_memory_percent
        self.process_id = os.getpid()
    
    def check_memory(self):
        """Verifica uso de memória e retorna True se estiver alto"""
        try:
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_percent:
                print(f"⚠️ ALERTA: Uso de memória alto: {memory.percent}%")
                return True
            return False
        except Exception as e:
            print(f"Erro ao verificar memória: {e}")
            return False
    
    def force_garbage_collection(self):
        """Força coleta de lixo"""
        try:
            import gc
            collected = gc.collect()
            print(f"🗑️ Coleta de lixo: {collected} objetos coletados")
        except Exception as e:
            print(f"Erro na coleta de lixo: {e}")
    
    def restart_if_needed(self):
        """Reinicia o processo se a memória estiver muito alta"""
        if self.check_memory():
            print("🚨 Memória crítica detectada! Reiniciando processo...")
            # Enviar sinal para reiniciar
            os.kill(self.process_id, signal.SIGTERM)
            time.sleep(2)
            os.kill(self.process_id, signal.SIGKILL)

def setup_memory_monitoring():
    """Configura monitoramento de memória"""
    monitor = MemoryMonitor()
    
    def memory_check():
        while True:
            try:
                if monitor.check_memory():
                    monitor.force_garbage_collection()
                    # Se ainda estiver alto após coleta, considerar reiniciar
                    if monitor.check_memory():
                        print("🚨 Memória ainda alta após coleta de lixo!")
                time.sleep(30)  # Verificar a cada 30 segundos
            except Exception as e:
                print(f"Erro no monitor de memória: {e}")
                time.sleep(30)
    
    import threading
    memory_thread = threading.Thread(target=memory_check, daemon=True)
    memory_thread.start()
    
    return monitor

# Instância global
memory_monitor = setup_memory_monitoring()

if __name__ == "__main__":
    print("Iniciando monitor de memória...")
    while True:
        time.sleep(10)
        memory_monitor.check_memory() 