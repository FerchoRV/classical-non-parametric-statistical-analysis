# Sistema de Análisis Estadístico

Aplicación de escritorio genérica con interfaz gráfica moderna (customtkinter)
para el análisis de datos de encuestas y mediciones, basada en **estadística no
paramétrica** y **estadística descriptiva**. Funciona con cualquier conjunto de
datos (Excel, CSV, TXT o JSON), no está atado a un estudio en particular.

Se justifica el uso de pruebas no paramétricas porque las variables son de
escala **ordinal** (Likert 1–5) y **dicotómica** (1 = Sí / 0 = No), que violan
los supuestos de normalidad y de escala de intervalo/razón requeridos por las
pruebas paramétricas. Las inferencias se basan en **rangos y medianas**, no en
medias aritméticas (Corder & Foreman, 2014; Sullivan & Artino, 2013; Field, 2024).

## Requisitos

- Python 3.10+
- Windows / macOS / Linux con entorno gráfico

## Instalación

El entorno virtual ya está creado en `.venv`. Para reinstalar desde cero:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ejecución

```bash
.venv\Scripts\python.exe main.py
```

## Estructura del proyecto

```
main.py                      Punto de entrada principal (conexión a documentos)
requirements.txt             Dependencias del proyecto
<sus_datos>.xlsx|.csv|.txt|.json  Datos a analizar (cualquier archivo de entrada)
results/                     Resultados exportados (Excel)
graphics/                    Gráficos exportados (PNG)
src/
  config.py                  Rutas, constantes y tema visual
  core/
    data_loader.py           Carga de Excel, CSV, TXT y JSON (pandas)
    nonparametric.py         Spearman, Mann-Whitney, Kruskal-Wallis y Fisher;
                             tamaños de efecto y p-valores exactos (scipy)
    descriptive.py           Media, mediana, moda y otros descriptivos
    plotting.py              Gráficos de barras, cajas, dispersión y circular
                             (matplotlib/seaborn)
    exporter.py              Exportación de resultados a Excel
  gui/
    app.py                   Ventana principal y navegación
    home_view.py             Pantalla inicial: carga de documento + módulos
    nonparametric_view.py    Módulo de pruebas no paramétricas
    descriptive_view.py      Módulo descriptivo y de gráficos
    widgets.py               Tabla de datos reutilizable
    state.py                 Estado compartido (DataFrame cargado)
```

## Uso

### 1. Pantalla inicial
Pulse **Cargar documento** para abrir un archivo de Excel, CSV, TXT o JSON. Tras
cargarlo se habilitan los botones **Pruebas No Paramétricas** y **Estadística
Descriptiva**, y se muestra una vista previa de los datos.

### 2. Pruebas no paramétricas
Cuatro pruebas seleccionables, todas permiten elegir las columnas a analizar:

1. **Correlación de Spearman — Ordinal vs Continua:** asociación entre una
   variable ordinal (ej. percepción 1–5) y una continua (ej. *accuracy*
   acumulado de los logs).
2. **Correlación de Spearman — Ordinal vs Ordinal:** asociación entre dos
   variables ordinales (ej. precisión vs intuitividad). A mayor valoración en
   una, mayor en la otra (Field, 2018).
3. **Análisis por grupos — Ordinal vs Nominal:** compara las medianas de una
   variable ordinal entre las categorías de una variable **nominal** definida
   por el usuario. Es **flexible** según el número de categorías:
   - **2 categorías** → Prueba **U de Mann-Whitney** + correlación rango-biserial.
   - **3 o más categorías** → Prueba **H de Kruskal-Wallis** + épsilon cuadrado.
4. **Asociación categórica — Nominal vs Nominal (Fisher):** evalúa la asociación
   entre dos variables categóricas/nominales. En vez de chi-cuadrado (poco
   fiable con frecuencias esperadas < 5, habitual en muestras pequeñas) usa
   pruebas **exactas**:
   - **Tabla 2×2** → Prueba **exacta de Fisher**.
   - **Tabla r×c (3+ categorías)** → Prueba **exacta de Monte Carlo**
     (Fisher-Freeman-Halton con márgenes fijos).
   - Tamaño del efecto: **V de Cramér**.

