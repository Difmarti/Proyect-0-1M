"""
Script para diagnosticar y resolver problemas de conexión con MT5
"""
import sys
import os
import time
from dotenv import load_dotenv

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

print("=" * 70)
print("SOLUCIONADOR DE PROBLEMAS DE CONEXIÓN MT5")
print("=" * 70)

import MetaTrader5 as mt5

# Lista de métodos para intentar
methods = [
    ("Sin parámetros (auto-detección)", lambda: mt5.initialize()),
    ("Con timeout extendido", lambda: mt5.initialize(timeout=60000)),
    ("Con ruta específica", lambda: mt5.initialize(path=os.getenv('MT5_PATH'))),
    ("Con ruta y timeout", lambda: mt5.initialize(path=os.getenv('MT5_PATH'), timeout=60000)),
]

success = False

for i, (description, method) in enumerate(methods, 1):
    print(f"\n[Intento {i}] {description}...")

    try:
        if method():
            print("   ✓ ¡ÉXITO! MT5 inicializado")

            # Obtener info
            terminal_info = mt5.terminal_info()
            if terminal_info:
                print(f"\n   Terminal conectado:")
                print(f"     - Nombre: {terminal_info.name}")
                print(f"     - Ruta: {terminal_info.path}")
                print(f"     - Build: {terminal_info.build}")
                print(f"     - Conectado: {terminal_info.connected}")
                print(f"     - Algo Trading permitido: {terminal_info.trade_allowed}")

            success = True
            break
        else:
            error = mt5.last_error()
            print(f"   ✗ Falló: {error}")
    except Exception as e:
        print(f"   ✗ Excepción: {e}")

if not success:
    print("\n" + "=" * 70)
    print("NO SE PUDO CONECTAR A MT5")
    print("=" * 70)
    print("\nPROBLEMAS CONOCIDOS Y SOLUCIONES:\n")

    print("1. ERROR IPC TIMEOUT (-10005):")
    print("   - MT5 no está ejecutándose o no responde")
    print("   - Solución: Cierra y abre MT5 (como administrador si es posible)")
    print("   - Asegúrate que MT5 esté completamente cargado antes de ejecutar esto\n")

    print("2. MT5 NO PERMITE CONEXIONES DE API:")
    print("   - Algunos brokers bloquean la API de Python")
    print("   - Solución: Ve a Herramientas → Opciones → Expert Advisors")
    print("   - Marca: 'Permitir trading automatizado' y 'Permitir importación de DLL'\n")

    print("3. VERSIÓN DE MT5 INCOMPATIBLE:")
    print("   - Algunas versiones antiguas no soportan la API de Python")
    print("   - Solución: Actualiza MT5 a la última versión\n")

    print("4. FIREWALL/ANTIVIRUS:")
    print("   - Puede estar bloqueando la comunicación")
    print("   - Solución temporal: Desactiva antivirus y prueba de nuevo\n")

    print("5. SOLUCIÓN ALTERNATIVA:")
    print("   - Si nada funciona, podemos configurar el bridge para que")
    print("   - se ejecute SIN MT5 inicialmente y use solo datos históricos\n")

    sys.exit(1)

# Si llegamos aquí, la conexión fue exitosa
# Intentar hacer login
print("\n" + "=" * 70)
print("PROBANDO LOGIN A LA CUENTA")
print("=" * 70)

account = int(os.getenv('MT5_ACCOUNT'))
password = os.getenv('MT5_PASSWORD')
server = os.getenv('MT5_SERVER')

print(f"\nCuenta: {account}")
print(f"Servidor: {server}")
print("Intentando login...")

authorized = mt5.login(account, password, server)

if authorized:
    print("\n✓ ¡LOGIN EXITOSO!")

    account_info = mt5.account_info()
    if account_info:
        print(f"\nInformación de la cuenta:")
        print(f"  Balance: ${account_info.balance:.2f}")
        print(f"  Equity: ${account_info.equity:.2f}")
        print(f"  Margin: ${account_info.margin:.2f}")
        print(f"  Profit: ${account_info.profit:.2f}")
        print(f"  Moneda: {account_info.currency}")
        print(f"  Apalancamiento: 1:{account_info.leverage}")
else:
    error = mt5.last_error()
    print(f"\n✗ Error en login: {error}")
    print(f"\nPOSIBLES CAUSAS:")
    print("  - Credenciales incorrectas")
    print("  - Servidor incorrecto")
    print("  - Cuenta bloqueada o expirada")
    print("  - MT5 ya está conectado a otra cuenta")

    mt5.shutdown()
    sys.exit(1)

# Verificar símbolos
print("\n" + "=" * 70)
print("VERIFICANDO SÍMBOLOS")
print("=" * 70)

trading_pairs = os.getenv('TRADING_PAIRS', '').split(',')
print(f"\nPares configurados: {', '.join(trading_pairs)}")

available = 0
for pair in trading_pairs:
    pair = pair.strip()
    symbol_info = mt5.symbol_info(pair)
    if symbol_info:
        print(f"  ✓ {pair}: Disponible")
        available += 1
    else:
        print(f"  ✗ {pair}: NO disponible en este broker")

print(f"\nTotal disponibles: {available}/{len(trading_pairs)}")

mt5.shutdown()

print("\n" + "=" * 70)
print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
print("=" * 70)
print("\nEl bridge está listo para ejecutarse.")
print("\nPuedes iniciar el bridge con:")
print("  python mt5_bridge.py")
