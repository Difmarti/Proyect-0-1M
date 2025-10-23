"""
Script de diagnóstico para ver por qué no se generan señales crypto
"""

import sys
import io

# Configure UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append('.')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from crypto_strategy import CryptoStrategy

# Configuración
CRYPTO_PAIRS = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD']
TIMEFRAME = mt5.TIMEFRAME_M15

def main():
    print("=" * 80)
    print("DIAGNÓSTICO DE SEÑALES CRYPTO")
    print("=" * 80)

    # Inicializar MT5
    if not mt5.initialize():
        print(f"❌ Error inicializando MT5: {mt5.last_error()}")
        return

    print(f"✅ MT5 inicializado")
    print(f"Hora actual: {datetime.now()}")
    print(f"Hora UTC: {datetime.utcnow()}")
    print()

    # Crear estrategia
    strategy = CryptoStrategy()

    print(f"Parámetros de estrategia:")
    print(f"  RSI Oversold: {strategy.rsi_oversold}")
    print(f"  RSI Overbought: {strategy.rsi_overbought}")
    print(f"  Volumen multiplicador: {strategy.volume_multiplier}")
    print(f"  Horarios óptimos: {strategy.optimal_hours}")
    print(f"  Horas a evitar: {strategy.avoid_hours}")
    print()

    # Analizar cada par
    for symbol in CRYPTO_PAIRS:
        print("=" * 80)
        print(f"ANALIZANDO: {symbol}")
        print("=" * 80)

        # Obtener datos
        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 200)

        if rates is None or len(rates) == 0:
            print(f"❌ No hay datos para {symbol}")
            print()
            continue

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # Asegurar columna volume
        if 'volume' not in df.columns and 'tick_volume' in df.columns:
            df['volume'] = df['tick_volume']

        print(f"✅ Datos obtenidos: {len(df)} barras")
        print(f"   Última actualización: {df['time'].iloc[-1]}")
        print()

        # Hora actual
        current_hour = datetime.now().hour
        is_optimal = strategy.is_optimal_hour(current_hour)

        print(f"HORARIO:")
        print(f"  Hora actual: {current_hour}")
        print(f"  Es horario óptimo: {'✅ SÍ' if is_optimal else '❌ NO'}")
        if not is_optimal:
            print(f"  ⚠️ SEÑAL BLOQUEADA POR HORARIO")
        print()

        # Calcular indicadores
        close_prices = df['close']

        rsi = strategy.calculate_rsi(close_prices, strategy.rsi_period)
        ema_fast = strategy.calculate_ema(close_prices, strategy.ema_fast)
        ema_slow = strategy.calculate_ema(close_prices, strategy.ema_slow)
        macd_line, signal_line, macd_histogram = strategy.calculate_macd(close_prices)
        upper_bb, middle_bb, lower_bb = strategy.calculate_bollinger_bands(
            close_prices, strategy.bb_period, strategy.bb_std
        )
        vwap = strategy.calculate_vwap(df)

        avg_volume = df['volume'].rolling(window=strategy.volume_period).mean()

        # Valores actuales
        current_rsi = rsi.iloc[-1]
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        current_macd_histogram = macd_histogram.iloc[-1]
        current_price = close_prices.iloc[-1]
        current_vwap = vwap.iloc[-1]
        current_volume = df['volume'].iloc[-1]
        current_avg_volume = avg_volume.iloc[-1]

        print(f"INDICADORES ACTUALES:")
        print(f"  Precio actual: ${current_price:.2f}")
        print(f"  RSI: {current_rsi:.2f} (Oversold: <{strategy.rsi_oversold}, Overbought: >{strategy.rsi_overbought})")
        print(f"  EMA Fast (9): ${current_ema_fast:.2f}")
        print(f"  EMA Slow (21): ${current_ema_slow:.2f}")
        print(f"  MACD Histogram: {current_macd_histogram:.5f}")
        print(f"  VWAP: ${current_vwap:.2f}")
        print(f"  Volumen actual: {current_volume:.0f}")
        print(f"  Volumen promedio: {current_avg_volume:.0f}")
        print(f"  Volumen requerido: {current_avg_volume * strategy.volume_multiplier:.0f}")
        print()

        # Verificar condiciones
        volume_ok = current_volume > (current_avg_volume * strategy.volume_multiplier)

        print(f"VERIFICACIÓN DE CONDICIONES:")
        print(f"  Volumen suficiente: {'✅' if volume_ok else '❌'} ({current_volume:.0f} vs {current_avg_volume * strategy.volume_multiplier:.0f})")
        if not volume_ok:
            print(f"    ⚠️ SEÑAL BLOQUEADA POR VOLUMEN BAJO")
        print()

        # Condiciones LONG
        print(f"CONDICIONES LONG:")
        long_conditions = {
            f"RSI < {strategy.rsi_oversold}": current_rsi < strategy.rsi_oversold,
            f"EMA Fast > EMA Slow": current_ema_fast > current_ema_slow,
            f"MACD > 0": current_macd_histogram > 0,
            f"Precio > VWAP": current_price > current_vwap
        }

        for cond_name, cond_met in long_conditions.items():
            status = "✅" if cond_met else "❌"
            print(f"  {status} {cond_name}")

        long_signal = all(long_conditions.values()) and volume_ok and is_optimal
        print(f"  SEÑAL LONG: {'✅ ACTIVADA' if long_signal else '❌ NO'}")
        print()

        # Condiciones SHORT
        print(f"CONDICIONES SHORT:")
        short_conditions = {
            f"RSI > {strategy.rsi_overbought}": current_rsi > strategy.rsi_overbought,
            f"EMA Fast < EMA Slow": current_ema_fast < current_ema_slow,
            f"MACD < 0": current_macd_histogram < 0,
            f"Precio < VWAP": current_price < current_vwap
        }

        for cond_name, cond_met in short_conditions.items():
            status = "✅" if cond_met else "❌"
            print(f"  {status} {cond_name}")

        short_signal = all(short_conditions.values()) and volume_ok and is_optimal
        print(f"  SEÑAL SHORT: {'✅ ACTIVADA' if short_signal else '❌ NO'}")
        print()

        # Llamar a la estrategia
        signal = strategy.analyze_signal(df, symbol)
        print(f"RESULTADO DE ESTRATEGIA: {signal if signal else 'SIN SEÑAL'}")
        print()

    mt5.shutdown()
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 80)


if __name__ == "__main__":
    main()
