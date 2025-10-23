"""
Gestor de Riesgo Integrado
Maneja el límite de pérdida diaria del 10% compartido entre Forex y Crypto
"""

import json
import logging
from datetime import datetime, time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RiskManager:
    """Gestión de riesgo integrada para Forex y Crypto"""

    def __init__(self, redis_client, max_daily_loss_pct=10.0):
        self.redis_client = redis_client
        self.max_daily_loss_pct = max_daily_loss_pct

        # Límites de operaciones
        self.max_forex_positions = 3
        self.max_crypto_positions = 3
        self.max_total_positions = 5

        # Control de pérdidas consecutivas
        self.max_consecutive_losses = 3
        self.position_size_reduction = 0.5  # Reducir al 50%

        # Estado actual
        self.is_trading_stopped = False
        self.position_size_multiplier = 1.0

    def get_daily_stats(self):
        """Obtener estadísticas del día actual"""
        try:
            stats_json = self.redis_client.get('risk:daily_stats')
            if stats_json:
                return json.loads(stats_json)
            else:
                # Inicializar stats del día
                return self._initialize_daily_stats()
        except Exception as e:
            logger.error(f"Error obteniendo stats diarios: {e}")
            return self._initialize_daily_stats()

    def _initialize_daily_stats(self):
        """Inicializar estadísticas diarias"""
        stats = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'initial_balance': 0.0,
            'current_balance': 0.0,
            'total_pnl': 0.0,
            'forex_pnl': 0.0,
            'crypto_pnl': 0.0,
            'loss_pct': 0.0,
            'consecutive_losses': 0,
            'forex_positions': 0,
            'crypto_positions': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        self._save_daily_stats(stats)
        return stats

    def _save_daily_stats(self, stats):
        """Guardar estadísticas diarias en Redis"""
        try:
            self.redis_client.set('risk:daily_stats', json.dumps(stats), ex=86400)  # 24 horas
        except Exception as e:
            logger.error(f"Error guardando stats diarios: {e}")

    def update_initial_balance(self, balance):
        """Actualizar balance inicial del día"""
        stats = self.get_daily_stats()

        # Verificar si es un nuevo día
        if stats['date'] != datetime.now().strftime('%Y-%m-%d'):
            stats = self._initialize_daily_stats()

        stats['initial_balance'] = balance
        stats['current_balance'] = balance
        self._save_daily_stats(stats)

        logger.info(f"Balance inicial del día: ${balance:.2f}")

    def can_open_position(self, asset_type, balance):
        """
        Verificar si se puede abrir una nueva posición

        Args:
            asset_type: 'forex' o 'crypto'
            balance: Balance actual de la cuenta

        Returns:
            (puede_operar, razon)
        """
        stats = self.get_daily_stats()

        # Verificar si es nuevo día
        if stats['date'] != datetime.now().strftime('%Y-%m-%d'):
            self.reset_daily()
            stats = self.get_daily_stats()

        # 1. Verificar si el trading está detenido
        if self.is_trading_stopped:
            return False, "Trading detenido por límite de pérdida diaria"

        # 2. Calcular pérdida actual
        current_loss_pct = self._calculate_loss_percentage(stats, balance)

        # 3. Verificar límite de pérdida diaria
        if current_loss_pct >= self.max_daily_loss_pct:
            self.is_trading_stopped = True
            self._send_alert(
                "⛔ LÍMITE DIARIO ALCANZADO",
                f"Pérdida diaria: {current_loss_pct:.2f}% - Trading detenido hasta mañana"
            )
            return False, f"Límite de pérdida diaria alcanzado: {current_loss_pct:.2f}%"

        # 4. Alertas progresivas
        if current_loss_pct >= 8.0:
            self._send_alert(
                "🔴 ALERTA CRÍTICA",
                f"Pérdida diaria: {current_loss_pct:.2f}% - Último 2% disponible"
            )
        elif current_loss_pct >= 5.0:
            self._send_alert(
                "🟡 PRECAUCIÓN",
                f"Pérdida diaria: {current_loss_pct:.2f}% - {self.max_daily_loss_pct - current_loss_pct:.2f}% restante"
            )

        # 5. Verificar límites de posiciones
        if asset_type == 'forex':
            if stats['forex_positions'] >= self.max_forex_positions:
                return False, f"Máximo de posiciones Forex alcanzado ({self.max_forex_positions})"
        else:  # crypto
            if stats['crypto_positions'] >= self.max_crypto_positions:
                return False, f"Máximo de posiciones Crypto alcanzado ({self.max_crypto_positions})"

        # 6. Verificar límite total de posiciones
        total_positions = stats['forex_positions'] + stats['crypto_positions']
        if total_positions >= self.max_total_positions:
            return False, f"Máximo de posiciones totales alcanzado ({self.max_total_positions})"

        # 7. Verificar pérdidas consecutivas
        if stats['consecutive_losses'] >= self.max_consecutive_losses:
            self.position_size_multiplier = self.position_size_reduction
            logger.warning(
                f"⚠️ {stats['consecutive_losses']} pérdidas consecutivas - "
                f"Reduciendo tamaño de posición al {self.position_size_reduction * 100}%"
            )

        # 8. Verificar volatilidad extrema (implementar más adelante)
        # if self._check_high_volatility():
        #     return False, "Volatilidad extrema detectada"

        return True, "OK"

    def _calculate_loss_percentage(self, stats, current_balance):
        """Calcular porcentaje de pérdida del día"""
        if stats['initial_balance'] == 0:
            stats['initial_balance'] = current_balance
            self._save_daily_stats(stats)
            return 0.0

        loss = stats['initial_balance'] - current_balance
        loss_pct = (loss / stats['initial_balance']) * 100

        # Actualizar stats
        stats['current_balance'] = current_balance
        stats['loss_pct'] = loss_pct
        self._save_daily_stats(stats)

        return max(0, loss_pct)  # No permitir porcentajes negativos

    def register_position_opened(self, asset_type):
        """Registrar que se abrió una posición"""
        stats = self.get_daily_stats()

        if asset_type == 'forex':
            stats['forex_positions'] += 1
        else:  # crypto
            stats['crypto_positions'] += 1

        self._save_daily_stats(stats)
        logger.info(f"Posición {asset_type} abierta. Total: Forex={stats['forex_positions']}, Crypto={stats['crypto_positions']}")

    def register_position_closed(self, asset_type, profit):
        """
        Registrar que se cerró una posición

        Args:
            asset_type: 'forex' o 'crypto'
            profit: Ganancia/pérdida de la operación
        """
        stats = self.get_daily_stats()

        # Actualizar posiciones abiertas
        if asset_type == 'forex':
            stats['forex_positions'] = max(0, stats['forex_positions'] - 1)
            stats['forex_pnl'] += profit
        else:  # crypto
            stats['crypto_positions'] = max(0, stats['crypto_positions'] - 1)
            stats['crypto_pnl'] += profit

        # Actualizar PnL total
        stats['total_pnl'] += profit
        stats['total_trades'] += 1

        # Actualizar contadores de victorias/derrotas
        if profit > 0:
            stats['winning_trades'] += 1
            stats['consecutive_losses'] = 0
            self.position_size_multiplier = 1.0  # Restaurar tamaño normal
        else:
            stats['losing_trades'] += 1
            stats['consecutive_losses'] += 1

        self._save_daily_stats(stats)

        # Log
        result = "ganancia" if profit > 0 else "pérdida"
        logger.info(
            f"Posición {asset_type} cerrada: {result} de ${profit:.2f}. "
            f"PnL total día: ${stats['total_pnl']:.2f}"
        )

    def get_position_size_multiplier(self):
        """Obtener multiplicador de tamaño de posición actual"""
        return self.position_size_multiplier

    def reset_daily(self):
        """Resetear contadores diarios (llamar a las 00:00 UTC)"""
        logger.info("🔄 Reseteando estadísticas diarias...")

        self.is_trading_stopped = False
        self.position_size_multiplier = 1.0

        # Las estadísticas se inicializarán automáticamente en la próxima consulta
        self.redis_client.delete('risk:daily_stats')

        self._send_alert("🌅 NUEVO DÍA DE TRADING", "Límites reseteados. Trading reactivado.")

    def get_daily_report(self):
        """Generar reporte diario"""
        stats = self.get_daily_stats()

        win_rate = (stats['winning_trades'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0

        report = f"""
📊 REPORTE DIARIO - {stats['date']}
═══════════════════════════════════

💰 BALANCE:
   Inicial: ${stats['initial_balance']:.2f}
   Actual: ${stats['current_balance']:.2f}
   P/L Día: ${stats['total_pnl']:.2f} ({stats['loss_pct']:.2f}%)

📈 FOREX:
   Posiciones abiertas: {stats['forex_positions']}
   P/L: ${stats['forex_pnl']:.2f}

🪙 CRYPTO:
   Posiciones abiertas: {stats['crypto_positions']}
   P/L: ${stats['crypto_pnl']:.2f}

📊 OPERACIONES:
   Total: {stats['total_trades']}
   Ganadas: {stats['winning_trades']}
   Perdidas: {stats['losing_trades']}
   Win Rate: {win_rate:.1f}%

⚠️ LÍMITE DIARIO:
   Pérdida máxima: {self.max_daily_loss_pct}% (${stats['initial_balance'] * self.max_daily_loss_pct / 100:.2f})
   Pérdida actual: {stats['loss_pct']:.2f}% (${stats['initial_balance'] - stats['current_balance']:.2f})
   Disponible: {self.max_daily_loss_pct - stats['loss_pct']:.2f}%

🔔 ESTADO:
   Trading: {"DETENIDO ⛔" if self.is_trading_stopped else "ACTIVO ✅"}
   Tamaño posición: {self.position_size_multiplier * 100:.0f}%
   Pérdidas consecutivas: {stats['consecutive_losses']}
"""
        return report

    def _send_alert(self, title, message):
        """Enviar alerta (implementar integración con notificaciones)"""
        logger.warning(f"{title}: {message}")

        # Aquí puedes integrar:
        # - Telegram
        # - Email
        # - SMS
        # - Discord
        # - Webhook

        # Guardar en Redis para que el dashboard la muestre
        try:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message
            }
            self.redis_client.lpush('alerts', json.dumps(alert))
            self.redis_client.ltrim('alerts', 0, 99)  # Mantener últimas 100 alertas
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")
