#!/bin/bash

# Script de deploy otimizado para EC2
echo "🚀 Iniciando deploy otimizado para EC2..."

# Parar processo anterior se existir
echo "🛑 Parando processo anterior..."
pkill -f "python3 main.py" || true
sleep 2

# Limpar cache do Python
echo "🧹 Limpando cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Verificar memória disponível
echo "📊 Verificando recursos..."
free -h
df -h

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Configurar variáveis de ambiente para economia de memória
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Configurar limites de memória
ulimit -v 1048576  # 1GB virtual memory limit

# Iniciar servidor com monitoramento
echo "🚀 Iniciando servidor otimizado..."
nohup python3 main.py > app.log 2>&1 &

# Aguardar inicialização
sleep 5

# Verificar se está rodando
if pgrep -f "python3 main.py" > /dev/null; then
    echo "✅ Servidor iniciado com sucesso!"
    echo "📊 PID: $(pgrep -f 'python3 main.py')"
    echo "📄 Logs: tail -f app.log"
else
    echo "❌ Falha ao iniciar servidor"
    exit 1
fi

# Monitorar por alguns segundos
echo "👀 Monitorando inicialização..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Servidor respondendo corretamente!"
        break
    fi
    echo "⏳ Aguardando... ($i/10)"
    sleep 2
done

echo "🎉 Deploy concluído!"
echo "📊 Para monitorar: tail -f app.log"
echo "🛑 Para parar: pkill -f 'python3 main.py'" 