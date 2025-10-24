"""
Dashboard de Trading en Consola
Muestra estadísticas en tiempo real del bridge
"""

import time
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import redis
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error: Falta instalar dependencias: {e}")
    print("Ejecuta: pip install psycopg2-binary redis python-dotenv")
    sys.exit(1)

load_dotenv()

class TradingDashboard:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'trading_db'),
            'user': os.getenv('POSTGRES_USER', 'trading_user'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }

        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
            self.redis_client.ping()
        except:
            pass

    def get_db_connection(self):
        """Obtiene conexión a PostgreSQL"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            return None

    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_account_metrics(self):
        """Obtiene métricas de cuenta más recientes"""
        conn = self.get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT balance, equity, margin, free_margin, margin_level, profit
                    FROM account_metrics
                    ORDER BY time DESC
                    LIMIT 1
                """)
                return cur.fetchone()
        except Exception as e:
            print(f"Error obteniendo métricas: {e}")
            return None
        finally:
            conn.close()

    def get_active_trades(self):
        """Obtiene trades activos"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ticket, symbol, type, volume, open_price,
                           current_price, profit, open_time
                    FROM active_trades
                    ORDER BY open_time DESC
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo trades activos: {e}")
            return []
        finally:
            conn.close()

    def get_today_stats(self):
        """Obtiene estadísticas del día"""
        conn = self.get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                    WHERE close_time >= CURRENT_DATE
                """)
                return cur.fetchone()
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return None
        finally:
            conn.close()

    def get_performance_by_symbol(self):
        """Obtiene rendimiento por símbolo"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        symbol,
                        COUNT(*) as trades,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(profit) as total_profit,
                        AVG(profit) as avg_profit
                    FROM trade_history
                    WHERE close_time >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY symbol
                    ORDER BY total_profit DESC
                    LIMIT 10
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo rendimiento por símbolo: {e}")
            return []
        finally:
            conn.close()

    def format_currency(self, value):
        """Formatea valor como moneda"""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"

    def format_percent(self, value):
        """Formatea valor como porcentaje"""
        if value is None:
            return "0.00%"
        return f"{value:.2f}%"

    def get_color_for_profit(self, profit):
        """Retorna código de color según ganancia/pérdida"""
        if profit > 0:
            return "\033[92m"  # Verde
        elif profit < 0:
            return "\033[91m"  # Rojo
        else:
            return "\033[0m"   # Normal

    def print_header(self):
        """Imprime encabezado del dashboard"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("╔" + "="*78 + "╗")
        print("║" + " "*20 + "🤖 TRADING BOT DASHBOARD - BRIDGE V3" + " "*21 + "║")
        print("║" + f" {now}".center(78) + "║")
        print("╚" + "="*78 + "╝")

    def print_account_section(self, metrics):
        """Imprime sección de cuenta"""
        print("\n┌─ 💰 CUENTA ────────────────────────────────────────────────────────────────┐")

        if metrics:
            balance = metrics.get('balance', 0)
            equity = metrics.get('equity', 0)
            profit = metrics.get('profit', 0)
            margin = metrics.get('margin', 0)
            free_margin = metrics.get('free_margin', 0)
            margin_level = metrics.get('margin_level', 0)

            profit_color = self.get_color_for_profit(profit)
            reset = "\033[0m"

            print(f"│ Balance:      {self.format_currency(balance):<20} │ Margen:       {self.format_currency(margin):<20} │")
            print(f"│ Equity:       {self.format_currency(equity):<20} │ Margen Libre: {self.format_currency(free_margin):<20} │")
            print(f"│ {profit_color}Profit:       {self.format_currency(profit):<20}{reset} │ Margen Nivel: {self.format_percent(margin_level):<20} │")
        else:
            print("│ " + "⚠️  No hay datos de cuenta disponibles".center(76) + " │")

        print("└────────────────────────────────────────────────────────────────────────────┘")

    def print_active_trades_section(self, trades):
        """Imprime sección de trades activos"""
        print("\n┌─ 📊 TRADES ACTIVOS ────────────────────────────────────────────────────────┐")

        if trades:
            print("│ Ticket    │ Símbolo   │ Tipo  │ Lotes │ Entrada    │ Actual     │ Profit     │")
            print("├───────────┼───────────┼───────┼───────┼────────────┼────────────┼────────────┤")

            reset = "\033[0m"

            for trade in trades[:5]:  # Mostrar máximo 5
                ticket = str(trade['ticket'])[:9]
                symbol = trade['symbol'][:9]
                trade_type = trade['type'][:5]
                volume = f"{trade['volume']:.2f}"
                open_price = f"{trade['open_price']:.2f}"
                current_price = f"{trade.get('current_price', 0):.2f}"
                profit = trade.get('profit', 0)

                profit_color = self.get_color_for_profit(profit)
                profit_str = f"{profit_color}{self.format_currency(profit):<11}{reset}"

                print(f"│ {ticket:<9} │ {symbol:<9} │ {trade_type:<5} │ {volume:<5} │ {open_price:<10} │ {current_price:<10} │ {profit_str} │")

            if len(trades) > 5:
                print(f"│ ... y {len(trades) - 5} trades más" + " "*56 + "│")
        else:
            print("│ " + "✅ No hay trades activos".center(76) + " │")

        print("└────────────────────────────────────────────────────────────────────────────┘")

    def print_today_stats_section(self, stats):
        """Imprime estadísticas del día"""
        print("\n┌─ 📈 ESTADÍSTICAS HOY ──────────────────────────────────────────────────────┐")

        if stats and stats.get('total_trades', 0) > 0:
            total = stats['total_trades']
            wins = stats.get('wins', 0) or 0
            losses = stats.get('losses', 0) or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            total_profit = stats.get('total_profit', 0) or 0
            avg_profit = stats.get('avg_profit', 0) or 0
            max_profit = stats.get('max_profit', 0) or 0
            min_profit = stats.get('min_profit', 0) or 0

            profit_color = self.get_color_for_profit(total_profit)
            reset = "\033[0m"

            print(f"│ Trades:       {total:<10} │ Ganadas:      {wins:<10} │ Perdidas:     {losses:<10} │")
            print(f"│ Win Rate:     {self.format_percent(win_rate):<10} │ {profit_color}Profit Total: {self.format_currency(total_profit):<10}{reset} │")
            print(f"│ Avg Profit:   {self.format_currency(avg_profit):<10} │ Max Profit:   {self.format_currency(max_profit):<10} │ Min Profit:   {self.format_currency(min_profit):<10} │")
        else:
            print("│ " + "📊 No hay trades cerrados hoy".center(76) + " │")

        print("└────────────────────────────────────────────────────────────────────────────┘")

    def print_performance_section(self, performance):
        """Imprime rendimiento por símbolo"""
        print("\n┌─ 🎯 RENDIMIENTO POR SÍMBOLO (7 días) ─────────────────────────────────────┐")

        if performance:
            print("│ Símbolo   │ Trades │ Ganadas │ Win Rate │ Profit Total │ Avg Profit   │")
            print("├───────────┼────────┼─────────┼──────────┼──────────────┼──────────────┤")

            reset = "\033[0m"

            for perf in performance[:5]:  # Top 5
                symbol = perf['symbol'][:9]
                trades = perf['trades']
                wins = perf.get('wins', 0) or 0
                win_rate = (wins / trades * 100) if trades > 0 else 0
                total_profit = perf.get('total_profit', 0) or 0
                avg_profit = perf.get('avg_profit', 0) or 0

                profit_color = self.get_color_for_profit(total_profit)

                print(f"│ {symbol:<9} │ {trades:<6} │ {wins:<7} │ {self.format_percent(win_rate):<8} │ {profit_color}{self.format_currency(total_profit):<13}{reset} │ {self.format_currency(avg_profit):<12} │")
        else:
            print("│ " + "📊 No hay datos de rendimiento disponibles".center(76) + " │")

        print("└────────────────────────────────────────────────────────────────────────────┘")

    def print_footer(self):
        """Imprime pie de página"""
        print("\n" + "─"*80)
        print("⟳ Actualizando cada 5 segundos... Presiona Ctrl+C para salir")
        print("─"*80)

    def run(self):
        """Ejecuta el dashboard"""
        print("\n🚀 Iniciando dashboard...")

        # Verificar conexión
        conn = self.get_db_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos")
            print("Verifica que el servidor PostgreSQL esté corriendo y los datos en .env sean correctos")
            return
        conn.close()

        print("✅ Conectado a la base de datos")
        time.sleep(2)

        try:
            while True:
                self.clear_screen()

                # Obtener datos
                metrics = self.get_account_metrics()
                active_trades = self.get_active_trades()
                today_stats = self.get_today_stats()
                performance = self.get_performance_by_symbol()

                # Renderizar dashboard
                self.print_header()
                self.print_account_section(metrics)
                self.print_active_trades_section(active_trades)
                self.print_today_stats_section(today_stats)
                self.print_performance_section(performance)
                self.print_footer()

                # Esperar 5 segundos
                time.sleep(5)

        except KeyboardInterrupt:
            print("\n\n" + "="*80)
            print("🛑 Dashboard detenido por el usuario")
            print("="*80 + "\n")

        except Exception as e:
            print(f"\n❌ Error en el dashboard: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    dashboard = TradingDashboard()
    dashboard.run()
