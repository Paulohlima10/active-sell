# Solução para Vazamento de Semáforos

## Problema Identificado

O aviso `resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown` indica que há recursos de multiprocessing (semáforos) que não estão sendo liberados adequadamente quando o programa é encerrado.

## Causas Principais

1. **ChromaDB**: O ChromaDB usa multiprocessing internamente e pode não liberar recursos adequadamente
2. **CrewAI**: A biblioteca CrewAI pode criar processos internos que não são limpos
3. **Tarefas assíncronas**: `asyncio.create_task()` sem await pode deixar tarefas pendentes

## Soluções Implementadas

### 1. Desabilitação da Telemetria do ChromaDB

```python
# Adicionado em main.py e agents/simpleAgent.py
os.environ["CHROMA_TELEMETRY"] = "false"
```

### 2. Método de Limpeza no SalesAssistant

```python
def cleanup(self):
    """
    Método para limpar recursos e evitar vazamentos de semáforos
    """
    try:
        if hasattr(self, 'chroma_client'):
            # Tentar limpar recursos do ChromaDB
            if hasattr(self.chroma_client, 'reset'):
                self.chroma_client.reset()
    except Exception as e:
        print(f"Erro durante limpeza do SalesAssistant: {e}")
```

### 3. Registro de Função de Limpeza

```python
# No construtor do SalesAssistant
atexit.register(self.cleanup)
```

### 4. Utilitário de Limpeza de Recursos

Criado `utils/resource_cleanup.py` para gerenciar limpeza centralizada.

### 5. Shutdown Handler no FastAPI

```python
async def cleanup_resources():
    await log_message("info", "Limpando recursos...")
    if resource_cleanup:
        resource_cleanup.force_cleanup()

app = FastAPI(
    on_startup=[start_log_processor, initialize_log],
    on_shutdown=[cleanup_resources]
)
```

## Como Testar

### 1. Executar o Script de Teste

```bash
python testes/teste_cleanup.py
```

### 2. Verificar se o Aviso Persiste

Após as mudanças, execute o servidor e verifique se o aviso ainda aparece:

```bash
python main.py
```

### 3. Monitorar Recursos

Use o script de teste para verificar se há vazamentos:

```bash
python testes/teste_cleanup.py
```

## Prevenção Futura

### 1. Sempre Aguardar Tarefas Assíncronas

```python
# ❌ Errado
asyncio.create_task(some_function())

# ✅ Correto
await some_function()
# ou
task = asyncio.create_task(some_function())
await task
```

### 2. Usar Context Managers

```python
# Para recursos que precisam ser fechados
with open(file_path) as f:
    content = f.read()
```

### 3. Limpeza Explícita

```python
# Sempre limpar recursos quando possível
def __del__(self):
    self.cleanup()
```

## Arquivos Modificados

1. `agents/simpleAgent.py` - Adicionado método de limpeza
2. `main.py` - Configuração de telemetria e shutdown handler
3. `utils/resource_cleanup.py` - Utilitário de limpeza (novo)
4. `testes/teste_cleanup.py` - Script de teste (novo)

## Monitoramento

Para monitorar se o problema foi resolvido:

1. Execute o servidor normalmente
2. Envie algumas mensagens de teste
3. Encerre o servidor com Ctrl+C
4. Verifique se o aviso de vazamento ainda aparece

Se o aviso persistir, pode ser necessário investigar outras bibliotecas ou implementar limpeza adicional.

## Comandos Úteis

```bash
# Testar limpeza de recursos
python testes/teste_cleanup.py

# Executar servidor com debug
python main.py

# Verificar processos Python
ps aux | grep python

# Verificar uso de memória
top -p $(pgrep python)
``` 