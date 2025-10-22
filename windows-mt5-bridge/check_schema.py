"""
Verificar el esquema de la base de datos
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Conectar a PostgreSQL
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', 5432),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cursor = conn.cursor()

# Obtener columnas de cada tabla
tables = ['price_data', 'account_metrics', 'active_trades', 'trade_history']

for table in tables:
    print(f"\n{'='*60}")
    print(f"Tabla: {table}")
    print(f"{'='*60}")

    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table}'
        ORDER BY ordinal_position;
    """)

    columns = cursor.fetchall()

    if columns:
        print(f"{'Columna':<30} {'Tipo':<20} {'Nullable'}")
        print(f"{'-'*30} {'-'*20} {'-'*8}")
        for col in columns:
            print(f"{col[0]:<30} {col[1]:<20} {col[2]}")
    else:
        print(f"  Tabla no encontrada o sin columnas")

cursor.close()
conn.close()

print(f"\n{'='*60}")
