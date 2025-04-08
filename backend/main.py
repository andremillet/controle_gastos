from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
import re
from datetime import datetime, timedelta

app = FastAPI()

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://0.0.0.0:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic atualizados
class Entrada(BaseModel):
    nome: str
    valor: float
    status: str = "pendente"
    data: Optional[str] = None

class Saida(BaseModel):
    nome: str
    valor: float
    flags: str = ""
    data_vencimento: Optional[str] = None
    parcelamento: Optional[int] = None  # Número de parcelas (2, 3, 5, 6, 10, etc.)

# Funções de banco de dados
def get_db():
    conn = sqlite3.connect("db.sqlite3")
    conn.row_factory = sqlite3.Row
    return conn

# Função para obter o início e fim do mês atual
def get_current_month_range():
    today = datetime.now()
    first_day = today.replace(day=1).strftime('%Y-%m-%d')
    
    # Calcular o último dia do mês
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    last_day = last_day.strftime('%Y-%m-%d')
    return first_day, last_day

# Função para obter o início e fim de um mês específico
def get_month_range(year, month):
    first_day = datetime(year, month, 1).strftime('%Y-%m-%d')
    
    # Calcular o último dia do mês
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    last_day = last_day.strftime('%Y-%m-%d')
    return first_day, last_day

# Função para criar parcelas
def create_parcelas(nome, valor_total, flags, parcelas, data_inicial=None):
    """
    Cria parcelas automaticamente baseado no número de parcelas
    """
    conn = get_db()
    cursor = conn.cursor()
    
    if not parcelas or parcelas <= 1:
        # Se não houver parcelamento, apenas inserir normalmente
        cursor.execute(
            "INSERT INTO saidas (nome, valor, flags, data_vencimento) VALUES (?, ?, ?, ?)",
            (nome, valor_total, flags, data_inicial or datetime.now().strftime('%Y-%m-%d'))
        )
        saida_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return saida_id
    
    # Adicionar a flag de parcelamento
    if not "parc" in flags:
        if flags:
            flags += f",parc{parcelas}"
        else:
            flags = f"parc{parcelas}"
    
    valor_parcela = round(valor_total / parcelas, 2)
    
    # Criar um ID de grupo para vincular todas as parcelas
    cursor.execute("INSERT INTO saidas (nome, valor, flags) VALUES ('temp', 0, '')")
    id_grupo = cursor.lastrowid
    cursor.execute("DELETE FROM saidas WHERE id = ?", (id_grupo,))
    
    # Data inicial para primeira parcela (hoje se não for especificada)
    if not data_inicial:
        data_inicial = datetime.now().strftime('%Y-%m-%d')
    
    data_atual = datetime.strptime(data_inicial, '%Y-%m-%d')
    first_id = None
    
    # Criar todas as parcelas
    for i in range(1, parcelas + 1):
        data_vencimento = data_atual.strftime('%Y-%m-%d')
        nome_parcela = f"{nome} ({i}/{parcelas})"
        
        cursor.execute("""
            INSERT INTO saidas 
            (nome, valor, flags, parcela_atual, total_parcelas, id_grupo_parcela, data_vencimento) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome_parcela, valor_parcela, flags, i, parcelas, id_grupo, data_vencimento))
        
        if i == 1:
            first_id = cursor.lastrowid
        
        # Avançar um mês para a próxima parcela
        if data_atual.month == 12:
            data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
        else:
            data_atual = data_atual.replace(month=data_atual.month + 1)
    
    conn.commit()
    conn.close()
    return first_id

# Endpoints de Entradas
@app.get("/entradas", response_model=List[dict])
def get_entradas(
    ano: Optional[int] = Query(None, description="Ano para filtrar (ex: 2025)"),
    mes: Optional[int] = Query(None, description="Mês para filtrar (1-12)")
):
    conn = get_db()
    cursor = conn.cursor()
    
    # Se ano e mês forem fornecidos, use-os para filtrar
    if ano and mes:
        first_day, last_day = get_month_range(ano, mes)
        cursor.execute(
            "SELECT * FROM entradas WHERE data BETWEEN ? AND ? ORDER BY data",
            (first_day, last_day)
        )
    else:
        # Caso contrário, use o mês atual
        first_day, last_day = get_current_month_range()
        cursor.execute(
            "SELECT * FROM entradas WHERE data BETWEEN ? AND ? ORDER BY data",
            (first_day, last_day)
        )
    
    entradas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return entradas

@app.get("/entradas/todos", response_model=List[dict])
def get_todas_entradas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entradas ORDER BY data DESC")
    entradas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return entradas

@app.post("/entradas", response_model=dict)
def add_entrada(entrada: Entrada):
    conn = get_db()
    cursor = conn.cursor()
    data = entrada.data or datetime.now().strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO entradas (nome, valor, status, data) VALUES (?, ?, ?, ?)",
                   (entrada.nome, entrada.valor, entrada.status, data))
    conn.commit()
    entrada_id = cursor.lastrowid
    conn.close()
    return {"id": entrada_id, **entrada.dict()}

@app.put("/entradas/{id}", response_model=dict)
def update_entrada(id: int, entrada: Entrada):
    conn = get_db()
    cursor = conn.cursor()
    data = entrada.data or datetime.now().strftime('%Y-%m-%d')
    cursor.execute("UPDATE entradas SET nome = ?, valor = ?, status = ?, data = ? WHERE id = ?",
                   (entrada.nome, entrada.valor, entrada.status, data, id))
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
def get_saidas(
    ano: Optional[int] = Query(None, description="Ano para filtrar (ex: 2025)"),
    mes: Optional[int] = Query(None, description="Mês para filtrar (1-12)")
):
    conn = get_db()
    cursor = conn.cursor()
    
    # Se ano e mês forem fornecidos, use-os para filtrar
    if ano and mes:
        first_day, last_day = get_month_range(ano, mes)
        cursor.execute("""
            SELECT id, nome, valor, flags, data, parcela_atual, 
                   total_parcelas, id_grupo_parcela, data_vencimento
            FROM saidas
            WHERE data_vencimento BETWEEN ? AND ?
            ORDER BY data_vencimento ASC
        """, (first_day, last_day))
    else:
        # Caso contrário, use o mês atual
        first_day, last_day = get_current_month_range()
        cursor.execute("""
            SELECT id, nome, valor, flags, data, parcela_atual, 
                   total_parcelas, id_grupo_parcela, data_vencimento
            FROM saidas
            WHERE data_vencimento BETWEEN ? AND ?
            ORDER BY data_vencimento ASC
        """, (first_day, last_day))
    
    saidas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return saidas

@app.get("/saidas/todos", response_model=List[dict])
def get_todas_saidas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, valor, flags, data, parcela_atual, 
               total_parcelas, id_grupo_parcela, data_vencimento
        FROM saidas
        ORDER BY data_vencimento ASC
    """)
    saidas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return saidas

