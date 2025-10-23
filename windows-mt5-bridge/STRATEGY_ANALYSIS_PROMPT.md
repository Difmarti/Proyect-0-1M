# 📊 Prompt para Análisis de Estrategia de Trading de Criptomonedas

## 🎯 USO DEL PROMPT

Copia y pega este prompt completo cuando necesites analizar una criptomoneda (BTC, ETH, LTC, XRP) para determinar si existe una oportunidad de trading según nuestra estrategia automatizada.

---

## 📋 PROMPT PARA ANÁLISIS

```
Actúa como un analista de trading experto en criptomonedas. Necesito que analices [SÍMBOLO] (ejemplo: BTCUSD) usando nuestra estrategia de trading automatizada y determines si existe una señal de entrada válida.

═══════════════════════════════════════════════════════════
ESTRATEGIA: TRADING DE CRIPTOMONEDAS - OPERACIONES CORTAS
═══════════════════════════════════════════════════════════

CARACTERÍSTICAS GENERALES:
• Tipo: Scalping / Day Trading
• Duración operaciones: Minutos a horas
• Timeframe principal: 15 minutos (M15)
• Operativa: 24/7 con filtros de horario óptimo
• Activos: BTCUSD, ETHUSD, LTCUSD, XRPUSD

═══════════════════════════════════════════════════════════
INDICADORES TÉCNICOS UTILIZADOS
═══════════════════════════════════════════════════════════

1. RSI (Relative Strength Index) - Período 14
   ├─ Propósito: Identificar condiciones de sobrecompra/sobreventa
   ├─ Nivel de sobreventa: 30 (señal de compra potencial)
   ├─ Nivel de sobrecompra: 70 (señal de venta potencial)
   └─ Fórmula: RSI = 100 - (100 / (1 + RS))
               donde RS = Promedio ganancias / Promedio pérdidas (14 períodos)

2. EMA (Exponential Moving Average) - Dos períodos
   ├─ EMA Rápida: 9 períodos
   ├─ EMA Lenta: 21 períodos
   ├─ Propósito: Determinar dirección de tendencia
   ├─ Cruce alcista: EMA 9 cruza por encima de EMA 21 → Tendencia alcista
   ├─ Cruce bajista: EMA 9 cruza por debajo de EMA 21 → Tendencia bajista
   └─ EMA da más peso a datos recientes que SMA

3. MACD (Moving Average Convergence Divergence)
   ├─ Fast EMA: 12 períodos
   ├─ Slow EMA: 26 períodos
   ├─ Signal Line: 9 períodos (EMA del MACD)
   ├─ Histograma: MACD Line - Signal Line
   ├─ Propósito: Confirmar momentum y fuerza de tendencia
   ├─ Histograma positivo (> 0): Momentum alcista
   ├─ Histograma negativo (< 0): Momentum bajista
   └─ Cruces de MACD con Signal Line indican cambios de momentum

4. Bandas de Bollinger - Período 20, Desviación 2
   ├─ Banda Superior: SMA(20) + 2 * Desviación Estándar
   ├─ Banda Media: SMA(20)
   ├─ Banda Inferior: SMA(20) - 2 * Desviación Estándar
   ├─ Propósito: Medir volatilidad y niveles extremos
   ├─ Precio cerca banda inferior: Potencial sobreventa
   ├─ Precio cerca banda superior: Potencial sobrecompra
   └─ Ancho de bandas indica nivel de volatilidad del mercado

5. VWAP (Volume Weighted Average Price)
   ├─ Fórmula: VWAP = Σ(Precio Típico × Volumen) / Σ(Volumen)
   ├─ Precio Típico = (High + Low + Close) / 3
   ├─ Propósito: Identificar nivel de precio promedio ponderado por volumen
   ├─ Precio > VWAP: Presión compradora, mercado alcista
   ├─ Precio < VWAP: Presión vendedora, mercado bajista
   └─ VWAP es línea de equilibrio entre compradores y vendedores

6. VOLUMEN - Análisis de 20 períodos
   ├─ Volumen Promedio: Media móvil de 20 períodos
   ├─ Multiplicador requerido: 1.2x (120% del promedio)
   ├─ Propósito: Confirmar que hay suficiente liquidez y participación
   └─ Volumen alto valida las señales de entrada

═══════════════════════════════════════════════════════════
REGLAS DE ENTRADA - SEÑAL LONG (COMPRA)
═══════════════════════════════════════════════════════════

TODAS las siguientes condiciones deben cumplirse simultáneamente:

✓ CONDICIÓN 1 - RSI:
  • RSI < 30 (sobreventa)
  • Indica que el activo está infravalorado y puede rebotar
  • Buscar RSI entre 20-30 para mayor probabilidad

✓ CONDICIÓN 2 - EMAs:
  • EMA 9 > EMA 21
  • Confirma que la tendencia de corto plazo es alcista
  • Idealmente, EMA 9 debe estar alejándose al alza de EMA 21

✓ CONDICIÓN 3 - MACD:
  • Histograma MACD > 0
  • Confirma momentum alcista
  • Mejor si histograma está creciendo (barras cada vez más grandes)

✓ CONDICIÓN 4 - VWAP:
  • Precio actual > VWAP
  • Confirma que compradores están dominando
  • Mayor distancia sobre VWAP = mayor fuerza

✓ CONDICIÓN 5 - Volumen:
  • Volumen actual > 120% del promedio de 20 períodos
  • Confirma interés del mercado y validez de la señal
  • Sin volumen alto, la señal NO es válida

✓ CONDICIÓN 6 - Horario:
  • Hora actual NO debe estar en horas a evitar (3:00-6:00 UTC)
  • Horarios óptimos (mayor probabilidad de éxito):
    - 0:00-2:00 UTC (Cierre USA)
    - 7:00-9:00 UTC (Apertura Europa)
    - 8:00-10:00 UTC (Sesión Asia)
    - 13:00-16:00 UTC (Apertura Wall Street)

═══════════════════════════════════════════════════════════
REGLAS DE ENTRADA - SEÑAL SHORT (VENTA)
═══════════════════════════════════════════════════════════

TODAS las siguientes condiciones deben cumplirse simultáneamente:

✓ CONDICIÓN 1 - RSI:
  • RSI > 70 (sobrecompra)
  • Indica que el activo está sobrevalorado y puede corregir
  • Buscar RSI entre 70-80 para mayor probabilidad

✓ CONDICIÓN 2 - EMAs:
  • EMA 9 < EMA 21
  • Confirma que la tendencia de corto plazo es bajista
  • Idealmente, EMA 9 debe estar alejándose a la baja de EMA 21

✓ CONDICIÓN 3 - MACD:
  • Histograma MACD < 0
  • Confirma momentum bajista
  • Mejor si histograma está decreciendo (barras cada vez más grandes en negativo)

✓ CONDICIÓN 4 - VWAP:
  • Precio actual < VWAP
  • Confirma que vendedores están dominando
  • Mayor distancia bajo VWAP = mayor presión vendedora

✓ CONDICIÓN 5 - Volumen:
  • Volumen actual > 120% del promedio de 20 períodos
  • Confirma interés del mercado y validez de la señal
  • Sin volumen alto, la señal NO es válida

✓ CONDICIÓN 6 - Horario:
  • Hora actual NO debe estar en horas a evitar (3:00-6:00 UTC)
  • Mismo rango de horarios óptimos que para señales LONG

═══════════════════════════════════════════════════════════
GESTIÓN DE RIESGO POR OPERACIÓN
═══════════════════════════════════════════════════════════

Stop Loss (SL):
• Porcentaje: 2% del precio de entrada
• Para LONG: SL = Precio entrada × 0.98 (2% por debajo)
• Para SHORT: SL = Precio entrada × 1.02 (2% por encima)
• Objetivo: Limitar pérdidas si el análisis es incorrecto

Take Profit (TP):
• Porcentaje: 3.5% del precio de entrada
• Para LONG: TP = Precio entrada × 1.035 (3.5% por encima)
• Para SHORT: TP = Precio entrada × 0.965 (3.5% por debajo)
• Risk/Reward Ratio: 1:1.75 (por cada $1 arriesgado, ganar $1.75)

Trailing Stop:
• Activación: Cuando la ganancia alcanza +2%
• Distancia: 1% del precio actual
• Se mueve automáticamente siguiendo el precio favorable
• Objetivo: Proteger ganancias mientras el precio se mueve a favor

Tamaño de Posición:
• Máximo por operación: 5% del balance
• Basado en riesgo del 2% de stop loss
• Formula: Tamaño = (Balance × % Riesgo) / (% Stop Loss)

═══════════════════════════════════════════════════════════
LÍMITES GLOBALES DE RIESGO
═══════════════════════════════════════════════════════════

Límite Diario:
• Pérdida máxima diaria: 10% del balance inicial
• Compartido entre Forex y Crypto
• Si se alcanza → Trading detenido hasta el día siguiente
• Alertas progresivas:
  - 5% pérdida: Advertencia amarilla
  - 8% pérdida: Alerta crítica roja
  - 10% pérdida: Stop total automático

Límites de Posiciones:
• Máximo posiciones crypto simultáneas: 3
• Máximo posiciones forex simultáneas: 3
• Máximo posiciones totales: 5
• Objetivo: Diversificar riesgo y evitar sobreexposición

Pérdidas Consecutivas:
• Si 3 pérdidas seguidas → Reducir tamaño posición al 50%
• Objetivo: Proteger capital durante rachas negativas
• Se restaura después de una operación ganadora

═══════════════════════════════════════════════════════════
FACTORES ADICIONALES A CONSIDERAR
═══════════════════════════════════════════════════════════

Contexto de Mercado:
• Verificar si hay noticias importantes pendientes
• Evitar operar durante anuncios de Fed, BCE, grandes eventos cripto
• Considerar el sentiment general del mercado

Confirmaciones Adicionales:
• Velas de precio: Buscar patrones de reversión (martillo, estrella fugaz, envolventes)
• Divergencias: RSI/MACD divergiendo del precio aumenta probabilidad
• Soportes/Resistencias: Entrada cerca de niveles clave aumenta validez

Señales Más Fuertes:
• Todas las condiciones cumplen holgadamente (no apenas)
• RSI extremo: <25 para LONG, >75 para SHORT
• MACD con cruce reciente de signal line
• Volumen muy por encima del promedio (>150%)
• Múltiples timeframes confirman misma dirección

═══════════════════════════════════════════════════════════
TU TAREA DE ANÁLISIS
═══════════════════════════════════════════════════════════

Por favor, analiza [SÍMBOLO] en timeframe de 15 minutos y proporciona:

1. VALORES ACTUALES DE INDICADORES:
   • RSI (14): [valor]
   • EMA 9: [valor]
   • EMA 21: [valor]
   • MACD Line: [valor]
   • Signal Line: [valor]
   • Histograma: [valor]
   • Banda Superior BB: [valor]
   • Banda Media BB: [valor]
   • Banda Inferior BB: [valor]
   • VWAP: [valor]
   • Precio actual: [valor]
   • Volumen actual: [valor]
   • Volumen promedio (20): [valor]
   • Hora actual UTC: [valor]

2. EVALUACIÓN DE CONDICIONES:
   Para cada condición (1-6), indica:
   • ✅ CUMPLE o ❌ NO CUMPLE
   • Explicación breve del por qué

3. CONCLUSIÓN:
   • Señal detectada: LONG / SHORT / NINGUNA
   • Nivel de confianza: ALTO / MEDIO / BAJO
   • Factores que fortalecen la señal
   • Factores que debilitan la señal
   • Riesgos a considerar

4. RECOMENDACIÓN DE ENTRADA (si aplica):
   • Precio de entrada sugerido: $[valor]
   • Stop Loss: $[valor] (-2%)
   • Take Profit: $[valor] (+3.5%)
   • Risk/Reward: 1:[valor]
   • Tamaño de posición sugerido: [% del balance]

5. ANÁLISIS DE CONTEXTO:
   • ¿El precio está en tendencia o rango?
   • ¿Hay soportes/resistencias cercanos?
   • ¿Qué dice el precio en timeframes superiores (1h, 4h)?
   • ¿Hay eventos importantes próximos?

═══════════════════════════════════════════════════════════
FORMATO DE RESPUESTA ESPERADO
═══════════════════════════════════════════════════════════

Proporciona el análisis en formato estructurado y claro, indicando si la estrategia generaría una señal de entrada y con qué nivel de confianza. Si no se cumplen todas las condiciones, explica qué está faltando y qué necesitaría cambiar en el mercado para generar una señal válida.

Sé específico con los números y proporciona razonamiento claro basado en la estrategia descrita.
```

