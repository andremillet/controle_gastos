import sqlite3
from datetime import datetime

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
    
    # Tabela de Saídas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            flags TEXT DEFAULT '',
            data TEXT DEFAULT (strftime('%Y-%m-%d', 'now'))
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

if __name__ == "__main__":
    init_db()
    populate_initial_data()
