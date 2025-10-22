# Trading Bot System Architecture

## Overview

Este es un sistema de trading automatizado con arquitectura distribuida que separa los componentes Linux (backend/dashboard) de la conexión MT5 que corre en Windows.

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        WINDOWS MACHINE                          │
│  (Donde corre MetaTrader 5)                                     │
│                                                                  │
│  ┌────────────────┐         ┌────────────────────────────┐     │
│  │ MetaTrader 5   │ ◄─────  │  windows-mt5-bridge/       │     │
│  │  Terminal      │  API    │  mt5_bridge.py             │     │
│  │                │         │                            │     │
│  │  - Live prices │         │  - Fetch prices from MT5   │     │
│  │  - Trades      │         │  - Sync trades             │     │
│  │  - Account     │         │  - Sync account metrics    │     │
│  └────────────────┘         └──────────┬─────────────────┘     │
│                                         │                        │
└─────────────────────────────────────────┼────────────────────────┘
                                          │
                                          │ TCP/IP Network
                                          │ (PostgreSQL: 5432)
                                          │ (Redis: 6379)
                                          │
┌─────────────────────────────────────────┼────────────────────────┐
│                     LINUX SERVER        │                        │
│                                         ▼                        │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Data Layer                              │       │
│  │                                                       │       │
│  │  ┌─────────────────────┐  ┌─────────────────────┐   │       │
│  │  │ TimescaleDB         │  │ Redis Cache         │   │       │
│  │  │ (PostgreSQL)        │  │                     │   │       │
│  │  │                     │  │ - Account metrics   │   │       │
│  │  │ - price_data        │  │ - Quick lookups     │   │       │
│  │  │ - active_trades     │  │                     │   │       │
│  │  │ - trade_history     │  │                     │   │       │
│  │  │ - account_metrics   │  │                     │   │       │
│  │  │ - trading_signals   │  │                     │   │       │
│  │  └─────────────────────┘  └─────────────────────┘   │       │
│  └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │                                       │
│  ┌───────────────────────┴──────────────────────────────┐       │
│  │              API Layer                               │       │
│  │                                                       │       │
│  │  ┌─────────────────────────────────────────────┐    │       │
│  │  │  FastAPI (trading_api)                      │    │       │
│  │  │  Port: 8080                                 │    │       │
│  │  │                                             │    │       │
│  │  │  Endpoints:                                 │    │       │
│  │  │  - GET /health                              │    │       │
│  │  │  - GET /metrics                             │    │       │
│  │  │  - GET /trades/open                         │    │       │
│  │  │  - GET /trades/history                      │    │       │
│  │  │  - GET /performance/by_pair                 │    │       │
│  │  │  - GET /equity/curve                        │    │       │
│  │  └─────────────────────────────────────────────┘    │       │
│  └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │                                       │
│  ┌───────────────────────┴──────────────────────────────┐       │
│  │          Presentation Layer                          │       │
│  │                                                       │       │
│  │  ┌─────────────────────────────────────────────┐    │       │
│  │  │  Streamlit Dashboard (trading_dashboard)    │    │       │
│  │  │  Port: 8501                                 │    │       │
│  │  │                                             │    │       │
│  │  │  - Real-time account metrics                │    │       │
│  │  │  - Active trades table                      │    │       │
│  │  │  - Equity curve chart                       │    │       │
│  │  │  - Performance by currency pair             │    │       │
│  │  │  - Trading hours heatmap                    │    │       │
│  │  │                                             │    │       │
│  │  │  Auto-refresh: Every 5 seconds              │    │       │
│  │  └─────────────────────────────────────────────┘    │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Componentes

### Windows Machine

#### MT5 Windows Bridge (`windows-mt5-bridge/`)
**Lenguaje**: Python 3.11+
**Ubicación**: Máquina Windows con MT5 instalado
**Función**: Puente entre MT5 y el servidor Linux

**Responsabilidades**:
- Conectarse al terminal MT5 local usando la librería MetaTrader5
- Fetch de precios OHLCV cada 1 minuto
- Sincronización de métricas de cuenta cada 1 minuto
- Sincronización de trades activos cada 30 segundos
- Sincronización de historial de trades
- Escritura directa a PostgreSQL y Redis en el servidor Linux

**Comunicación**:
- MT5 → Script Python (via MetaTrader5 library)
- Script Python → PostgreSQL (TCP puerto 5432)
- Script Python → Redis (TCP puerto 6379)

### Linux Server (Docker Compose)

#### 1. TimescaleDB (`timescaledb`)
**Imagen**: `timescale/timescaledb:latest-pg15`
**Puerto**: 5432
**Función**: Base de datos de series temporales para almacenar datos de trading

**Tablas principales**:
- `price_data` (hypertable): Datos OHLCV particionados por tiempo
- `active_trades`: Posiciones actualmente abiertas
- `trade_history`: Trades cerrados con P/L
- `trading_signals` (hypertable): Señales y decisiones del bot
- `account_metrics` (hypertable): Snapshots de balance, equity, margin

**Funciones**:
- `calculate_drawdown()`: Calcula drawdown actual
- `update_account_metrics()`: Inserta snapshot de cuenta

#### 2. Redis (`redis`)
**Imagen**: `redis:7-alpine`
**Puerto**: 6379
**Función**: Cache de alta velocidad y message queue

**Uso**:
- Cache de métricas de cuenta para acceso rápido
- Session storage
- Rate limiting
- Pub/sub para eventos en tiempo real

#### 3. FastAPI (`api`)
**Base**: `python:3.11-slim`
**Puerto**: 8080
**Función**: REST API para consultar datos de trading