---

## 💡 EJEMPLO DE USO

### Análisis de BTCUSD

**Reemplaza [SÍMBOLO] con:**
```
BTCUSD en timeframe de 15 minutos, usando datos de las últimas 200 velas
```

**El análisis te dirá:**
- ✅ Si existe señal LONG, SHORT o ninguna
- 📊 Valores exactos de todos los indicadores
- 🎯 Niveles de entrada, SL y TP
- ⚠️ Riesgos y consideraciones especiales
- 💪 Nivel de confianza de la señal

---

## 📌 NOTAS IMPORTANTES

### ¿Cuándo usar este prompt?

1. **Antes de abrir una posición manual** - Validar que cumple con la estrategia
2. **Para revisar señales del bot** - Verificar por qué el bot entró o no entró
3. **Para aprender** - Entender qué busca la estrategia en el mercado
4. **Para optimizar** - Identificar patrones de éxito/fracaso

### ¿Qué NO hace este prompt?

- ❌ No predice el futuro con certeza
- ❌ No garantiza ganancias
- ❌ No reemplaza gestión de riesgo
- ❌ No considera eventos de noticias automáticamente

### Adaptación para otros activos

Para analizar **ETHUSD, LTCUSD o XRPUSD**:
- Simplemente cambia [SÍMBOLO] por el activo deseado
- Las reglas son idénticas para todos los activos crypto
- Los porcentajes de SL/TP son los mismos

### Para Forex (si aplica en el futuro)

La estrategia de crypto **NO** es la misma que la de Forex. Si necesitas analizar pares Forex:
- Debes usar una estrategia diferente (no implementada aún)
- Forex usa timeframe M15 pero con indicadores distintos
- Gestión de riesgo es compartida (10% diario total)

---

## 🔄 ACTUALIZACIONES

**Versión:** 1.0
**Fecha:** 2025-10-22
**Compatible con:** mt5_bridge_v2.py
**Módulo de estrategia:** crypto_strategy.py

### Changelog

- **v1.0** (2025-10-22): Versión inicial con estrategia completa de crypto

---

## 📚 DOCUMENTACIÓN RELACIONADA

- **crypto_strategy.py** - Código fuente de la estrategia
- **ENV_CONFIGURATION.md** - Parámetros configurables
- **BRIDGE_V2_README.md** - Guía de uso del bridge
- **MT5_TEMPLATE_PROMPT.md** - Plantilla visual para MT5
- **risk_manager.py** - Sistema de gestión de riesgo

---

**🎯 ¡Usa este prompt para obtener análisis consistentes y alineados con la estrategia automatizada de tu bot!**
