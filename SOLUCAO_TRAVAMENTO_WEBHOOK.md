# Solução para Travamento dos Endpoints

## Problema Identificado

Quando uma mensagem é enviada via WhatsApp para o agente responder, todos os endpoints param de funcionar e o sistema trava. Isso acontece porque o método `ask_question` do CrewAI está sendo executado de forma síncrona, bloqueando o event loop do asyncio.

## Causa Raiz

1. **CrewAI Bloqueante**: O método `crew.kickoff()` é síncrono e pode demorar muito para executar
2. **Event Loop Bloqueado**: Como o CrewAI roda na mesma thread do event loop, ele bloqueia todas as outras operações
3. **Timeout Ausente**: Não há timeout para evitar que o processamento demore indefinidamente

## Soluções Implementadas

### 1. Versão Assíncrona do ask_question

```python
async def ask_question_async(self, question, client_id):
    """
    Versão assíncrona do ask_question para evitar bloqueios no event loop
    """
    # Executar a tarefa do CrewAI em um thread separado
    def run_crew_kickoff():
        return self.crew.kickoff(inputs={...})
    
    # Executar em thread separado
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, run_crew_kickoff)
```

### 2. Timeout para Evitar Travamento

```python
# Usar versão assíncrona com timeout
response = await asyncio.wait_for(
    assistent.ask_question_async(mensagem_cliente, conversation_id),
    timeout=30.0  # 30 segundos de timeout
)
```

### 3. Sistema de Retry

```python
max_retries = 2
for attempt in range(max_retries):
    try:
        result = await loop.run_in_executor(executor, run_crew_kickoff)
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise e
        await asyncio.sleep(1)  # Esperar antes de tentar novamente
```

### 4. Resposta de Fallback

```python
except Exception as e:
    # Resposta de fallback em caso de erro
    fallback_response = f"Olá! Sou seu assistente virtual. Como posso ajudá-lo hoje? Sua pergunta foi: {question}"
    return fallback_response
```

## Mudanças nos Arquivos

### 1. `agents/simpleAgent.py`

- ✅ Adicionado método `ask_question_async()` assíncrono
- ✅ Implementado ThreadPoolExecutor para não bloquear o event loop
- ✅ Adicionado sistema de retry
- ✅ Implementado resposta de fallback
- ✅ Melhor tratamento de erros

### 2. `server/webhook_chat.py`

- ✅ Modificado para usar `ask_question_async()` em vez de `ask_question()`
- ✅ Adicionado timeout de 30 segundos
- ✅ Melhor tratamento de erros e timeouts

### 3. `testes/teste_webhook_chat.py` (Novo)

- ✅ Script de teste para verificar se o webhook não trava mais
- ✅ Teste de múltiplas requisições simultâneas
- ✅ Teste de outros endpoints durante o processamento

## Como Testar

### 1. Executar o Script de Teste

```bash
python testes/teste_webhook_chat.py
```

### 2. Teste Manual

1. Inicie o servidor:
   ```bash
   python main.py
   ```

2. Envie uma mensagem via WhatsApp

3. Verifique se outros endpoints ainda funcionam:
   ```bash
   curl http://localhost:8000/health
   ```

### 3. Monitoramento

- ✅ O webhook deve responder em menos de 30 segundos
- ✅ Outros endpoints devem continuar funcionando
- ✅ Não deve haver travamento do sistema

## Benefícios da Solução

1. **Não Bloqueia Event Loop**: O CrewAI roda em thread separada
2. **Timeout Protegido**: Máximo de 30 segundos para resposta
3. **Resposta Garantida**: Sempre retorna uma resposta (mesmo que seja fallback)
4. **Retry Automático**: Tenta novamente em caso de falha
5. **Compatibilidade**: Mantém versão síncrona para outros usos

## Monitoramento

Para verificar se a solução está funcionando:

1. **Logs**: Verifique se não há erros de timeout
2. **Performance**: Tempo de resposta deve ser consistente
3. **Disponibilidade**: Outros endpoints devem continuar funcionando
4. **Estabilidade**: Sistema não deve travar

## Comandos Úteis

```bash
# Testar webhook
python testes/teste_webhook_chat.py

# Verificar logs
tail -f app.log

# Testar health endpoint
curl http://localhost:8000/health

# Monitorar processos
ps aux | grep python
```

## Próximos Passos

Se ainda houver problemas:

1. **Aumentar Timeout**: Se 30 segundos não for suficiente
2. **Otimizar CrewAI**: Verificar se há configurações que podem acelerar o processamento
3. **Cache de Respostas**: Implementar cache para perguntas frequentes
4. **Queue System**: Implementar sistema de fila para processamento assíncrono 