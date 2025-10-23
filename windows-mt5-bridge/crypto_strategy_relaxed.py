"""
Estrategia de Trading de Criptomonedas - VERSIÓN RELAJADA
Con condiciones más flexibles para generar más señales

DIFERENCIAS vs estrategia original:
1. Volumen reducido de 1.2x a 1.0x (volumen promedio o superior)
2. RSI ampliado: Oversold 40 (vs 30), Overbought 60 (vs 70)
3. Requiere 3 de 4 condiciones (vs 4 de 4)
4. Sin restricciones de horario (trading 24/7)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CryptoStrategyRelaxed:
    """Estrategia de criptomonedas con condiciones RELAJADAS"""

    def __init__(self):
        # Parámetros de indicadores
        self.rsi_period = 14
        self.rsi_oversold = 40  # ← Cambiado de 30 a 40 (más señales)
        self.rsi_overbought = 60  # ← Cambiado de 70 a 60 (más señales)

        self.ema_fast = 9
        self.ema_slow = 21

        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        self.bb_period = 20
        self.bb_std = 2

        self.volume_period = 20
        self.volume_multiplier = 1.0  # ← Cambiado de 1.2 a 1.0 (más flexible)

        # Gestión de riesgo
        self.stop_loss_pct = 2.0
        self.take_profit_pct = 3.5

        # Umbral de condiciones (3 de 4 deben cumplirse)
        self.min_conditions = 3  # ← NUEVO: Requiere 3 de 4 condiciones

    def calculate_rsi(self, prices, period=14):
        """Calcular RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_ema(self, prices, period):
        """Calcular EMA"""
        return prices.ewm(span=period, adjust=False).mean()

    def calculate_macd(self, prices):
        """Calcular MACD"""
        ema_fast = self.calculate_ema(prices, self.macd_fast)
        ema_slow = self.calculate_ema(prices, self.macd_slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, self.macd_signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calcular Bandas de Bollinger"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return upper_band, sma, lower_band

    def calculate_vwap(self, df):
        """Calcular VWAP"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

    def check_volume_condition(self, current_volume, avg_volume):
        """Verificar condición de volumen (RELAJADA)"""
        return current_volume >= (avg_volume * self.volume_multiplier)

    def analyze_signal(self, df, symbol):
        """
        Analizar señales de trading (VERSIÓN RELAJADA)

        Returns:
            'LONG': Señal de compra
            'SHORT': Señal de venta
            None: Sin señal
        """
        if len(df) < max(self.rsi_period, self.ema_slow, self.bb_period, self.volume_period):
            logger.warning(f"{symbol}: Datos insuficientes para análisis")
            return None

        # Calcular indicadores
        close_prices = df['close']

        rsi = self.calculate_rsi(close_prices, self.rsi_period)
        ema_fast = self.calculate_ema(close_prices, self.ema_fast)
        ema_slow = self.calculate_ema(close_prices, self.ema_slow)
        macd_line, signal_line, macd_histogram = self.calculate_macd(close_prices)
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands(close_prices)
        vwap = self.calculate_vwap(df)

        # Volumen promedio
        avg_volume = df['volume'].rolling(window=self.volume_period).mean()

        # Valores actuales
        current_rsi = rsi.iloc[-1]
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        current_macd_histogram = macd_histogram.iloc[-1]
        current_price = close_prices.iloc[-1]
        current_vwap = vwap.iloc[-1]
        current_volume = df['volume'].iloc[-1]
        current_avg_volume = avg_volume.iloc[-1]

        # Verificar volumen (RELAJADO)
        if not self.check_volume_condition(current_volume, current_avg_volume):
            logger.debug(f"{symbol}: Volumen insuficiente")
            return None

        # ═══════════════════════════════════════════════════════════════
        # SEÑAL LONG (Compra) - RELAJADA (3 de 4 condiciones)
        # ═══════════════════════════════════════════════════════════════
        long_conditions = {
            'rsi': current_rsi < self.rsi_oversold,
            'ema': current_ema_fast > current_ema_slow,
            'macd': current_macd_histogram > 0,
            'vwap': current_price > current_vwap
        }

        long_conditions_met = sum(long_conditions.values())

        if long_conditions_met >= self.min_conditions:
            logger.info(f"""
{symbol} - SEÑAL LONG detectada ({long_conditions_met}/{len(long_conditions)} condiciones):
  {'✅' if long_conditions['rsi'] else '❌'} RSI: {current_rsi:.2f} < {self.rsi_oversold}
  {'✅' if long_conditions['ema'] else '❌'} EMA9: {current_ema_fast:.2f} > EMA21: {current_ema_slow:.2f}
  {'✅' if long_conditions['macd'] else '❌'} MACD Histogram: {current_macd_histogram:.5f} > 0
  {'✅' if long_conditions['vwap'] else '❌'} Precio: {current_price:.2f} > VWAP: {current_vwap:.2f}
  ✅ Volumen: {current_volume:.0f} >= Avg: {current_avg_volume:.0f}
            """)
            return 'LONG'

        # ═══════════════════════════════════════════════════════════════
        # SEÑAL SHORT (Venta) - RELAJADA (3 de 4 condiciones)
        # ═══════════════════════════════════════════════════════════════
        short_conditions = {
            'rsi': current_rsi > self.rsi_overbought,
            'ema': current_ema_fast < current_ema_slow,
            'macd': current_macd_histogram < 0,
            'vwap': current_price < current_vwap
        }

        short_conditions_met = sum(short_conditions.values())

        if short_conditions_met >= self.min_conditions:
            logger.info(f"""
{symbol} - SEÑAL SHORT detectada ({short_conditions_met}/{len(short_conditions)} condiciones):
  {'✅' if short_conditions['rsi'] else '❌'} RSI: {current_rsi:.2f} > {self.rsi_overbought}
  {'✅' if short_conditions['ema'] else '❌'} EMA9: {current_ema_fast:.2f} < EMA21: {current_ema_slow:.2f}
  {'✅' if short_conditions['macd'] else '❌'} MACD Histogram: {current_macd_histogram:.5f} < 0
  {'✅' if short_conditions['vwap'] else '❌'} Precio: {current_price:.2f} < VWAP: {current_vwap:.2f}
  ✅ Volumen: {current_volume:.0f} >= Avg: {current_avg_volume:.0f}
            """)
            return 'SHORT'

        # Sin señal
        logger.debug(f"{symbol}: Sin señal (LONG: {long_conditions_met}/4, SHORT: {short_conditions_met}/4)")
        return None

    def calculate_sl_tp(self, entry_price, signal_type):
        """Calcular Stop Loss y Take Profit"""
        if signal_type == 'LONG':
            sl = entry_price * (1 - self.stop_loss_pct / 100)
            tp = entry_price * (1 + self.take_profit_pct / 100)
        else:  # SHORT
            sl = entry_price * (1 + self.stop_loss_pct / 100)
            tp = entry_price * (1 - self.take_profit_pct / 100)

        return sl, tp

    def calculate_position_size(self, balance, risk_pct, sl_pct):
        """Calcular tamaño de posición basado en riesgo"""
        risk_amount = balance * (risk_pct / 100)
        position_size = risk_amount / (sl_pct / 100)
        return position_size
