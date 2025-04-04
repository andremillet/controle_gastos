from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuração de CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class Entrada(BaseModel):
    nome: str
    valor: float
    status: str = "pendente"

class Saida(BaseModel):
    nome: str
    valor: float
    flags: str = ""

# Funções de banco de dados
def get_db():
    conn = sqlite3.connect("db.sqlite3")
    conn.row_factory = sqlite3.Row
    return conn

# Endpoints de Entradas
@app.get("/entradas", response_model=List[dict])
def get_entradas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entradas")
    entradas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return entradas

@app.post("/entradas", response_model=dict)
def add_entrada(entrada: Entrada):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entradas (nome, valor, status) VALUES (?, ?, ?)",
                   (entrada.nome, entrada.valor, entrada.status))
    conn.commit()
    entrada_id = cursor.lastrowid
    conn.close()
    return {"id": entrada_id, **entrada.dict()}

# Endpoints de Saídas
@app.get("/saidas", response_model=List[dict])
def get_saidas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM saidas")
    saidas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return saidas

@app.post("/saidas", response_model=dict)
def add_saida(saida: Saida):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO saidas (nome, valor, flags) VALUES (?, ?, ?)",
                   (saida.nome, saida.valor, saida.flags))
    conn.commit()
    saida_id = cursor.lastrowid
    conn.close()
    return {"id": saida_id, **saida.dict()}

# Dashboard
@app.get("/dashboard")
def get_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    # Totais
    cursor.execute("SELECT SUM(valor) FROM entradas WHERE status = 'recebido'")
    entradas_recebidas = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(valor) FROM entradas")
    entradas_totais = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(valor) FROM saidas WHERE flags LIKE '%feito%'")
    saidas_pagas = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(valor) FROM saidas")
    saidas_totais = cursor.fetchone()[0] or 0
    
    saldo = entradas_recebidas - saidas_pagas
    pendentes = saidas_totais - saidas_pagas
    
    conn.close()
    return {
        "saldo": saldo,
        "entradas_totais": entradas_totais,
        "entradas_recebidas": entradas_recebidas,
        "saidas_totais": saidas_totais,
        "saidas_pagas": saidas_pagas,
        "pendentes": pendentes
    }
