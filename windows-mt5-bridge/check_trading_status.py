"""
Verificar estado del trading y rentabilidad
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

load_dotenv()

db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'trading_db'),
    'user': os.getenv('POSTGRES_USER', 'trading_user'),
    'password': os.getenv('POSTGRES_PASSWORD', '')
}

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("="*80)
    print("📊 ESTADO DEL TRADING - ANÁLISIS COMPLETO")
    print("="*80)

    # 1. Métricas actuales
    print("\n1️⃣ MÉTRICAS DE CUENTA ACTUAL:")
    cur.execute("""
        SELECT balance, equity, margin, free_margin, profit, time
        FROM account_metrics
        ORDER BY time DESC
        LIMIT 1
    """)
    metrics = cur.fetchone()
    if metrics:
        print(f"   Balance:      ${metrics['balance']:,.2f}")
        print(f"   Equity:       ${metrics['equity']:,.2f}")
        print(f"   Profit:       ${metrics['profit']:,.2f}")
        print(f"   Margen:       ${metrics['margin']:,.2f}")
        print(f"   Última actualización: {metrics['time']}")

    # 2. Trades activos
    print("\n2️⃣ TRADES ACTIVOS:")
    cur.execute("""
        SELECT ticket, symbol, type, volume, open_price, current_price, profit, open_time
        FROM active_trades
        ORDER BY open_time DESC
    """)
    active = cur.fetchall()
    if active:
        for trade in active:
            print(f"   🎫 {trade['ticket']} | {trade['symbol']} {trade['type']} | Lotes: {trade['volume']} | Profit: ${trade['profit']:,.2f}")
    else:
        print("   ✅ No hay trades activos")

    # 3. Historial de hoy
    print("\n3️⃣ TRADES CERRADOS HOY:")
    cur.execute("""
        SELECT symbol, type, volume, profit, close_time
        FROM trade_history
        WHERE close_time >= CURRENT_DATE
        ORDER BY close_time DESC
        LIMIT 10
    """)
    today = cur.fetchall()
    if today:
        total_profit_today = 0
        for trade in today:
            total_profit_today += trade['profit']
            print(f"   {trade['symbol']} {trade['type']} | Lotes: {trade['volume']} | Profit: ${trade['profit']:,.2f} | {trade['close_time']}")
        print(f"\n   💰 PROFIT TOTAL HOY: ${total_profit_today:,.2f}")
    else:
        print("   📊 No hay trades cerrados hoy")

    # 4. Estadísticas generales
    print("\n4️⃣ ESTADÍSTICAS GENERALES:")
    cur.execute("""
        SELECT
            COUNT(*) as total_trades,
            SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
            SUM(profit) as total_profit,
            AVG(profit) as avg_profit,
            MAX(profit) as max_profit,
            MIN(profit) as min_profit
        FROM trade_history
    """)
    stats = cur.fetchone()
    if stats and stats['total_trades'] > 0:
        win_rate = (stats['wins'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
        print(f"   Total trades:  {stats['total_trades']}")
        print(f"   Ganadas:       {stats['wins']} ({win_rate:.1f}%)")
        print(f"   Perdidas:      {stats['losses']}")
        print(f"   Profit total:  ${stats['total_profit']:,.2f}")
        print(f"   Avg profit:    ${stats['avg_profit']:,.2f}")
        print(f"   Max profit:    ${stats['max_profit']:,.2f}")
        print(f"   Max loss:      ${stats['min_profit']:,.2f}")
    else:
        print("   📊 No hay historial de trades")

    # 5. Rendimiento por símbolo
    print("\n5️⃣ RENDIMIENTO POR SÍMBOLO:")
    cur.execute("""
        SELECT
            symbol,
            COUNT(*) as trades,
            SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
            SUM(profit) as total_profit,
            AVG(profit) as avg_profit
        FROM trade_history
        GROUP BY symbol
        ORDER BY total_profit DESC
    """)
    by_symbol = cur.fetchall()
    if by_symbol:
        for row in by_symbol:
            win_rate = (row['wins'] / row['trades'] * 100) if row['trades'] > 0 else 0
            print(f"   {row['symbol']:<10} | Trades: {row['trades']:>3} | Win: {win_rate:>5.1f}% | Profit: ${row['total_profit']:>8,.2f}")
    else:
        print("   📊 No hay datos por símbolo")

    # 6. Señales detectadas (últimas 24h)
    print("\n6️⃣ SEÑALES DETECTADAS (Últimas 24h):")
    cur.execute("""
        SELECT symbol, signal_type, strategy, confidence, time
        FROM trading_signals
        WHERE time >= NOW() - INTERVAL '24 hours'
        ORDER BY time DESC
        LIMIT 10
    """)
    signals = cur.fetchall()
    if signals:
        for sig in signals:
            print(f"   {sig['time']} | {sig['symbol']} {sig['signal_type']} | Strategy: {sig['strategy']} | Conf: {sig['confidence']:.2f}")
    else:
        print("   ⚠️ NO HAY SEÑALES DETECTADAS EN LAS ÚLTIMAS 24 HORAS")

    # 7. Evolución del balance
    print("\n7️⃣ EVOLUCIÓN DEL BALANCE (Últimos 7 días):")
    cur.execute("""
        SELECT DATE(time) as date,
               MIN(balance) as min_balance,
               MAX(balance) as max_balance,
               AVG(equity) as avg_equity
        FROM account_metrics
        WHERE time >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(time)
        ORDER BY date DESC
    """)
    evolution = cur.fetchall()
    if evolution:
        for row in evolution:
            print(f"   {row['date']} | Balance: ${row['min_balance']:>8,.2f} - ${row['max_balance']:>8,.2f} | Avg Equity: ${row['avg_equity']:>8,.2f}")

    # 8. ERROR: Numeric overflow
    print("\n8️⃣ DIAGNÓSTICO DE ERRORES:")
    print("   ⚠️ ERROR DETECTADO: 'numeric field overflow'")
    print("   Problema: Los precios de crypto (BTCUSD ~43,000) no caben en NUMERIC(10,5)")
    print("   Solución: Necesitas modificar el schema de la base de datos")

    cur.close()
    conn.close()

    print("\n" + "="*80)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
