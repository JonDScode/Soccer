# Roadmap del proyecto

Fases pensadas para que cada una deje un entregable de portafolio por sí sola. El orden va de "datos que ya existen" a "modelos propios" a "tiempo real".

## Fase 0 — Setup + primer contacto con datos reales ✅ (este repo)
- Estructura del proyecto, fuentes documentadas, scripts de ingesta y generador sintético.

## Fase 1 — EDA y visualización (mplsoccer)
- Descargar el Mundial 2022 con `download_statsbomb.py`.
- Notebook: shot maps, pass networks, mapas de calor de presión de un equipo.
- **Entregable**: notebook con 4-5 visualizaciones de nivel publicable.

## Fase 2 — Modelo de xG propio ✅ + xT ✅
- ✅ [notebooks/02_modelo_xg.ipynb](../notebooks/02_modelo_xg.ipynb): logística y gradient boosting entrenados con ~6.500 tiros (2018, Euro 24, femeninos, históricos) y evaluados en el Mundial 2022 sin verlo. Brier 0.082-0.084 vs 0.076 de StatsBomb; correlación 0.81 tiro a tiro. La brecha se explica por sus features de datos 360 (posición del portero y defensores).
- ✅ **xT (expected threat)**: cadena de Markov 16x12 entrenada con 492k pases/conducciones ([src/soccer/xt.py](../src/soccer/xt.py) + [models/xt_grid.json](../models/xt_grid.json)) — alimenta el gráfico de **match momentum** del dashboard, la versión abierta del de las transmisiones del Mundial.

## Fase 3 — Forecasting de resultados
- Con football-data.co.uk (10+ temporadas): modelo de Poisson bivariado / Dixon-Coles, y comparación contra ratings Elo (Club Elo) y contra las cuotas de mercado.
- Backtesting honesto: ¿el modelo bate al mercado de apuestas? (spoiler: casi nunca, y explicar por qué es parte del valor).
- **Entregable**: módulo de forecasting + reporte de backtesting.

## Fase 4 — Scouting: similitud de jugadores
- Stats por-90 de FBref vía `soccerdata`, clustering / PCA / vecinos más cercanos: "dame jugadores parecidos a X pero más baratos" (cruzar con Transfermarkt).
- **Entregable**: app Streamlit de búsqueda de jugadores similares.

## Fase 5 — Pipeline en tiempo real
- Poller de la API de football-data.org (free tier), almacenar en DuckDB, dashboard Streamlit con tabla en vivo y predicciones de la Fase 3 actualizándose.
- **Entregable**: pipeline end-to-end demostrable — esto es lo que más brilla en un portafolio de data engineering + science.

## Fase 6 — Avanzado (elegir uno)
- **VAEP/xT** con `socceraction`: valorar cada acción de un jugador, no solo tiros.
- **Pitch control** con tracking de Metrica Sports (modelo de Spearman, tutorial de Friends of Tracking).
- **xG con datos 360** de StatsBomb: añadir posición de defensores al modelo de la Fase 2.
