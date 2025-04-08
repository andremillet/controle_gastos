import sqlite3
from datetime import datetime

def migrate_db():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    
    # Get current date in YYYY-MM-DD format
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Check if the new columns exist in the saidas table
    cursor.execute("PRAGMA table_info(saidas)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add new columns if they don't exist
    if "parcela_atual" not in columns:
        cursor.execute("ALTER TABLE saidas ADD COLUMN parcela_atual INTEGER DEFAULT 1")
    
    if "total_parcelas" not in columns:
        cursor.execute("ALTER TABLE saidas ADD COLUMN total_parcelas INTEGER DEFAULT 1")
    
    if "id_grupo_parcela" not in columns:
        cursor.execute("ALTER TABLE saidas ADD COLUMN id_grupo_parcela INTEGER DEFAULT NULL")
    
    if "data_vencimento" not in columns:
        cursor.execute(f"ALTER TABLE saidas ADD COLUMN data_vencimento TEXT DEFAULT '{current_date}'")
        # Update all rows to have the current date
        cursor.execute(f"UPDATE saidas SET data_vencimento = '{current_date}' WHERE data_vencimento IS NULL")
    
    # Check if data column exists in entradas
    cursor.execute("PRAGMA table_info(entradas)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "data" not in columns:
        cursor.execute(f"ALTER TABLE entradas ADD COLUMN data TEXT DEFAULT '{current_date}'")
        # Update all rows to have the current date
        cursor.execute(f"UPDATE entradas SET data = '{current_date}' WHERE data IS NULL")
    
    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_db()
