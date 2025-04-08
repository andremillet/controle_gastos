import sqlite3
from datetime import datetime, timedelta
import re

def init_db():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    
    # Tabela de Entradas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            status TEXT DEFAULT 'pendente',
            data TEXT DEFAULT (strftime('%Y-%m-%d', 'now'))
        )
    """)
    
    # Tabela de Saídas (atualizada com novos campos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            flags TEXT DEFAULT '',
            data TEXT DEFAULT (strftime('%Y-%m-%d', 'now')),
            parcela_atual INTEGER DEFAULT 1,
            total_parcelas INTEGER DEFAULT 1,
            id_grupo_parcela INTEGER DEFAULT NULL,
            data_vencimento TEXT DEFAULT (strftime('%Y-%m-%d', 'now'))
        )
    """)
    
    conn.commit()
    conn.close()

def populate_initial_data():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    
    # Dados iniciais de entradas
    entradas = [
        ("vasco_barcelos", 9000, "recebido"),
        ("hercruz", 5000, "pendente"),
        ("policlinica_mesquita", 6000, "pendente"),
        ("lirio_dos_vales", 1600, "pendente")
    ]
    
    # Dados iniciais de saídas
    saidas = [
        ("cartao inter andre", 2922, "feito"),
        ("analise kamylla", 360, ""),
        ("grupo de estudos kamylla", 800, "feito"),
        ("posgraduacao kamylla", 500, "urg,feito"),
        ("cartao santander kamylla", 2300, "feito"),
        ("conta corrente santander kamylla", 500, "no_rec,feito"),
        ("plano de saude amil", 1364, "urg,feito"),
        ("internet", 0, ""),
        ("luz", 800, ""),
        ("agua", 150, ""),
        ("aluguel", 2200, ""),
        ("gatos", 0, ""),
        ("mei andre", 80, ""),
        ("rozi", 600, ""),
        ("celular", 350, ""),
        ("remedio", 200, ""),
        ("mercado", 1500, "")
    ]
    
    cursor.executemany("INSERT OR IGNORE INTO entradas (nome, valor, status) VALUES (?, ?, ?)", entradas)
    cursor.executemany("INSERT OR IGNORE INTO saidas (nome, valor, flags) VALUES (?, ?, ?)", saidas)
    
    conn.commit()
    conn.close()

def create_parcelas(nome, valor_total, flags, data_inicial=None):
    """
    Cria parcelas automaticamente baseado na flag 'parcX' onde X é o número de parcelas
    """
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    
    # Detectar o padrão de parcelamento nas flags (parc2, parc3, parc10, etc)
    parcelas_match = re.search(r'parc(\d+)', flags)
    if not parcelas_match:
        # Se não houver parcelamento, apenas inserir normalmente
        cursor.execute(
            "INSERT INTO saidas (nome, valor, flags, data_vencimento) VALUES (?, ?, ?, ?)",
            (nome, valor_total, flags, data_inicial or datetime.now().strftime('%Y-%m-%d'))
        )
        conn.commit()
        conn.close()
        return
    
    total_parcelas = int(parcelas_match.group(1))
    valor_parcela = round(valor_total / total_parcelas, 2)
    
    # Criar um ID de grupo para vincular todas as parcelas
    cursor.execute("INSERT INTO saidas (nome, valor, flags) VALUES ('temp', 0, '')")
    id_grupo = cursor.lastrowid
    cursor.execute("DELETE FROM saidas WHERE id = ?", (id_grupo,))
    
    # Data inicial para primeira parcela (hoje se não for especificada)
    if not data_inicial:
        data_inicial = datetime.now().strftime('%Y-%m-%d')
    
    data_atual = datetime.strptime(data_inicial, '%Y-%m-%d')
    
    # Criar todas as parcelas
    for i in range(1, total_parcelas + 1):
        data_vencimento = data_atual.strftime('%Y-%m-%d')
        nome_parcela = f"{nome} ({i}/{total_parcelas})"
        
        cursor.execute("""
            INSERT INTO saidas 
            (nome, valor, flags, parcela_atual, total_parcelas, id_grupo_parcela, data_vencimento) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome_parcela, valor_parcela, flags, i, total_parcelas, id_grupo, data_vencimento))
        
        # Avançar um mês para a próxima parcela
        if data_atual.month == 12:
            data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
        else:
            data_atual = data_atual.replace(month=data_atual.month + 1)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    populate_initial_data()
