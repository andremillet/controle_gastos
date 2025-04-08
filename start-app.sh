#!/bin/bash

# Função para liberar uma porta se estiver em uso
free_port() {
    PORT=$1
    PID=$(lsof -t -i:$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Liberando porta $PORT (PID: $PID)..."
        kill $PID 2>/dev/null || (sleep 1 && kill -9 $PID 2>/dev/null)
        sleep 1
    fi
}

# Libera as portas 8000 e 8080
free_port 8000
free_port 8080

# Navega para o diretório base
cd ~/petri-dish/controle_gastos || { echo "Diretório base não encontrado!"; exit 1; }

# Inicia o backend primeiro
cd backend || { echo "Diretório backend não encontrado!"; exit 1; }
[ -f ../.venv/bin/activate ] && source ../.venv/bin/activate || { echo "Virtualenv não encontrado!"; exit 1; }
nohup uvicorn main:app --reload > backend.log 2>&1 &

# Aguarda um momento para o backend iniciar
sleep 2

# Inicia o frontend em background
cd ../frontend || { echo "Diretório frontend não encontrado!"; exit 1; }
nohup python3 -m http.server 8080 > frontend.log 2>&1 &

# Abre a página no navegador
sleep 1  # Pequeno atraso para garantir que o frontend esteja ativo
xdg-open "http://127.0.0.1:8080" &
