"""
Script de prueba para verificar todas las conexiones del Windows MT5 Bridge
"""
import os
from dotenv import load_dotenv
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Cargar variables de entorno
load_dotenv()

print("=" * 60)
print("PRUEBA DE CONEXIONES - Windows MT5 Bridge")
print("=" * 60)

# 1. Probar conexión a PostgreSQL
print("\n1. Probando conexión a PostgreSQL...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', 5432),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    db_version = cursor.fetchone()
    print(f"   ✓ PostgreSQL conectado exitosamente!")
    print(f"   Versión: {db_version[0][:50]}...")

    # Verificar tablas
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f"   Tablas encontradas: {len(tables)}")
    for table in tables:
        print(f"     - {table[0]}")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ✗ Error conectando a PostgreSQL: {e}")
    sys.exit(1)

# 2. Probar conexión a Redis
print("\n2. Probando conexión a Redis...")
try:
    import redis
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True
    )
    redis_client.ping()
    print(f"   ✓ Redis conectado exitosamente!")

    # Info de Redis
    info = redis_client.info('server')
    print(f"   Versión: {info.get('redis_version', 'N/A')}")
except Exception as e:
    print(f"   ✗ Error conectando a Redis: {e}")
    sys.exit(1)

# 3. Probar conexión a MT5
print("\n3. Probando conexión a MetaTrader 5...")
try:
    import MetaTrader5 as mt5

    # Inicializar MT5
    if not mt5.initialize():
        print(f"   ✗ Error inicializando MT5: {mt5.last_error()}")
        sys.exit(1)

    print(f"   ✓ MT5 inicializado exitosamente!")

    # Información de la terminal
    terminal_info = mt5.terminal_info()
    if terminal_info:
        print(f"   Terminal: {terminal_info.name}")
        print(f"   Ruta: {terminal_info.path}")
        print(f"   Build: {terminal_info.build}")

    # Intentar login
    account = int(os.getenv('MT5_ACCOUNT'))
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')

    print(f"\n   Intentando login...")
    print(f"   Cuenta: {account}")
    print(f"   Servidor: {server}")

    authorized = mt5.login(account, password, server)

    if not authorized:
        error = mt5.last_error()
        print(f"   ✗ Error en login: {error}")
        print(f"   Código: {error[0]}, Descripción: {error[1]}")
        mt5.shutdown()
        sys.exit(1)

    print(f"   ✓ Login exitoso!")

    # Información de la cuenta
    account_info = mt5.account_info()
    if account_info:
        print(f"\n   Información de la cuenta:")
        print(f"     - Balance: ${account_info.balance:.2f}")
        print(f"     - Equity: ${account_info.equity:.2f}")
        print(f"     - Margin: ${account_info.margin:.2f}")
        print(f"     - Profit: ${account_info.profit:.2f}")

    # Verificar símbolos
    symbols = mt5.symbols_get()
    if symbols:
        print(f"   Símbolos disponibles: {len(symbols)}")

        # Verificar pares configurados
        trading_pairs = os.getenv('TRADING_PAIRS', '').split(',')
        print(f"\n   Verificando pares configurados:")
        for pair in trading_pairs:
            symbol_info = mt5.symbol_info(pair.strip())
            if symbol_info:
                print(f"     ✓ {pair}: Disponible")
            else:
                print(f"     ✗ {pair}: NO disponible")

    mt5.shutdown()

except Exception as e:
    print(f"   ✗ Error con MT5: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE!")
print("=" * 60)
print("\nEl bridge está listo para ejecutarse.")
print("Ejecuta: python mt5_bridge.py")
