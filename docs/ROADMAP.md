# Roadmap del proyecto

Fases pensadas para que cada una deje un entregable de portafolio por sí sola. El orden va de "datos que ya existen" a "modelos propios" a "tiempo real".

## Fase 0 — Setup + primer contacto con datos reales ✅ (este repo)
- Estructura del proyecto, fuentes documentadas, scripts de ingesta y generador sintético.

## Fase 1 — EDA y visualización (mplsoccer)
- Descargar el Mundial 2022 con `download_statsbomb.py`.
- Notebook: shot maps, pass networks, mapas de calor de presión de un equipo.
- **Entregable**: notebook con 4-5 visualizaciones de nivel publicable.

## Fase 2 — Modelo de xG propio
- Con los tiros de StatsBomb (o Understat), entrenar un modelo de probabilidad de gol: regresión logística (baseline) → XGBoost (distancia, ángulo, parte del cuerpo, tipo de jugada).
- Comparar contra el xG oficial de StatsBomb (calibración, Brier score).
- **Entregable**: notebook + módulo `src/soccer/xg.py` + writeup de qué features importan.

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