@app.post("/saidas", response_model=dict)
def add_saida(saida: Saida):
    # Se tiver parcelamento, usa a função específica
    if saida.parcelamento and saida.parcelamento > 1:
        saida_id = create_parcelas(
            saida.nome, 
            saida.valor, 
            saida.flags, 
            saida.parcelamento, 
            saida.data_vencimento
        )
        return {"id": saida_id, **saida.dict()}
    
    # Caso contrário, insere normalmente
    conn = get_db()
    cursor = conn.cursor()
    data_vencimento = saida.data_vencimento or datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO saidas (nome, valor, flags, data_vencimento) 
        VALUES (?, ?, ?, ?)
    """, (saida.nome, saida.valor, saida.flags, data_vencimento))
    conn.commit()
    saida_id = cursor.lastrowid
    conn.close()
    return {"id": saida_id, **saida.dict()}

@app.put("/saidas/{id}", response_model=dict)
def update_saida(id: int, saida: Saida):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar se faz parte de um grupo de parcelas
    cursor.execute("SELECT id_grupo_parcela, total_parcelas FROM saidas WHERE id = ?", (id,))
    result = cursor.fetchone()
    
    if result and result['id_grupo_parcela'] and result['total_parcelas'] > 1:
        # Se for uma parcela, perguntar se deseja atualizar todas as parcelas do grupo
        grupo_id = result['id_grupo_parcela']
        
        # Atualizar apenas a parcela específica
        data_vencimento = saida.data_vencimento or datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE saidas 
            SET nome = ?, valor = ?, flags = ?, data_vencimento = ? 
            WHERE id = ?
        """, (saida.nome, saida.valor, saida.flags, data_vencimento, id))
    else:
        # Atualização normal
        data_vencimento = saida.data_vencimento or datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE saidas 
            SET nome = ?, valor = ?, flags = ?, data_vencimento = ? 
            WHERE id = ?
        """, (saida.nome, saida.valor, saida.flags, data_vencimento, id))
    
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
    
    # Verificar se faz parte de um grupo de parcelas
    cursor.execute("SELECT id_grupo_parcela FROM saidas WHERE id = ?", (id,))
    result = cursor.fetchone()
    
    if result and result['id_grupo_parcela']:
        # Se for uma parcela, deletar apenas esta parcela específica
        cursor.execute("DELETE FROM saidas WHERE id = ?", (id,))
    else:
        # Deleção normal
        cursor.execute("DELETE FROM saidas WHERE id = ?", (id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Saída não encontrada")
    
    conn.commit()
    conn.close()
    return {"message": "Saída deletada com sucesso"}

# Endpoint para deletar todas as parcelas de um grupo
@app.delete("/saidas/grupo/{grupo_id}")
def delete_grupo_parcelas(grupo_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saidas WHERE id_grupo_parcela = ?", (grupo_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Grupo de parcelas não encontrado")
    
    return {"message": f"Grupo de parcelas deletado com sucesso. {deleted_count} parcelas removidas."}

# Endpoint para obter meses disponíveis para filtro
@app.get("/meses-disponiveis")
def get_meses_disponiveis():
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar meses únicos de entradas
    cursor.execute("""
        SELECT DISTINCT strftime('%Y', data) as ano, strftime('%m', data) as mes
        FROM entradas
        ORDER BY ano DESC, mes DESC
    """)
    meses_entradas = [{"ano": int(row[0]), "mes": int(row[1])} for row in cursor.fetchall()]
    
    # Buscar meses únicos de saídas
    cursor.execute("""
        SELECT DISTINCT strftime('%Y', data_vencimento) as ano, strftime('%m', data_vencimento) as mes
        FROM saidas
        ORDER BY ano DESC, mes DESC
    """)
    meses_saidas = [{"ano": int(row[0]), "mes": int(row[1])} for row in cursor.fetchall()]
    
    # Combinar e remover duplicados
    todos_meses = meses_entradas + meses_saidas
    meses_unicos = []
    for mes in todos_meses:
        if mes not in meses_unicos:
            meses_unicos.append(mes)
    
    # Ordenar por ano e mês (decrescente)
    meses_unicos.sort(key=lambda x: (x["ano"], x["mes"]), reverse=True)
    
    conn.close()
    return meses_unicos

# Dashboard
@app.get("/dashboard")
def get_dashboard(
    ano: Optional[int] = Query(None, description="Ano para filtrar (ex: 2025)"),
    mes: Optional[int] = Query(None, description="Mês para filtrar (1-12)")
):
    conn = get_db()
    cursor = conn.cursor()
    
    # Definir o período a ser analisado
    if ano and mes:
        first_day, last_day = get_month_range(ano, mes)
    else:
        first_day, last_day = get_current_month_range()
    
    # Entradas do mês selecionado
    cursor.execute("""
        SELECT SUM(valor) FROM entradas 
        WHERE status = 'recebido' AND data BETWEEN ? AND ?
    """, (first_day, last_day))
    entradas_recebidas = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT SUM(valor) FROM entradas 
        WHERE data BETWEEN ? AND ?
    """, (first_day, last_day))
    entradas_totais = cursor.fetchone()[0] or 0
    
    # Saídas do mês selecionado
    cursor.execute("""
        SELECT SUM(valor) FROM saidas 
        WHERE flags LIKE '%feito%' AND data_vencimento BETWEEN ? AND ?
    """, (first_day, last_day))
    saidas_pagas = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT SUM(valor) FROM saidas 
        WHERE data_vencimento BETWEEN ? AND ?
    """, (first_day, last_day))
    saidas_totais = cursor.fetchone()[0] or 0
    
    # Dados de parcelas
    cursor.execute("""
        SELECT COUNT(*) FROM saidas 
        WHERE total_parcelas > 1 AND data_vencimento BETWEEN ? AND ?
    """, (first_day, last_day))
    total_itens_parcelados = cursor.fetchone()[0] or 0
    
    # Valor das próximas parcelas (vencimento nos próximos 30 dias)
    hoje = datetime.now().strftime('%Y-%m-%d')
    proximo_mes = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT SUM(valor) FROM saidas 
        WHERE data_vencimento BETWEEN ? AND ?
        AND flags NOT LIKE '%feito%'
    """, (hoje, proximo_mes))
    proximas_parcelas = cursor.fetchone()[0] or 0
    
    saldo = entradas_recebidas - saidas_pagas
    pendentes = saidas_totais - saidas_pagas
    
    # Obter o nome do mês para exibição
    mes_nome = datetime(ano or datetime.now().year, mes or datetime.now().month, 1).strftime('%B %Y')
    
    conn.close()
    return {
        "mes_referencia": mes_nome,
        "saldo": saldo,
        "entradas_totais": entradas_totais,
        "entradas_recebidas": entradas_recebidas,
        "saidas_totais": saidas_totais,
        "saidas_pagas": saidas_pagas,
        "pendentes": pendentes,
        "total_itens_parcelados": total_itens_parcelados,
        "proximas_parcelas": proximas_parcelas
    }
