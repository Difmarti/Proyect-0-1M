"""
Estrategia de Trading de Criptomonedas - Operaciones Cortas
Integrada con estrategia Forex existente

Características:
- Timeframes: 5m, 15m, 30m, 1h
- Indicadores: RSI, EMA, MACD, Bollinger Bands, VWAP
- Operativa: 24/7
- Límite pérdida diaria: 10% (compartido con Forex)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CryptoStrategy:
    """Estrategia de criptomonedas con operaciones cortas"""

    def __init__(self):
        # Parámetros de indicadores
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70

        self.ema_fast = 9
        self.ema_slow = 21

        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        self.bb_period = 20
        self.bb_std = 2

        self.volume_period = 20
        self.volume_multiplier = 1.2

        # Gestión de riesgo
        self.stop_loss_pct = 2.0  # 2%
        self.take_profit_pct = 3.5  # 3.5%
        self.trailing_stop_activation = 2.0  # Activar en +2%
        self.trailing_stop_distance = 1.0  # Seguir con -1%

        # Horarios óptimos UTC
        self.optimal_hours = [
            (13, 16),  # Apertura Wall Street
            (0, 2),    # Cierre USA
            (8, 10),   # Asia
            (7, 9)     # Europa
        ]

        self.avoid_hours = [3, 4, 5, 6]  # Bajo volumen

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
        """Calcular VWAP (Volume Weighted Average Price)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

    def is_optimal_hour(self, current_hour):
        """Verificar si es hora óptima para operar"""
        if current_hour in self.avoid_hours:
            return False

        for start, end in self.optimal_hours:
            if start <= current_hour < end:
                return True

        return True  # Permitir otras horas (24/7)

    def check_volume_condition(self, current_volume, avg_volume):
        """Verificar condición de volumen"""
        return current_volume > (avg_volume * self.volume_multiplier)

    def analyze_signal(self, df, symbol):
        """
        Analizar señales de trading

        Returns:
            'LONG': Señal de compra
            'SHORT': Señal de venta
            None: Sin señal
        """
        if len(df) < max(self.rsi_period, self.ema_slow, self.bb_period, self.volume_period):
            logger.warning(f"{symbol}: Datos insuficientes para análisis")
            return None

        # Obtener hora actual
        current_hour = datetime.now().hour

        # Verificar horario
        if not self.is_optimal_hour(current_hour):
            logger.debug(f"{symbol}: Fuera de horario óptimo (hora {current_hour})")
            return None

        # Calcular indicadores
        close_prices = df['close']

        rsi = self.calculate_rsi(close_prices, self.rsi_period)
        ema_fast = self.calculate_ema(close_prices, self.ema_fast)
        ema_slow = self.calculate_ema(close_prices, self.ema_slow)
        macd_line, signal_line, macd_histogram = self.calculate_macd(close_prices)
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands(close_prices, self.bb_period, self.bb_std)
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

        # Verificar volumen
        if not self.check_volume_condition(current_volume, current_avg_volume):
            logger.debug(f"{symbol}: Volumen insuficiente")
            return None

        # SEÑAL LONG (Compra)
        long_conditions = [
            current_rsi < self.rsi_oversold,
            current_ema_fast > current_ema_slow,
            current_macd_histogram > 0,
            current_price > current_vwap
        ]

        if all(long_conditions):
            logger.info(f"""
{symbol} - SEÑAL LONG detectada:
  RSI: {current_rsi:.2f} < {self.rsi_oversold}
  EMA9: {current_ema_fast:.2f} > EMA21: {current_ema_slow:.2f}
  MACD Histogram: {current_macd_histogram:.5f} > 0
  Precio: {current_price:.2f} > VWAP: {current_vwap:.2f}
  Volumen: {current_volume:.0f} > Avg: {current_avg_volume:.0f}
            """)
            return 'LONG'

        # SEÑAL SHORT (Venta)
        short_conditions = [
            current_rsi > self.rsi_overbought,
            current_ema_fast < current_ema_slow,
            current_macd_histogram < 0,
            current_price < current_vwap
        ]

        if all(short_conditions):
            logger.info(f"""
{symbol} - SEÑAL SHORT detectada:
  RSI: {current_rsi:.2f} > {self.rsi_overbought}
  EMA9: {current_ema_fast:.2f} < EMA21: {current_ema_slow:.2f}
  MACD Histogram: {current_macd_histogram:.5f} < 0
  Precio: {current_price:.2f} < VWAP: {current_vwap:.2f}
  Volumen: {current_volume:.0f} > Avg: {current_avg_volume:.0f}
            """)
            return 'SHORT'

        return None

    def calculate_position_size(self, balance, risk_percentage, stop_loss_pct):
        """
        Calcular tamaño de posición basado en riesgo

        Args:
            balance: Balance disponible
            risk_percentage: % de riesgo por operación (1-5%)
            stop_loss_pct: % de stop loss

        Returns:
            Tamaño de posición en lotes
        """
        risk_amount = balance * (risk_percentage / 100)
        position_size = risk_amount / (stop_loss_pct / 100)

        # Limitar a máximo 5% del balance
        max_position = balance * 0.05
        position_size = min(position_size, max_position)

        return position_size

    def calculate_sl_tp(self, entry_price, signal_type):
        """
        Calcular Stop Loss y Take Profit

        Args:
            entry_price: Precio de entrada
            signal_type: 'LONG' o 'SHORT'

        Returns:
            (stop_loss, take_profit)
        """
        if signal_type == 'LONG':
            stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.take_profit_pct / 100)
        else:  # SHORT
            stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.take_profit_pct / 100)

        return stop_loss, take_profit

    def should_activate_trailing_stop(self, entry_price, current_price, signal_type):
        """Verificar si se debe activar trailing stop"""
        if signal_type == 'LONG':
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100

        return profit_pct >= self.trailing_stop_activation

    def calculate_trailing_stop(self, current_price, signal_type):
        """Calcular nivel de trailing stop"""
        if signal_type == 'LONG':
            trailing_stop = current_price * (1 - self.trailing_stop_distance / 100)
        else:  # SHORT
            trailing_stop = current_price * (1 + self.trailing_stop_distance / 100)

        return trailing_stop
