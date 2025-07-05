# Diagnóstico: Travamento Apenas no EC2 AWS

## Problema Identificado

O sistema trava apenas na máquina remota EC2 da AWS, mas funciona normalmente na máquina local. Isso indica diferenças de ambiente que podem estar causando o problema.

## Possíveis Causas

### 1. **Recursos Limitados no EC2**
- **CPU**: EC2 pode ter menos cores disponíveis
- **RAM**: Memória insuficiente para processar múltiplas requisições
- **I/O**: Disco mais lento (EBS vs SSD local)

### 2. **Configurações de Rede**
- **Latência**: Conexões mais lentas com APIs externas
- **Timeout**: Configurações de timeout diferentes
- **Rate Limiting**: Limitações de requisições por segundo

### 3. **Diferenças de Ambiente**
- **Python Version**: Versões diferentes do Python
- **Dependencies**: Bibliotecas com versões diferentes
- **System Libraries**: Bibliotecas do sistema diferentes

### 4. **Configurações do CrewAI**
- **Threading**: Comportamento diferente em ambientes com menos recursos
- **Memory Usage**: Uso de memória mais intensivo no EC2
- **Concurrent Requests**: Limitações de concorrência

## Soluções Propostas

### 1. **Otimização de Recursos**

```python
# Adicionar configurações de recursos no main.py
import os
import multiprocessing

# Configurar para usar menos threads se necessário
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Limitar workers do uvicorn
if __name__ == "__main__":
    workers = min(multiprocessing.cpu_count(), 2)  # Máximo 2 workers
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=workers)
```

### 2. **Timeout Mais Conservador**

```python
# Reduzir timeout para EC2
response = await asyncio.wait_for(
    assistent.ask_question_async(mensagem_cliente, conversation_id),
    timeout=15.0  # Reduzir de 30 para 15 segundos
)
```

### 3. **Monitoramento de Recursos**

```python
# Adicionar monitoramento no webhook_chat.py
import psutil
import os

async def log_system_resources():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    await log_message("info", f"CPU: {cpu_percent}%, RAM: {memory.percent}%")
```

### 4. **Configuração de Pool de Conexões**

```python
# Otimizar conexões do banco para EC2
async def get_db_conn():
    return await asyncpg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        statement_cache_size=0,
        command_timeout=10,  # Timeout mais conservador
        server_settings={
            'application_name': 'active-sell-ec2'
        }
    )
```

## Scripts de Diagnóstico

### 1. **Verificar Recursos do EC2**

```bash
# Verificar CPU e RAM
top -n 1
free -h
nproc

# Verificar disco
df -h
iostat -x 1 5

# Verificar rede
ping -c 5 google.com
curl -w "@-" -o /dev/null -s "https://api.openai.com"
```

### 2. **Teste de Performance**

```python
# Adicionar ao teste_webhook_chat.py
async def test_ec2_performance():
    """Teste específico para EC2"""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.virtual_memory().percent
    
    # Fazer requisição
    response = await test_webhook_response()
    
    end_time = time.time()
    end_memory = psutil.virtual_memory().percent
    
    print(f"⏱️ Tempo total: {end_time - start_time:.2f}s")
    print(f"💾 Uso de RAM: {start_memory}% -> {end_memory}%")
    
    return response
```

## Configurações Recomendadas para EC2

### 1. **Uvicorn Config**

```python
# main.py
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        workers=1,  # Usar apenas 1 worker no EC2
        loop="asyncio",
        access_log=True,
        log_level="info"
    )
```

### 2. **CrewAI Config**

```python
# agents/simpleAgent.py
def __init__(self, partner_code):
    # Configurações específicas para EC2
    os.environ["CREWAI_MAX_WORKERS"] = "1"
    os.environ["CREWAI_TIMEOUT"] = "15"
    
    # Resto do código...
```

### 3. **ChromaDB Config**

```python
# Configurações para EC2
self.chroma_client = chromadb.PersistentClient(
    path="db",
    settings=chromadb.config.Settings(
        anonymized_telemetry=False,
        allow_reset=False,  # Desabilitar reset
        is_persistent=True
    )
)
```

## Comandos para EC2

```bash
# Verificar recursos
htop
iotop
netstat -tulpn

# Monitorar logs
tail -f app.log
journalctl -u your-service -f

# Verificar processos
ps aux | grep python
pstree -p $(pgrep python)
```

## Próximos Passos

1. **Implementar monitoramento** para identificar gargalos
2. **Reduzir workers** do uvicorn para 1
3. **Ajustar timeouts** para valores mais conservadores
4. **Monitorar recursos** durante o uso
5. **Implementar fallbacks** mais robustos

## Verificação de Ambiente

```bash
# Comparar versões
python --version
pip list | grep -E "(crewai|chromadb|fastapi|uvicorn)"

# Verificar configurações
ulimit -a
sysctl -a | grep -E "(file-max|max-user-watches)"
``` 