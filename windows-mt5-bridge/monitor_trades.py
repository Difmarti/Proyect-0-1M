"""
Monitor de Trading en Tiempo Real
Analiza el log de mt5_bridge_v3.log y muestra alertas de operaciones
"""

import time
import re
import os
from datetime import datetime
from collections import deque
import sys

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

class TradeMonitor:
    def __init__(self, log_file='mt5_bridge_v3.log'):
        self.log_file = log_file
        self.last_position = 0
        self.active_signals = {}
        self.open_trades = {}
        self.last_alert_time = {}

    def print_banner(self):
        """Muestra banner inicial"""
        print("\n" + "="*80)
        print("🤖 MONITOR DE TRADING EN TIEMPO REAL - Bridge V3")
        print("="*80)
        print(f"📁 Archivo: {self.log_file}")
        print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

    def print_alert(self, alert_type, symbol, details):
        """Muestra alerta formateada"""
        timestamp = datetime.now().strftime('%H:%M:%S')

        if alert_type == 'SIGNAL_DETECTED':
            icon = "🔔"
            color = "\033[93m"  # Amarillo
            title = "SEÑAL DETECTADA"
        elif alert_type == 'TRADE_OPENED':
            icon = "✅"
            color = "\033[92m"  # Verde
            title = "OPERACIÓN ABIERTA"
        elif alert_type == 'TRADE_CLOSED':
            icon = "🔒"
            color = "\033[94m"  # Azul
            title = "OPERACIÓN CERRADA"
        elif alert_type == 'TRADE_FAILED':
            icon = "❌"
            color = "\033[91m"  # Rojo
            title = "OPERACIÓN FALLIDA"
        elif alert_type == 'RISK_WARNING':
            icon = "⚠️"
            color = "\033[95m"  # Magenta
            title = "ADVERTENCIA DE RIESGO"
        else:
            icon = "ℹ️"
            color = "\033[0m"  # Normal
            title = "INFO"

        reset = "\033[0m"

        print(f"\n{color}{'='*80}")
        print(f"{icon} [{timestamp}] {title} - {symbol}")
        print(f"{'='*80}{reset}")

        for key, value in details.items():
            print(f"  {key}: {value}")

        print(f"{color}{'='*80}{reset}\n")

    def parse_signal_line(self, line):
        """Parsea línea de señal detectada"""
        # Ejemplo: "2024-01-20 09:15:30 - INFO - BTCUSD - SEÑAL SHORT detectada (3/4 condiciones)"
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?([A-Z]+USD)\s*-\s*SEÑAL\s+(LONG|SHORT)\s+detectada.*?\((\d+)/(\d+)\s+condiciones\)'
        match = re.search(pattern, line)

        if match:
            timestamp_str, symbol, signal_type, conditions_met, total_conditions = match.groups()
            return {
                'timestamp': timestamp_str,
                'symbol': symbol,
                'signal_type': signal_type,
                'conditions_met': int(conditions_met),
                'total_conditions': int(total_conditions)
            }
        return None

    def parse_position_size(self, line):
        """Parsea tamaño de posición calculado"""
        # Ejemplo: "Position size calculated: 0.01 lots (Risk: $20.00)"
        pattern = r'Position size calculated:\s+([\d.]+)\s+lots.*?Risk:\s+\$?([\d.]+)'
        match = re.search(pattern, line)

        if match:
            lots, risk = match.groups()
            return {
                'lots': float(lots),
                'risk': float(risk)
            }
        return None

    def parse_trade_opened(self, line):
        """Parsea operación abierta exitosamente"""
        # Ejemplo: "✅ Trade OPENED successfully: Ticket 123456789"
        pattern = r'Trade OPENED successfully:\s+Ticket\s+(\d+)'
        match = re.search(pattern, line)

        if match:
            return {'ticket': int(match.group(1))}
        return None

    def parse_order_executed(self, line):
        """Parsea detalles de orden ejecutada"""
        # Ejemplo: "Order executed: BTCUSD SHORT @ 43250.50 | SL: 44115.01 | TP: 41737.00"
        pattern = r'Order executed:\s+([A-Z]+USD)\s+(LONG|SHORT)\s+@\s+([\d.]+)\s+\|\s+SL:\s+([\d.]+)\s+\|\s+TP:\s+([\d.]+)'
        match = re.search(pattern, line)

        if match:
            symbol, order_type, price, sl, tp = match.groups()
            return {
                'symbol': symbol,
                'type': order_type,
                'entry_price': float(price),
                'stop_loss': float(sl),
                'take_profit': float(tp)
            }
        return None

    def parse_trade_failed(self, line):
        """Parsea operación fallida"""
        # Ejemplo: "❌ Trade FAILED for BTCUSD: AutoTrading disabled by client (retcode: 10027)"
        pattern = r'Trade FAILED for\s+([A-Z]+USD):\s+(.+?)(?:\(retcode:\s+(\d+)\))?$'
        match = re.search(pattern, line)

        if match:
            symbol, reason, retcode = match.groups()
            return {
                'symbol': symbol,
                'reason': reason.strip(),
                'retcode': int(retcode) if retcode else None
            }
        return None

    def parse_position_closed(self, line):
        """Parsea posición cerrada"""
        # Ejemplo: "Position 123456 closed successfully"
        pattern = r'Position\s+(\d+)\s+closed\s+successfully'
        match = re.search(pattern, line)

        if match:
            return {'ticket': int(match.group(1))}
        return None

    def parse_risk_warning(self, line):
        """Parsea advertencias de riesgo"""
        patterns = {
            'daily_limit': r'Daily loss limit reached:\s+([\d.]+)%',
            'max_trades': r'Maximum simultaneous trades reached:\s+(\d+)',
            'insufficient_margin': r'Insufficient margin'
        }

        for warning_type, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                return {
                    'type': warning_type,
                    'value': match.group(1) if match.groups() else None
                }
        return None

    def calculate_risk_reward(self, entry, sl, tp, order_type):
        """Calcula ratio riesgo/beneficio"""
        if order_type == 'LONG':
            risk = abs(entry - sl)
            reward = abs(tp - entry)
        else:  # SHORT
            risk = abs(sl - entry)
            reward = abs(entry - tp)

        return reward / risk if risk > 0 else 0.0

    def monitor(self):
        """Monitorea el log en tiempo real"""
        self.print_banner()

        # Buffer para agrupar información relacionada
        pending_signal = None
        pending_position_size = None

        print("📡 Monitoreando log en tiempo real...")
        print("   Presiona Ctrl+C para detener\n")

        try:
            if not os.path.exists(self.log_file):
                print(f"⚠️ Esperando que se cree el archivo {self.log_file}...")
                while not os.path.exists(self.log_file):
                    time.sleep(1)

            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Ir al final del archivo
                f.seek(0, 2)
                self.last_position = f.tell()

                while True:
                    current_position = f.tell()
                    line = f.readline()

                    if not line:
                        # No hay nuevas líneas, esperar
                        time.sleep(0.5)
                        # Verificar si el archivo fue rotado
                        f.seek(0, 2)
                        if f.tell() < current_position:
                            f.seek(0)
                        continue

                    # Procesar la línea
                    line = line.strip()

                    # 1. Detectar señal
                    signal = self.parse_signal_line(line)
                    if signal:
                        pending_signal = signal

                        # Mostrar alerta de señal detectada
                        details = {
                            '🎯 Símbolo': signal['symbol'],
                            '📊 Tipo': signal['signal_type'],
                            '✓ Condiciones': f"{signal['conditions_met']}/{signal['total_conditions']}",
                            '⏰ Tiempo': signal['timestamp']
                        }
                        self.print_alert('SIGNAL_DETECTED', signal['symbol'], details)
                        continue

                    # 2. Detectar tamaño de posición
                    position_size = self.parse_position_size(line)
                    if position_size and pending_signal:
                        pending_position_size = position_size
                        continue

                    # 3. Detectar operación abierta exitosamente
                    trade_opened = self.parse_trade_opened(line)
                    if trade_opened:
                        ticket = trade_opened['ticket']
                        self.open_trades[ticket] = {
                            'signal': pending_signal,
                            'position_size': pending_position_size,
                            'opened_at': datetime.now()
                        }
                        continue

                    # 4. Detectar detalles de orden ejecutada
                    order_details = self.parse_order_executed(line)
                    if order_details:
                        # Encontrar el ticket más reciente para este símbolo
                        matching_ticket = None
                        for ticket, trade_info in self.open_trades.items():
                            if (trade_info['signal'] and
                                trade_info['signal']['symbol'] == order_details['symbol']):
                                matching_ticket = ticket
                                break

                        if matching_ticket:
                            trade_info = self.open_trades[matching_ticket]

                            # Calcular R:R
                            rr_ratio = self.calculate_risk_reward(
                                order_details['entry_price'],
                                order_details['stop_loss'],
                                order_details['take_profit'],
                                order_details['type']
                            )

                            # Calcular distancia SL y TP en pips (para forex, crypto usa puntos)
                            sl_distance = abs(order_details['entry_price'] - order_details['stop_loss'])
                            tp_distance = abs(order_details['take_profit'] - order_details['entry_price'])

                            details = {
                                '🎫 Ticket': matching_ticket,
                                '🎯 Símbolo': order_details['symbol'],
                                '📊 Tipo': order_details['type'],
                                '💰 Entrada': f"${order_details['entry_price']:,.2f}",
                                '🛑 Stop Loss': f"${order_details['stop_loss']:,.2f} (-{sl_distance:,.2f})",
                                '🎯 Take Profit': f"${order_details['take_profit']:,.2f} (+{tp_distance:,.2f})",
                                '📐 R:R Ratio': f"1:{rr_ratio:.2f}",
                                '📦 Lotes': trade_info['position_size']['lots'] if trade_info['position_size'] else 'N/A',
                                '💵 Riesgo': f"${trade_info['position_size']['risk']:.2f}" if trade_info['position_size'] else 'N/A'
                            }

                            self.print_alert('TRADE_OPENED', order_details['symbol'], details)

                            # Limpiar buffers
                            pending_signal = None
                            pending_position_size = None
                        continue

                    # 5. Detectar operación fallida
                    trade_failed = self.parse_trade_failed(line)
                    if trade_failed:
                        details = {
                            '🎯 Símbolo': trade_failed['symbol'],
                            '❌ Razón': trade_failed['reason'],
                            '🔢 Retcode': trade_failed['retcode'] if trade_failed['retcode'] else 'N/A'
                        }

                        # Agregar sugerencia según el error
                        if trade_failed['retcode'] == 10027:
                            details['💡 Solución'] = 'Habilita AutoTrading en MT5 (botón debe estar VERDE)'
                        elif trade_failed['retcode'] == 10019:
                            details['💡 Solución'] = 'Fondos insuficientes en la cuenta'
                        elif trade_failed['retcode'] == 10013:
                            details['💡 Solución'] = 'Solicitud inválida - verifica parámetros'

                        self.print_alert('TRADE_FAILED', trade_failed['symbol'], details)

                        # Limpiar buffers
                        pending_signal = None
                        pending_position_size = None
                        continue

                    # 6. Detectar posición cerrada
                    position_closed = self.parse_position_closed(line)
                    if position_closed:
                        ticket = position_closed['ticket']

                        if ticket in self.open_trades:
                            trade_info = self.open_trades[ticket]
                            symbol = trade_info['signal']['symbol'] if trade_info['signal'] else 'UNKNOWN'

                            # Calcular duración
                            duration = datetime.now() - trade_info['opened_at']
                            minutes = int(duration.total_seconds() / 60)

                            details = {
                                '🎫 Ticket': ticket,
                                '⏱️ Duración': f"{minutes} minutos"
                            }

                            self.print_alert('TRADE_CLOSED', symbol, details)

                            # Remover de trades activos
                            del self.open_trades[ticket]
                        continue

                    # 7. Detectar advertencias de riesgo
                    risk_warning = self.parse_risk_warning(line)
                    if risk_warning:
                        details = {
                            '⚠️ Tipo': risk_warning['type'].replace('_', ' ').title(),
                            '📊 Valor': risk_warning['value'] if risk_warning['value'] else 'N/A'
                        }

                        self.print_alert('RISK_WARNING', 'SISTEMA', details)
                        continue

        except KeyboardInterrupt:
            print("\n\n" + "="*80)
            print("🛑 Monitor detenido por el usuario")
            print("="*80)

            # Mostrar resumen de trades activos
            if self.open_trades:
                print(f"\n📊 Trades activos al detener: {len(self.open_trades)}")
                for ticket, info in self.open_trades.items():
                    symbol = info['signal']['symbol'] if info['signal'] else 'UNKNOWN'
                    print(f"  - Ticket {ticket}: {symbol}")
            else:
                print("\n✅ No hay trades activos")

            print("\n")

        except Exception as e:
            print(f"\n❌ Error en el monitor: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    monitor = TradeMonitor('mt5_bridge_v3.log')
    monitor.monitor()