**Endpoints principales**:
```
GET /health              - Health check
GET /metrics             - Métricas actuales de cuenta
GET /trades/open         - Trades abiertos
GET /trades/history      - Historial de trades
GET /performance/by_pair - Performance por par
GET /equity/curve        - Datos de curva de equity
```

**Documentación**: http://localhost:8080/docs (Swagger UI)

#### 4. Streamlit Dashboard (`dashboard`)
**Base**: `python:3.11-slim`
**Puerto**: 8501
**Función**: Dashboard web interactivo en tiempo real

**Features**:
- Auto-refresh cada 5 segundos
- Métricas de cuenta en tiempo real
- Tabla de trades activos
- Gráfico de curva de equity
- Análisis de performance por par
- Heatmap de horas de trading

**Acceso**: http://localhost:8501

## Flujo de Datos

### 1. Sincronización de Precios (cada 1 minuto)
```
MT5 → mt5_bridge.py → TimescaleDB (price_data table)
```

### 2. Sincronización de Cuenta (cada 1 minuto)
```
MT5 → mt5_bridge.py → TimescaleDB (account_metrics table)
                    → Redis (account:metrics hash)
```

### 3. Sincronización de Trades (cada 30 segundos)
```
MT5 → mt5_bridge.py → TimescaleDB (active_trades table)
```

### 4. Visualización de Datos
```
Dashboard → API → TimescaleDB/Redis → Response → Dashboard render
```

## Configuración de Red

### Firewall en Linux Server

Permitir conexiones desde la IP de Windows:

```bash
# PostgreSQL
sudo ufw allow from <WINDOWS_IP> to any port 5432

# Redis
sudo ufw allow from <WINDOWS_IP> to any port 6379

# Dashboard (acceso web)
sudo ufw allow 8501/tcp

# API (acceso web)
sudo ufw allow 8080/tcp
```

### Puertos Expuestos

| Servicio     | Puerto | Descripción                    |
|-------------|--------|--------------------------------|
| TimescaleDB | 5432   | PostgreSQL database            |
| Redis       | 6379   | Cache y message queue          |
| API         | 8080   | REST API (Swagger: /docs)      |
| Dashboard   | 8501   | Web UI (Streamlit)             |

## Instalación y Deployment

### Linux Server

1. **Iniciar servicios**:
```bash
cd /path/to/project
./install.sh
```

2. **Verificar servicios**:
```bash
docker ps
docker logs trading_api
docker logs trading_dashboard
```

3. **Acceder a servicios**:
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8080/docs

### Windows Machine

1. **Instalar Python 3.11+**

2. **Copiar directorio `windows-mt5-bridge/`**

3. **Instalar dependencias**:
```powershell
cd windows-mt5-bridge
pip install -r requirements.txt
```

4. **Configurar `.env`**:
```
MT5_ACCOUNT=12345678
MT5_PASSWORD=password
MT5_SERVER=Tickmill-Demo
POSTGRES_HOST=192.168.1.100  # IP del servidor Linux
POSTGRES_PASSWORD=<from Linux .env>
REDIS_HOST=192.168.1.100
```

5. **Ejecutar bridge**:
```powershell
python mt5_bridge.py
```

6. **(Opcional) Instalar como servicio Windows** con NSSM o Task Scheduler

## Monitoreo y Logs

### Linux (Docker containers)

```bash
# Ver todos los contenedores
docker ps

# Logs en tiempo real
docker logs -f trading_api
docker logs -f trading_dashboard

# Ver health status
docker inspect trading_api | grep -A 5 Health
```

### Windows (MT5 Bridge)

```powershell
# Ver logs en tiempo real
Get-Content mt5_bridge.log -Wait -Tail 50

# Ver últimas 100 líneas
Get-Content mt5_bridge.log -Tail 100
```

## Troubleshooting

### Dashboard muestra error 500

**Causa**: API no puede conectar a TimescaleDB

**Solución**:
```bash
docker logs trading_api
docker exec trading_timescaledb pg_isready -U trading_user
```

### MT5 Bridge no puede conectar

**Causa**: Firewall bloqueando puertos o credenciales incorrectas

**Solución**:
```bash
# En Linux, verificar firewall
sudo ufw status

# Test desde Windows
Test-NetConnection -ComputerName <LINUX_IP> -Port 5432
Test-NetConnection -ComputerName <LINUX_IP> -Port 6379
```

### No se sincronizan datos

**Causa**: MT5 Bridge no está corriendo o tiene errores

**Solución**:
- Verificar que `mt5_bridge.py` esté corriendo
- Revisar `mt5_bridge.log` para errores
- Verificar que MT5 esté abierto y conectado

## Seguridad

### Recomendaciones

1. **Firewall**: Solo permitir IP específica de Windows
2. **VPN**: Usar VPN si el servidor está en internet público
3. **SSL/TLS**: Configurar PostgreSQL con SSL
4. **Passwords**: Cambiar passwords por defecto
5. **Secrets**: NO subir `.env` a Git

### Archivo .gitignore

```
.env
*.log
__pycache__/
*.pyc
windows-mt5-bridge/.env
```

## Escalabilidad

### Múltiples cuentas MT5

Para ejecutar múltiples cuentas:

1. Crear múltiples instancias del bridge en Windows
2. Cada una con su propio `.env`
3. Todas apuntan al mismo PostgreSQL/Redis
4. Usar `account_id` en las tablas para distinguir

### Alta disponibilidad

- TimescaleDB: Configurar réplica
- Redis: Configurar Redis Sentinel
- API/Dashboard: Escalar horizontalmente con load balancer

## Backups

```bash
# Backup de base de datos
./backup.sh

# Restaurar
./restore.sh backups/full_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Referencias

- [TimescaleDB Docs](https://docs.timescale.com/)
- [MetaTrader5 Python Docs](https://www.mql5.com/en/docs/python_metatrader5)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
