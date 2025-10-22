"""
Test simple de MT5 para diagnosticar problemas
"""
import sys
import os
from dotenv import load_dotenv

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

print("=" * 60)
print("DIAGNÓSTICO DE METATRADER 5")
print("=" * 60)

# Verificar instalación de librería
print("\n1. Verificando librería MetaTrader5...")
try:
    import MetaTrader5 as mt5
    print(f"   ✓ Librería importada correctamente")
    print(f"   Versión: {mt5.__version__}")
except ImportError as e:
    print(f"   ✗ Error importando: {e}")
    sys.exit(1)

# Verificar ruta del terminal
print("\n2. Verificando ruta del terminal...")
mt5_path = os.getenv('MT5_PATH')
if mt5_path:
    print(f"   Ruta configurada: {mt5_path}")
    if os.path.exists(mt5_path):
        print(f"   ✓ Archivo encontrado")
    else:
        print(f"   ✗ Archivo NO encontrado")
else:
    print(f"   Sin ruta configurada (usando auto-detección)")

# Intentar inicializar MT5
print("\n3. Intentando inicializar MT5...")
print("   Nota: MT5 debe estar abierto y ejecutándose")

try:
    # Intentar inicializar sin ruta
    print("\n   Intento 1: Inicialización sin ruta específica...")
    if mt5.initialize():
        print(f"   ✓ Inicializado exitosamente!")

        # Información del terminal
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"\n   Información del terminal:")
            print(f"     - Nombre: {terminal_info.name}")
            print(f"     - Compañía: {terminal_info.company}")
            print(f"     - Ruta: {terminal_info.path}")
            print(f"     - Build: {terminal_info.build}")
            print(f"     - Conectado: {terminal_info.connected}")
            print(f"     - Algo Trading: {terminal_info.trade_allowed}")

        mt5.shutdown()
    else:
        error = mt5.last_error()
        print(f"   ✗ Error: {error}")

        # Si falla sin ruta, intentar con ruta
        if mt5_path and os.path.exists(mt5_path):
            print(f"\n   Intento 2: Inicialización con ruta específica...")
            if mt5.initialize(path=mt5_path):
                print(f"   ✓ Inicializado exitosamente con ruta!")

                terminal_info = mt5.terminal_info()
                if terminal_info:
                    print(f"\n   Información del terminal:")
                    print(f"     - Nombre: {terminal_info.name}")
                    print(f"     - Ruta: {terminal_info.path}")
                    print(f"     - Conectado: {terminal_info.connected}")

                mt5.shutdown()
            else:
                error = mt5.last_error()
                print(f"   ✗ Error con ruta: {error}")
                print(f"\n   SOLUCIONES POSIBLES:")
                print(f"   1. Asegúrate que MT5 esté ABIERTO y ejecutándose")
                print(f"   2. Ve a Herramientas → Opciones → Expert Advisors")
                print(f"   3. Activa: 'Permitir trading automatizado' y 'Permitir importación de DLL'")
                print(f"   4. Cierra MT5 completamente y ábrelo de nuevo")
                print(f"   5. Ejecuta este script como Administrador")
                sys.exit(1)

except Exception as e:
    print(f"   ✗ Excepción: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ MT5 está listo para usar")
print("=" * 60)
