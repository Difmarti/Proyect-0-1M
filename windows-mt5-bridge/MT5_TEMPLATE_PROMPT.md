# 📊 Prompt para Crear Plantilla de Indicadores en MT5

Copia y pega este prompt para crear una plantilla visual en MetaTrader 5 que muestre exactamente lo que el bot está analizando.

---

## 🎯 PROMPT PARA MT5 TEMPLATE

```
Necesito crear una plantilla de gráfico (template) en MetaTrader 5 que muestre visualmente todos los indicadores que usa mi bot de trading automatizado.

ESTRATEGIA DEL BOT - CRIPTOMONEDAS (Operaciones Cortas):

INDICADORES PRINCIPALES:
1. RSI (14 períodos)
   - Nivel de sobreventa: 30 (línea horizontal roja)
   - Nivel de sobrecompra: 70 (línea horizontal verde)
   - Configuración: Period=14, Applied Price=Close

2. EMA 9 y EMA 21
   - EMA 9: Color azul, grosor 2
   - EMA 21: Color rojo, grosor 2
   - Propósito: Identificar cruces para dirección

3. MACD (12, 26, 9)
   - Fast EMA: 12
   - Slow EMA: 26
   - Signal: 9
   - Mostrar: Línea MACD, Signal y Histograma
   - Colors: MACD=azul, Signal=rojo, Histogram=verde/rojo

4. Bandas de Bollinger (20, 2)
   - Período: 20
   - Desviación: 2
   - Bandas superior/inferior: Color gris
   - Línea media (SMA): Color amarillo

5. VWAP (Volume Weighted Average Price)
   - Color: Magenta/Púrpura, grosor 2
   - Nota: Si no está disponible por defecto, usar un custom indicator

6. Volumen
   - Mostrar barras de volumen en parte inferior
   - Media móvil de volumen (20 períodos)

TIMEFRAME:
- Principal: 15 minutos (M15)
- Secundario: 5 minutos (M5) y 1 hora (H1)

SÍMBOLOS PARA LA PLANTILLA:
- BTCUSD (Bitcoin)
- ETHUSD (Ethereum)
- LTCUSD (Litecoin)
- XRPUSD (Ripple)

CONDICIONES DE SEÑAL LONG (Compra) - Marcar en el gráfico:
- RSI cruza por debajo de 30 → Flecha verde hacia arriba
- EMA 9 cruza EMA 21 al alza
- MACD histograma positivo
- Precio por encima de VWAP
- Volumen > 20% del promedio

CONDICIONES DE SEÑAL SHORT (Venta) - Marcar en el gráfico:
- RSI cruza por encima de 70 → Flecha roja hacia abajo
- EMA 9 cruza EMA 21 a la baja
- MACD histograma negativo
- Precio por debajo de VWAP
- Volumen > 20% del promedio

DISTRIBUCIÓN DEL GRÁFICO:
- Ventana principal: Precio + EMAs + Bollinger Bands + VWAP
- Ventana inferior 1: RSI con niveles 30 y 70
- Ventana inferior 2: MACD con histograma
- Ventana inferior 3: Volumen con media móvil

COLORES SUGERIDOS (tema oscuro):
- Fondo: Negro o gris oscuro
- Grid: Gris tenue
- Velas: Verde (alcista) / Rojo (bajista)
- EMA 9: Azul brillante
- EMA 21: Rojo brillante
- Bollinger Bands: Gris claro
- VWAP: Magenta/Púrpura
- RSI: Línea amarilla
- MACD Line: Azul
- MACD Signal: Rojo
- MACD Histogram: Verde (positivo) / Rojo (negativo)

INSTRUCCIONES PASO A PASO:
1. Abrir MT5 y seleccionar gráfico de BTCUSD
2. Cambiar timeframe a M15
3. Insertar → Indicadores → Trend → Moving Average (dos veces para EMA 9 y 21)
4. Insertar → Indicadores → Oscillators → RSI
5. Insertar → Indicadores → Oscillators → MACD
6. Insertar → Indicadores → Trend → Bollinger Bands
7. Insertar → Indicadores → Volumes → Volumes
8. Para VWAP: Buscar en Market o Custom Indicators si no está incluido
9. Configurar colores y niveles según especificaciones
10. Guardar template: Plantillas → Guardar Plantilla → "CryptoBot_Strategy"

EXPORTAR TEMPLATE:
- Guardar como: "CryptoBot_Strategy.tpl"
- Ubicación: MT5/templates/
- Aplicar a otros símbolos: Click derecho → Plantillas → CryptoBot_Strategy

Por favor, proporciona instrucciones detalladas sobre cómo:
1. Configurar cada indicador con los parámetros exactos
2. Ajustar los colores para máxima claridad visual
3. Organizar las ventanas para ver todo a la vez
4. Guardar y exportar la plantilla
5. Aplicar la plantilla a múltiples gráficos
6. Añadir alertas visuales cuando se cumplen las condiciones de entrada
```

---

## 📋 Parámetros Específicos para Configuración Manual

### RSI (Relative Strength Index)
```
Period: 14
Applied to: Close
Levels:
  - 70 (Overbought) - Color: Red, Style: Dash
  - 30 (Oversold) - Color: Lime, Style: Dash
Colors:
  - Line: Yellow
Fixed minimum: 0
Fixed maximum: 100
```

### EMA Fast (9)
```
Period: 9
Method: Exponential
Applied to: Close
Style: Color=Blue, Width=2
```

