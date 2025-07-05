# Deploy Otimizado para EC2

## Problema Identificado

O processo foi "killed" (OOM - Out of Memory) no EC2, indicando que o servidor está consumindo mais memória do que disponível.

## Soluções Implementadas

### 1. **CrewAI Otimizado**
- CrewAI mantido com otimizações para economizar memória
- Histórico limitado a 500 caracteres
- Busca no ChromaDB limitada a 1 resultado
- Timeout aumentado para 12 segundos para dar tempo ao CrewAI

### 2. **Timeout Otimizado**
- Aumentado para 12 segundos para CrewAI
- Força coleta de lixo após cada processamento

### 3. **Monitor de Memória**
- Monitoramento em tempo real
- Coleta automática de lixo
- Alertas quando memória está alta

### 4. **Configurações de Ambiente**
- Variáveis de ambiente para economia de memória
- Limite de memória virtual (1GB)
- Otimizações do Python

## Como Fazer o Deploy

### 1. **Usar o Script de Deploy**

```bash
# Tornar executável
chmod +x deploy_ec2.sh

# Executar deploy
./deploy_ec2.sh
```

### 2. **Deploy Manual**

```bash
# Parar processo anterior
pkill -f "python3 main.py"

# Limpar cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Configurar ambiente
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
ulimit -v 1048576

# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor
nohup python3 main.py > app.log 2>&1 &
```

### 3. **Verificar Status**

```bash
# Verificar se está rodando
ps aux | grep python3

# Verificar logs
tail -f app.log

# Testar endpoint
curl http://localhost:8000/health
```

## Monitoramento

### 1. **Logs em Tempo Real**

```bash
tail -f app.log
```

### 2. **Monitor de Recursos**

```bash
# Verificar uso de memória
free -h
top -p $(pgrep python3)

# Verificar disco
df -h
```

### 3. **Alertas de Memória**

O sistema agora mostra alertas quando:
- CPU > 80%
- RAM > 80%
- DISK > 80%

## Configurações Otimizadas

### 1. **Variáveis de Ambiente**

```bash
export PYTHONOPTIMIZE=1          # Otimizações do Python
export PYTHONDONTWRITEBYTECODE=1  # Não escreve .pyc
export PYTHONUNBUFFERED=1         # Output não bufferizado
```

### 2. **Limites do Sistema**

```bash
ulimit -v 1048576  # 1GB virtual memory
ulimit -n 1024     # 1024 file descriptors
```

### 3. **Configurações do Uvicorn**

```python
# Apenas 1 worker no EC2
workers = min(multiprocessing.cpu_count(), 1)
```

## Troubleshooting

### 1. **Se o processo for killed novamente**

```bash
# Verificar logs de OOM
dmesg | grep -i "killed process"

# Verificar uso de memória
cat /proc/meminfo
```

### 2. **Se o servidor não responder**

```bash
# Verificar se está rodando
ps aux | grep python3

# Verificar porta
netstat -tulpn | grep 8000

# Reiniciar se necessário
pkill -f "python3 main.py"
./deploy_ec2.sh
```

### 3. **Se houver erros de importação**

```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

## Comandos Úteis

```bash
# Parar servidor
pkill -f "python3 main.py"

# Ver logs
tail -f app.log

# Ver recursos
htop
free -h

# Testar webhook
curl -X POST http://localhost:8000/webhook_chat \
  -H "Content-Type: application/json" \
  -d '{"event":"messages.upsert","data":{"key":{"remoteJid":"5511999999999@s.whatsapp.net","fromMe":false},"pushName":"Teste","messageType":"conversation","message":{"conversation":"Olá"}}}'

# Testar CrewAI especificamente
python3 teste_crewai_ec2.py
```

## Próximos Passos

1. **Monitorar logs** para ver se o OOM foi resolvido
2. **Ajustar limites** se necessário
3. **Implementar cache** para reduzir processamento
4. **Considerar upgrade** do EC2 se problemas persistirem 