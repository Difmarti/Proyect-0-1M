"""
Script de Prueba de Estrategia de Criptomonedas
Prueba las señales de crypto SIN ejecutar operaciones reales
"""

import os
import sys
from dotenv import load_dotenv
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Importar estrategia
from crypto_strategy import CryptoStrategy

load_dotenv()

print("=" * 70)
print("PRUEBA DE ESTRATEGIA DE CRIPTOMONEDAS")
print("=" * 70)

# Initialize MT5
print("\n1. Inicializando MT5...")
if not mt5.initialize():
    print(f"   ✗ Error: {mt5.last_error()}")
    sys.exit(1)

print("   ✓ MT5 inicializado")

# Login
print("\n2. Login a la cuenta...")
account = int(os.getenv('MT5_ACCOUNT'))
password = os.getenv('MT5_PASSWORD')
server = os.getenv('MT5_SERVER')

if not mt5.login(account, password, server):
    print(f"   ✗ Error de login: {mt5.last_error()}")
    mt5.shutdown()
    sys.exit(1)

print(f"   ✓ Login exitoso: {account}")

# Get crypto pairs
print("\n3. Obteniendo pares de crypto...")
crypto_pairs = os.getenv('CRYPTO_PAIRS', 'BTCUSD,ETHUSD,LTCUSD,XRPUSD').split(',')
timeframe_minutes = int(os.getenv('CRYPTO_TIMEFRAME', '15'))

# Mapping de timeframes
tf_mapping = {
    5: mt5.TIMEFRAME_M5,
    15: mt5.TIMEFRAME_M15,
    30: mt5.TIMEFRAME_M30,
    60: mt5.TIMEFRAME_H1
}

timeframe = tf_mapping.get(timeframe_minutes, mt5.TIMEFRAME_M15)
print(f"   Timeframe: {timeframe_minutes} minutos")
print(f"   Pares: {', '.join(crypto_pairs)}")

# Initialize strategy
print("\n4. Inicializando estrategia...")
strategy = CryptoStrategy()
print("   ✓ Estrategia cargada")

# Analyze each pair
print("\n5. Analizando señales...")
print("=" * 70)

signals_found = 0

for symbol in crypto_pairs:
    symbol = symbol.strip()

    print(f"\n📊 Analizando {symbol}...")

    # Fetch data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 200)

    if rates is None or len(rates) == 0:
        print(f"   ⚠️  No hay datos disponibles para {symbol}")
        continue

    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # MT5 usa 'tick_volume' para crypto
    if 'volume' not in df.columns and 'tick_volume' in df.columns:
        df['volume'] = df['tick_volume']

    print(f"   ✓ Datos obtenidos: {len(df)} barras")
    print(f"   Último precio: ${df['close'].iloc[-1]:.2f}")
    print(f"   Volumen actual: {df['volume'].iloc[-1]:.0f}")

    # Analyze signal
    signal = strategy.analyze_signal(df, symbol)

    if signal:
        signals_found += 1
        current_price = df['close'].iloc[-1]

        # Calculate SL and TP
        sl, tp = strategy.calculate_sl_tp(current_price, signal)

        print(f"""
╔══════════════════════════════════════════════════════════╗
║  🎯 SEÑAL {signal} DETECTADA EN {symbol}
║
║  Precio actual: ${current_price:.2f}
║  Stop Loss: ${sl:.2f} ({abs((sl - current_price) / current_price * 100):.2f}%)
║  Take Profit: ${tp:.2f} ({abs((tp - current_price) / current_price * 100):.2f}%)
║  Risk/Reward: 1:{abs((tp - current_price) / (current_price - sl)):.2f}
╚══════════════════════════════════════════════════════════╝
        """)
    else:
        print(f"   ℹ️  Sin señal en este momento")

print("\n" + "=" * 70)
print(f"RESUMEN: {signals_found} señal(es) detectada(s)")
print("=" * 70)

# Mostrar condiciones actuales de mercado
print("\n6. Condiciones de mercado:")
print("   Hora actual (UTC):", datetime.utcnow().strftime('%H:%M'))

current_hour = datetime.utcnow().hour
if current_hour in strategy.avoid_hours:
    print(f"   ⚠️  HORA NO ÓPTIMA (evitar trading)")
else:
    for start, end in strategy.optimal_hours:
        if start <= current_hour < end:
            print(f"   ✓ HORA ÓPTIMA para trading")
            break
    else:
        print(f"   ℹ️  Hora aceptable (no óptima)")

# Cleanup
mt5.shutdown()

print("\n" + "=" * 70)
print("PRUEBA COMPLETADA")
print("=" * 70)
print("\nNota: Esta prueba solo analiza señales, NO ejecuta operaciones reales.")
print("Para integrar con el bot, sigue las instrucciones en CRYPTO_INTEGRATION.md")
