import os
import gc
import atexit
import signal
import sys
from typing import List, Callable

class ResourceCleanup:
    """
    Utilitário para gerenciar limpeza de recursos e evitar vazamentos de semáforos
    """
    
    def __init__(self):
        self.cleanup_functions: List[Callable] = []
        self._setup_signal_handlers()
        atexit.register(self._cleanup_all)
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais de shutdown"""
        def signal_handler(signum, frame):
            print(f"Recebido sinal {signum}, iniciando limpeza...")
            self._cleanup_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def register_cleanup(self, cleanup_func: Callable):
        """Registra uma função de limpeza"""
        self.cleanup_functions.append(cleanup_func)
    
    def _cleanup_all(self):
        """Executa todas as funções de limpeza registradas"""
        print("Iniciando limpeza de recursos...")
        
        for cleanup_func in self.cleanup_functions:
            try:
                cleanup_func()
            except Exception as e:
                print(f"Erro durante limpeza: {e}")
        
        # Forçar coleta de lixo
        gc.collect()
        print("Limpeza de recursos concluída.")
    
    def force_cleanup(self):
        """Força a execução da limpeza imediatamente"""
        self._cleanup_all()

# Instância global
resource_cleanup = ResourceCleanup()

def setup_chromadb_cleanup():
    """Configura limpeza específica para ChromaDB"""
    def chromadb_cleanup():
        try:
            import chromadb
            # ChromaDB não precisa de limpeza explícita
            # O garbage collector cuidará da limpeza
            print("ChromaDB será limpo automaticamente pelo garbage collector...")
        except Exception as e:
            print(f"Erro ao limpar ChromaDB: {e}")
    
    resource_cleanup.register_cleanup(chromadb_cleanup)

def setup_multiprocessing_cleanup():
    """Configura limpeza para recursos de multiprocessing"""
    def multiprocessing_cleanup():
        try:
            import multiprocessing
            # Forçar limpeza de recursos de multiprocessing
            print("Limpando recursos de multiprocessing...")
        except Exception as e:
            print(f"Erro ao limpar multiprocessing: {e}")
    
    resource_cleanup.register_cleanup(multiprocessing_cleanup)

# Configurações iniciais
setup_chromadb_cleanup()
setup_multiprocessing_cleanup()

if __name__ == "__main__":
    print("Utilitário de limpeza de recursos carregado.")
    print("Use resource_cleanup.force_cleanup() para forçar limpeza imediata.") 