**P-valores exactos (muestras pequeñas):** en las tres pruebas de rangos
(Spearman y análisis por grupos) hay una casilla opcional **"Usar p-valor exacto
(permutaciones)"**. Al activarla se calcula, además del p asintótico, un p-valor
exacto por permutaciones y la decisión se basa en él. Es recomendable con n
pequeño o grupos desbalanceados, donde la aproximación asintótica es imprecisa.
La prueba categórica ya es exacta por diseño, por lo que no requiere esta opción.
La casilla se muestra solo en las pruebas de rangos y se oculta en la categórica.

**Lectura de los resultados.** Cada prueba reporta dos números distintos que no
deben confundirse:
- El **coeficiente / tamaño del efecto** (ρ de Spearman, rango-biserial,
  épsilon cuadrado o V de Cramér) mide la **fuerza** de la relación.
- El **valor p** mide la **significancia** (qué tan improbable es que el
  resultado se deba al azar): un valor p pequeño (p < α) indica evidencia
  fuerte, no una correlación débil.

Cada resultado incluye un resumen, un detalle (descriptivos por grupo o tabla de
contingencia), una **interpretación técnica** y una **conclusión simple** en
lenguaje directo (ej. "SÍ existe correlación...").

Los datos se ven durante toda la prueba y el resultado se **previsualiza** antes
de guardarlo. Se exporta a **Excel** en `results/` con el nombre indicado (hojas:
Resumen, Detalle e Interpretación, esta última con la interpretación técnica y la
conclusión simple). Tras guardar, la selección y la previsualización se
**limpian automáticamente**.

### 3. Estadística descriptiva y gráficos
- Marque las columnas a analizar. **Calcular descriptivos** obtiene media,
  mediana y moda (y desviación, mínimo y máximo) de las columnas **numéricas**.
- Gráficos disponibles:
  - **Barras:** una columna de texto/object **o numérica** (frecuencias).
  - **Cajas:** una o más columnas numéricas.
  - **Dispersión:** exactamente dos columnas numéricas.
  - **Circular:** una columna de texto/object o numérica; calcula y muestra el
    **porcentaje** (y la frecuencia) de cada categoría en su porción del círculo.
  - **Barra apilada (cantidad, ordinal por grupo):** muestra la **tendencia** de
    una variable ordinal (1–5) según una columna de agrupación (texto o
    numérica). El eje vertical es la **cantidad de respuestas**, por lo que las
    barras tienen distinto tamaño según el número de personas de cada grupo.
    Cada segmento se anota con su **porcentaje sobre el total** y el conteo. La
    leyenda no lleva título.
  - **Mapa de calor (ordinal por grupo):** misma relación en forma de matriz
    (filas = grupo, columnas = nivel 1–5); el color refleja el **porcentaje
    sobre el total** y cada celda muestra ese porcentaje y el conteo.
  - Para estos dos últimos se eligen dos columnas con selectores dedicados:
    la **columna de agrupación** y la **columna ordinal** (numérica).
- Personalice título, etiquetas de ejes X/Y, cuadrícula y leyenda. El gráfico se
  **previsualiza** y se guarda como **PNG** en `graphics/`. Tras guardar
  (descriptivos o gráfico), la selección y la previsualización se **limpian
  automáticamente**.

## Referencias

- Corder, G. W., & Foreman, D. I. (2014). *Nonparametric Statistics: A Step-by-Step Approach.*
- Field, A. (2024). *Discovering Statistics Using IBM SPSS Statistics.*
- Sullivan, G. M., & Artino, A. R. (2013). Analyzing and Interpreting Data From Likert-Type Scales.
