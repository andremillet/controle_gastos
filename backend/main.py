from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://0.0.0.0:8080", "*"],  # Adiciona origens específicas
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

@app.put("/entradas/{id}", response_model=dict)
def update_entrada(id: int, entrada: Entrada):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE entradas SET nome = ?, valor = ?, status = ? WHERE id = ?",
                   (entrada.nome, entrada.valor, entrada.status, id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Entrada não encontrada")
    conn.commit()
    conn.close()
    return {"id": id, **entrada.dict()}

@app.delete("/entradas/{id}")
def delete_entrada(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entradas WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Entrada não encontrada")
    conn.commit()
    conn.close()
    return {"message": "Entrada deletada com sucesso"}

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

@app.put("/saidas/{id}", response_model=dict)
def update_saida(id: int, saida: Saida):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE saidas SET nome = ?, valor = ?, flags = ? WHERE id = ?",
                   (saida.nome, saida.valor, saida.flags, id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Saída não encontrada")
    conn.commit()
    conn.close()
    return {"id": id, **saida.dict()}

@app.delete("/saidas/{id}")
def delete_saida(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saidas WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Saída não encontrada")
    conn.commit()
    conn.close()
    return {"message": "Saída deletada com sucesso"}

# Dashboard
@app.get("/dashboard")
def get_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
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