### EMA Slow (21)
```
Period: 21
Method: Exponential
Applied to: Close
Style: Color=Red, Width=2
```

### MACD
```
Fast EMA: 12
Slow EMA: 26
MACD SMA: 9
Applied to: Close
Colors:
  - Main line: DodgerBlue
  - Signal line: Red
  - Histogram: Lime (positive), Red (negative)
```

### Bollinger Bands
```
Period: 20
Deviation: 2
Applied to: Close
Shift: 0
Colors:
  - Upper Band: Gray, Style: Solid
  - Middle Band: Yellow, Style: Dash
  - Lower Band: Gray, Style: Solid
```

### Volume
```
Volume: Tick Volume
Colors:
  - Up Volume: Green
  - Down Volume: Red
Add MA on Volume:
  - Period: 20
  - Color: Orange
```

### VWAP (Si está disponible)
```
Color: Magenta
Width: 2
Style: Solid
```

---

## 🎨 Configuración Visual Recomendada

### Tema de Color (Properties → Colors)
```
Background: Black (0, 0, 0)
Foreground: White (255, 255, 255)
Grid: DarkSlateGray (47, 79, 79)
Chart Up: Lime (0, 255, 0)
Chart Down: Red (255, 0, 0)
Bull Candle: Lime
Bear Candle: Red
Volume Up: LimeGreen
Volume Down: IndianRed
```

### Disposición de Ventanas
```
Main Chart (70% altura):
  - Price + Candles
  - EMA 9 (Blue)
  - EMA 21 (Red)
  - Bollinger Bands (Gray)
  - VWAP (Magenta)

Sub-window 1 (10% altura):
  - RSI with levels 30/70

Sub-window 2 (10% altura):
  - MACD with Histogram

Sub-window 3 (10% altura):
  - Volume with MA
```

---

## 🚀 Atajos de Teclado MT5

```
Ctrl + I    = Abrir lista de indicadores
Ctrl + B    = Ver Objects List
Ctrl + T    = Abrir Terminal
Ctrl + M    = Market Watch
F1          = Cambiar a M1
F5          = Cambiar a M5
F6          = Cambiar a M15
F7          = Cambiar a M30
F8          = Cambiar a H1
F9          = New Order
```

---

## 📁 Ubicación de Archivos de Template

### Windows:
```
C:\Users\[TuUsuario]\AppData\Roaming\MetaQuotes\Terminal\[InstallationID]\templates\
```

### Para encontrar la carpeta:
1. En MT5: File → Open Data Folder
2. Navega a: templates/

---

## ✅ Checklist de Verificación

Después de crear la plantilla, verifica:

- [ ] RSI muestra líneas en 30 y 70
- [ ] EMA 9 (azul) y EMA 21 (roja) visibles
- [ ] MACD muestra histograma en colores
- [ ] Bandas de Bollinger rodean el precio
- [ ] VWAP está visible y actualizado
- [ ] Volumen muestra barras con media móvil
- [ ] Los colores son claros y distinguibles
- [ ] La plantilla se aplicó correctamente a BTCUSD
- [ ] La plantilla funciona en ETHUSD, LTCUSD, XRPUSD
- [ ] Template guardado como "CryptoBot_Strategy.tpl"

---

## 🎯 Ejemplo Visual Esperado

Tu gráfico debe verse así:

```
┌─────────────────────────────────────────────────────────┐
│  BTCUSD M15                                       ▲ ▼    │
│  ╔════════════════════════════════════════════════════╗ │
│  ║  📈 Precio con Velas                                ║ │
│  ║  ──── EMA 9 (Azul rápida)                          ║ │
│  ║  ──── EMA 21 (Roja lenta)                          ║ │
│  ║  ···· Bollinger Superior (Gris)                    ║ │
│  ║  ──── SMA 20 (Amarillo)                            ║ │
│  ║  ···· Bollinger Inferior (Gris)                    ║ │
│  ║  ──── VWAP (Magenta)                               ║ │
│  ╚════════════════════════════════════════════════════╝ │
├─────────────────────────────────────────────────────────┤
│  RSI (14)                                               │
│  ──── 70 (Sobrecompra)                                 │
│  ──── RSI Line (Amarillo)                              │
│  ──── 30 (Sobreventa)                                  │
├─────────────────────────────────────────────────────────┤
│  MACD                                                   │
│  ──── MACD Line (Azul)                                 │
│  ──── Signal (Rojo)                                    │
│  ████ Histograma (Verde/Rojo)                          │
├─────────────────────────────────────────────────────────┤
│  Volume                                                 │
│  ████ Barras de volumen                                │
│  ──── MA 20 (Naranja)                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Tips para Usar la Plantilla

1. **Multi-ventana**: Abre 4 gráficos (BTC, ETH, LTC, XRP) con la plantilla
2. **Sincronización**: Usa Ctrl+Click para sincronizar zoom/scroll
3. **Alertas**: Configura alertas cuando RSI toca 30 o 70
4. **Screenshots**: Guarda capturas cuando veas señales
5. **Comparación**: Compara lo que ves con los logs del bot

---

## 🔄 Actualizar la Plantilla

Si cambias parámetros en el .env:

1. Ajusta los indicadores en MT5
2. Guarda la plantilla (mismo nombre sobrescribe)
3. Reaplica en todos los gráficos: Click derecho → Plantillas → CryptoBot_Strategy

---

**¡Listo!** Con esta plantilla podrás ver exactamente lo que el bot está analizando en tiempo real.
