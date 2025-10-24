"""
Diagnóstico Completo: Por qué NO se detectan señales
Analiza datos, indicadores y condiciones de la estrategia
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configurar UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Importar módulos del bridge
sys.path.insert(0, os.path.dirname(__file__))
from bridge_v3.services.database_service import DatabaseService
from bridge_v3.services.mt5_service import MT5Service
from crypto_strategy_relaxed import CryptoStrategyRelaxed
from dotenv import load_dotenv

load_dotenv()

def calculate_indicators(df):
    """Calcula todos los indicadores técnicos"""
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # EMAs
    df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()

    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

    # VWAP
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

    # Volumen promedio
    df['volume_avg'] = df['volume'].rolling(window=20).mean()

    return df

def analyze_symbol(symbol, db_service, strategy):
    """Analiza un símbolo en detalle"""
    print(f"\n{'='*80}")
    print(f"📊 ANALIZANDO: {symbol}")
    print(f"{'='*80}\n")

    # Obtener datos
    df = db_service.get_price_data(symbol, 15, limit=100)

    if df is None or len(df) < 50:
        print(f"❌ DATOS INSUFICIENTES: {len(df) if df is not None else 0} barras (necesita 50+)")
        return

    print(f"✅ Datos disponibles: {len(df)} barras")
    print(f"   Rango: {df['time'].min()} → {df['time'].max()}")
    print(f"   Precio actual: ${df['close'].iloc[-1]:,.2f}")
    print(f"   Precio máximo: ${df['high'].max():,.2f}")
    print(f"   Precio mínimo: ${df['low'].min():,.2f}")

    # Calcular indicadores
    df = calculate_indicators(df)

    # Valores actuales
    current = df.iloc[-1]
    prev = df.iloc[-2]

    print(f"\n📈 INDICADORES TÉCNICOS (Última barra):")
    print(f"   RSI:              {current['rsi']:.2f}")
    print(f"   EMA Fast (9):     ${current['ema_fast']:,.2f}")
    print(f"   EMA Slow (21):    ${current['ema_slow']:,.2f}")
    print(f"   MACD:             {current['macd']:.2f}")
    print(f"   MACD Signal:      {current['macd_signal']:.2f}")
    print(f"   MACD Histogram:   {current['macd_histogram']:.2f}")
    print(f"   BB Upper:         ${current['bb_upper']:,.2f}")
    print(f"   BB Middle:        ${current['bb_middle']:,.2f}")
    print(f"   BB Lower:         ${current['bb_lower']:,.2f}")
    print(f"   VWAP:             ${current['vwap']:,.2f}")
    print(f"   Volumen:          {current['volume']:,.0f}")
    print(f"   Volumen Promedio: {current['volume_avg']:,.0f}")

    # Análisis de condiciones LONG
    print(f"\n🔍 CONDICIONES PARA SEÑAL LONG:")

    # 1. RSI
    rsi_oversold = current['rsi'] < 40
    print(f"   1. RSI < 40:           {current['rsi']:.2f} → {'✅ SÍ' if rsi_oversold else '❌ NO'}")

    # 2. EMA Crossover
    ema_bullish = current['ema_fast'] > current['ema_slow']
    print(f"   2. EMA Fast > Slow:    {current['ema_fast']:.2f} > {current['ema_slow']:.2f} → {'✅ SÍ' if ema_bullish else '❌ NO'}")

    # 3. MACD Histogram positivo
    macd_positive = current['macd_histogram'] > 0
    print(f"   3. MACD Hist > 0:      {current['macd_histogram']:.2f} → {'✅ SÍ' if macd_positive else '❌ NO'}")

    # 4. Precio sobre VWAP
    price_above_vwap = current['close'] > current['vwap']
    vwap_diff_pct = ((current['close'] - current['vwap']) / current['vwap']) * 100
    print(f"   4. Precio > VWAP:      ${current['close']:,.2f} > ${current['vwap']:,.2f} ({vwap_diff_pct:+.2f}%) → {'✅ SÍ' if price_above_vwap else '❌ NO'}")

    # 5. Volumen
    volume_ok = current['volume'] >= current['volume_avg'] * 1.0
    volume_ratio = current['volume'] / current['volume_avg']
    print(f"   5. Volumen >= 1.0x:    {current['volume']:,.0f} / {current['volume_avg']:,.0f} ({volume_ratio:.2f}x) → {'✅ SÍ' if volume_ok else '❌ NO'}")

    # 6. Precio cerca de BB Lower
    bb_distance = ((current['close'] - current['bb_lower']) / current['close']) * 100
    near_bb_lower = current['close'] <= current['bb_lower'] * 1.02
    print(f"   6. Precio ≤ BB Lower:  ${current['close']:,.2f} vs ${current['bb_lower']:,.2f} ({bb_distance:+.2f}%) → {'✅ SÍ' if near_bb_lower else '❌ NO'}")

    long_conditions = [rsi_oversold, ema_bullish, macd_positive, price_above_vwap]
    long_count = sum(long_conditions)

    print(f"\n   📊 RESUMEN LONG: {long_count}/4 condiciones cumplidas")
    if long_count >= 3:
        print(f"   ✅ SEÑAL LONG VÁLIDA (requiere 3/4)")
    else:
        print(f"   ❌ NO hay señal LONG (falta {3 - long_count} condición{'es' if 3 - long_count > 1 else ''})")

    # Análisis de condiciones SHORT
    print(f"\n🔍 CONDICIONES PARA SEÑAL SHORT:")

    # 1. RSI
    rsi_overbought = current['rsi'] > 60
    print(f"   1. RSI > 60:           {current['rsi']:.2f} → {'✅ SÍ' if rsi_overbought else '❌ NO'}")

    # 2. EMA Crossover
    ema_bearish = current['ema_fast'] < current['ema_slow']
    print(f"   2. EMA Fast < Slow:    {current['ema_fast']:.2f} < {current['ema_slow']:.2f} → {'✅ SÍ' if ema_bearish else '❌ NO'}")

    # 3. MACD Histogram negativo
    macd_negative = current['macd_histogram'] < 0
    print(f"   3. MACD Hist < 0:      {current['macd_histogram']:.2f} → {'✅ SÍ' if macd_negative else '❌ NO'}")

    # 4. Precio bajo VWAP
    price_below_vwap = current['close'] < current['vwap']
    print(f"   4. Precio < VWAP:      ${current['close']:,.2f} < ${current['vwap']:,.2f} ({vwap_diff_pct:+.2f}%) → {'✅ SÍ' if price_below_vwap else '❌ NO'}")

    # 5. Volumen
    print(f"   5. Volumen >= 1.0x:    {current['volume']:,.0f} / {current['volume_avg']:,.0f} ({volume_ratio:.2f}x) → {'✅ SÍ' if volume_ok else '❌ NO'}")

    # 6. Precio cerca de BB Upper
    bb_distance_upper = ((current['close'] - current['bb_upper']) / current['close']) * 100
    near_bb_upper = current['close'] >= current['bb_upper'] * 0.98
    print(f"   6. Precio ≥ BB Upper:  ${current['close']:,.2f} vs ${current['bb_upper']:,.2f} ({bb_distance_upper:+.2f}%) → {'✅ SÍ' if near_bb_upper else '❌ NO'}")

    short_conditions = [rsi_overbought, ema_bearish, macd_negative, price_below_vwap]
    short_count = sum(short_conditions)

    print(f"\n   📊 RESUMEN SHORT: {short_count}/4 condiciones cumplidas")
    if short_count >= 3:
        print(f"   ✅ SEÑAL SHORT VÁLIDA (requiere 3/4)")
    else:
        print(f"   ❌ NO hay señal SHORT (falta {3 - short_count} condición{'es' if 3 - short_count > 1 else ''})")

    # Tendencia general
    print(f"\n🎯 ANÁLISIS DE TENDENCIA:")
    if current['ema_fast'] > current['ema_slow']:
        trend = "ALCISTA (Bullish)"
        trend_strength = ((current['ema_fast'] - current['ema_slow']) / current['ema_slow']) * 100
    else:
        trend = "BAJISTA (Bearish)"
        trend_strength = ((current['ema_slow'] - current['ema_fast']) / current['ema_slow']) * 100

    print(f"   Tendencia: {trend} ({trend_strength:.2f}% separación)")

    if current['rsi'] < 30:
        print(f"   RSI: SOBREVENTA EXTREMA ({current['rsi']:.2f})")
    elif current['rsi'] < 40:
        print(f"   RSI: Zona de sobreventa ({current['rsi']:.2f})")
    elif current['rsi'] > 70:
        print(f"   RSI: SOBRECOMPRA EXTREMA ({current['rsi']:.2f})")
    elif current['rsi'] > 60:
        print(f"   RSI: Zona de sobrecompra ({current['rsi']:.2f})")
    else:
        print(f"   RSI: Neutral ({current['rsi']:.2f})")

    # Recomendación
    print(f"\n💡 RECOMENDACIÓN:")
    if long_count >= 3:
        print(f"   🟢 COMPRAR (LONG) - {long_count}/4 condiciones cumplidas")
    elif short_count >= 3:
        print(f"   🔴 VENDER (SHORT) - {short_count}/4 condiciones cumplidas")
    else:
        print(f"   ⚪ ESPERAR - No hay señal clara")
        print(f"      LONG: {long_count}/4, SHORT: {short_count}/4")

def main():
    print("="*80)
    print("🔍 DIAGNÓSTICO: ¿POR QUÉ NO HAY SEÑALES DE TRADING?")
    print("="*80)

    # Inicializar servicios
    print("\n📡 Conectando a servicios...")

    try:
        db_service = DatabaseService()
        print("   ✅ Base de datos conectada")
    except Exception as e:
        print(f"   ❌ Error de base de datos: {e}")
        return

    try:
        mt5_service = MT5Service()
        if not mt5_service.initialize():
            print("   ❌ Error: MT5 no pudo inicializar")
            return
        print("   ✅ MT5 conectado")
    except Exception as e:
        print(f"   ❌ Error de MT5: {e}")
        return

    strategy = CryptoStrategyRelaxed()
    print("   ✅ Estrategia cargada: CryptoStrategyRelaxed")

    # Obtener símbolos crypto
    crypto_pairs = os.getenv('CRYPTO_PAIRS', 'BTCUSD,ETHUSD,LTCUSD,XRPUSD').split(',')

    print(f"\n📋 Símbolos a analizar: {', '.join(crypto_pairs)}")

    # Analizar cada símbolo
    for symbol in crypto_pairs:
        analyze_symbol(symbol.strip(), db_service, strategy)

    print(f"\n{'='*80}")
    print("✅ DIAGNÓSTICO COMPLETO")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
