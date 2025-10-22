# MT5 Windows Bridge

Python bridge que se ejecuta en Windows con MetaTrader 5 instalado y sincroniza datos con el servidor Linux.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    WINDOWS MACHINE                          │
│                                                             │
│  ┌──────────────┐         ┌─────────────────────────┐     │
│  │ MetaTrader 5 │ ◄────── │   mt5_bridge.py         │     │
│  │  (Terminal)  │         │   (Este script)         │     │
│  └──────────────┘         └───────────┬─────────────┘     │
│                                        │                    │
└────────────────────────────────────────┼────────────────────┘
                                         │
                                         │ Network
                                         │ (TCP/IP)
                                         │
┌────────────────────────────────────────┼────────────────────┐
│                    LINUX SERVER        │                    │
│                                        ▼                    │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │  PostgreSQL      │◄─────│  Port 5432       │           │
│  │  (TimescaleDB)   │      └──────────────────┘           │
│  └──────────────────┘                                      │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │  Redis Cache     │◄─────│  Port 6379       │           │
│  └──────────────────┘      └──────────────────┘           │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │  API (FastAPI)   │      │  Port 8080       │           │
│  └──────────────────┘      └──────────────────┘           │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │  Dashboard       │      │  Port 8501       │           │
│  └──────────────────┘      └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Requisitos

### En Windows
- Python 3.11 o superior
- MetaTrader 5 instalado y ejecutándose
- Conexión de red al servidor Linux

### En Linux (ya configurado)
- PostgreSQL/TimescaleDB corriendo en puerto 5432
- Redis corriendo en puerto 6379
- Firewall configurado para permitir conexiones desde Windows

## Instalación en Windows

### 1. Instalar Python

Descarga e instala Python 3.11+ desde https://www.python.org/downloads/

**Importante**: Durante la instalación, marca la opción "Add Python to PATH"

### 2. Clonar o copiar este directorio

Copia la carpeta `windows-mt5-bridge` a tu máquina Windows.

### 3. Instalar dependencias

Abre PowerShell o CMD en la carpeta del bridge y ejecuta:

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia `.env.example` a `.env`:

```powershell
copy .env.example .env
```

Edita `.env` con tus valores:
- **MT5_ACCOUNT**: Tu número de cuenta MT5
- **MT5_PASSWORD**: Tu contraseña MT5
- **MT5_SERVER**: Servidor de tu broker (ej: "Tickmill-Demo")
- **POSTGRES_HOST**: IP de tu servidor Linux (ej: "192.168.1.100")
- **POSTGRES_PASSWORD**: Password de PostgreSQL (ver .env en servidor Linux)
- **REDIS_HOST**: IP de tu servidor Linux

### 5. Configurar firewall en Linux

En tu servidor Linux, permite conexiones desde Windows:

```bash
# Permitir PostgreSQL desde IP de Windows
sudo ufw allow from 192.168.1.XXX to any port 5432

# Permitir Redis desde IP de Windows
sudo ufw allow from 192.168.1.XXX to any port 6379
```

Reemplaza `192.168.1.XXX` con la IP de tu máquina Windows.

## Uso

### Ejecutar el bridge

```powershell
python mt5_bridge.py
```

El script hará lo siguiente:

1. **Conexión a MT5**: Se conecta a tu MT5 local
2. **Login**: Inicia sesión con tus credenciales (si se proporcionan)
3. **Sincronización inicial**:
   - Fetch de precio de los pares configurados
   - Sincronización de métricas de cuenta
   - Sincronización de trades activos
   - Historial de trades (últimos 90 días)
4. **Sincronización periódica**:
   - Precios: Cada 1 minuto
   - Métricas: Cada 1 minuto
   - Trades: Cada 30 segundos

### Ejecutar como servicio de Windows

Para que el bridge se ejecute automáticamente al iniciar Windows:

#### Opción 1: Usar NSSM (recomendado)

1. Descarga NSSM: https://nssm.cc/download
2. Abre PowerShell como Administrador:

```powershell
cd C:\path\to\nssm\win64
.\nssm.exe install MT5Bridge "C:\Python311\python.exe" "C:\path\to\mt5_bridge.py"
.\nssm.exe set MT5Bridge AppDirectory "C:\path\to\windows-mt5-bridge"
.\nssm.exe start MT5Bridge
```

#### Opción 2: Usar Task Scheduler

1. Abre Task Scheduler
2. Crear tarea básica > Nombre: "MT5 Bridge"
3. Trigger: Al iniciar el sistema
4. Acción: Iniciar programa
   - Programa: `C:\Python311\python.exe`
   - Argumentos: `C:\path\to\mt5_bridge.py`
   - Directorio: `C:\path\to\windows-mt5-bridge`

## Logs

Los logs se guardan en `mt5_bridge.log` en el mismo directorio del script.

Para ver los logs en tiempo real:

```powershell
Get-Content mt5_bridge.log -Wait -Tail 50
```

## Funcionalidades

### 1. Sincronización de Precios
- Obtiene barras OHLCV de MT5
- Las almacena en TimescaleDB
- Configurables por par y timeframe

### 2. Métricas de Cuenta
- Balance
- Equity
- Margin usado/libre
- Profit actual
- Se almacena en DB y Redis para acceso rápido

### 3. Trades Activos
- Sincroniza posiciones abiertas
- Actualiza precio actual y profit en tiempo real
- Marca como cerradas las que ya no existen en MT5

### 4. Historial de Trades
- Sincroniza deals históricos
- Útil para análisis de rendimiento
- Se ejecuta en inicio y luego periódicamente

## Troubleshooting

### Error: "Failed to initialize MT5"

- Asegúrate de que MT5 esté instalado y ejecutándose
- Verifica que el path a terminal64.exe sea correcto
- Prueba ejecutar Python como Administrador

### Error: "Failed to connect to database"

- Verifica que la IP del servidor Linux sea correcta
- Comprueba que el firewall permita la conexión
- Test de conectividad: `Test-NetConnection -ComputerName 192.168.1.100 -Port 5432`

### Error: "MT5 login failed"

- Verifica credenciales (Account, Password, Server)
- Asegúrate de que MT5 esté conectado a internet
- Verifica que la cuenta no esté ya conectada en otro terminal

### No se sincronizan datos

- Revisa los logs en `mt5_bridge.log`
- Verifica que los pares en `TRADING_PAIRS` existan en tu broker
- Comprueba que MT5 tenga cotizaciones activas

## Seguridad

⚠️ **Importante**:

- **NO** subas el archivo `.env` a Git (contiene credenciales)
- Usa conexión VPN si el servidor está en internet público
- Considera usar PostgreSQL con SSL
- Cambia las contraseñas por defecto de la base de datos

## Mejoras Futuras

- [ ] Reconexión automática en caso de pérdida de conexión
- [ ] Notificaciones por email/telegram en caso de errores
- [ ] Dashboard local en Windows para monitorear el bridge
- [ ] Compresión de datos para reducir tráfico de red
- [ ] Soporte para múltiples cuentas MT5

## Soporte

Para reportar problemas o sugerencias, revisa los logs y contacta al administrador del sistema.
