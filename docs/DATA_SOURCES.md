# Fuentes de datos de fútbol

Catálogo de dónde conseguir datos, ordenado por tipo. Regla general: **empieza con StatsBomb Open Data** (eventos reales, gratis, calidad profesional) y **football-data.co.uk** (resultados históricos masivos); lo sintético es el fallback, no el punto de partida.

## 1. Datos de eventos (event data) — gratis

Cada acción del partido con coordenadas: pases, tiros, duelos, presiones. Es el oro del análisis táctico.

| Fuente | Qué tiene | Cómo acceder |
|--------|-----------|--------------|
| **StatsBomb Open Data** | Mundiales 2018/2022 (M y F), Eurocopas, La Liga completa de la era Messi, temporadas de la FA WSL, finales de Champions. Incluye datos 360 (posición de todos los jugadores en cada evento) para algunas competiciones. | Repo GitHub `statsbomb/open-data` (JSON) o librería `statsbombpy` |
| **Wyscout / Pappalardo dataset** | Todas las 5 grandes ligas europeas 2017-18 + Mundial 2018 + Euro 2016. El dataset abierto de eventos más grande publicado (paper en *Nature Scientific Data*). | Figshare — buscar "Pappalardo soccer-match event dataset" |
| **Metrica Sports sample data** | 3 partidos con eventos **y tracking** (posiciones de los 22 jugadores a 25 fps). Único dataset gratis para pitch control. | Repo GitHub `metrica-sports/sample-data` |
| **SkillCorner Open Data** | 9 partidos de tracking extraído de broadcast (grandes clubes europeos). | Repo GitHub `SkillCorner/opendata` |

## 2. Estadísticas agregadas e históricas — gratis

| Fuente | Qué tiene | Cómo acceder |
|--------|-----------|--------------|
| **football-data.co.uk** | 25+ temporadas de resultados de ~22 ligas europeas en CSV, con cuotas de apuestas históricas (clave para forecasting y backtesting). | Descarga directa de CSVs |
| **FBref** | Stats avanzadas por jugador/equipo/partido (xG, progresión, presiones) de decenas de ligas, proveídas por Opta. | Scraping educado con la librería `soccerdata` (respetar rate limits) |
| **Understat** | xG tiro a tiro de las 6 grandes ligas europeas desde 2014. | Librería `soccerdata` o `understatapi` |
| **Kaggle — European Soccer Database** | 25.000+ partidos, 10.000+ jugadores (atributos de FIFA), 11 ligas, 2008-2016, en SQLite. | Kaggle datasets |
| **Transfermarkt** | Valores de mercado, traspasos, plantillas. | Proyecto GitHub `transfermarkt-datasets` (datos ya extraídos) |
| **Club Elo** | Ratings Elo históricos de todos los clubes europeos, día a día. | API gratuita en `clubelo.com` (CSV por HTTP) |
| **FiveThirtyEight SPI** | Ratings SPI y predicciones históricas de partidos globales (proyecto archivado pero los datos siguen publicados). | Repo GitHub `fivethirtyeight/data` |
| **openfootball** | Fixtures y resultados en texto plano de muchas ligas. | GitHub `openfootball` |

## 3. Tiempo real / en vivo — free tier

| Fuente | Free tier | Qué tiene |
|--------|-----------|-----------|
| **football-data.org** | 10 req/min, ~12 competiciones top | Fixtures, resultados en vivo, tablas, plantillas. La mejor API gratuita para empezar un pipeline "live". |
| **API-Football (api-sports.io)** | 100 req/día | Cobertura enorme (1.100+ ligas), eventos en vivo, cuotas. |
| **TheSportsDB** | Gratuita con key pública | Resultados, calendarios, metadatos de equipos. |
| SofaScore / FotMob | No oficial | Datos ricos pero vía scraping no documentado — útil para aprender, frágil para producción. |

Nota Colombia/Latam: API-Football cubre la Liga BetPlay y la Libertadores en su free tier; football-data.org es más limitada fuera de Europa.

## 4. Datos sintéticos (cuando no alcanza lo público)

Casos donde generarlos tiene sentido: simular temporadas completas para backtesting de modelos de forecasting, probar pipelines de streaming sin depender de una API, o generar volumen para práctica de ingeniería de datos.

El script [`scripts/generate_synthetic.py`](../scripts/generate_synthetic.py) genera una liga coherente: equipos con fuerzas de ataque/defensa latentes, calendario de ida y vuelta, tiros con coordenadas y xG calculado con un modelo logístico de distancia/ángulo, y resultados muestreados de esos xG — de modo que las métricas derivadas (tabla, goles esperados vs reales) se comportan como las reales.

## 5. Librerías Python del ecosistema

- `statsbombpy` — cliente oficial de StatsBomb Open Data
- `soccerdata` — scraper unificado de FBref, Understat, WhoScored, etc.
- `kloppy` — normaliza eventos/tracking de distintos proveedores a un modelo común
- `mplsoccer` — visualización: campos, shot maps, radares, pass networks
- `socceraction` — implementación de VAEP y xT (valoración de acciones)

## Recursos para aprender el dominio

- *Soccermatics* (David Sumpter) — libro + curso gratuito "Mathematical Modelling of Football" (Uppsala) con código
- Friends of Tracking (YouTube) — tutoriales de pitch control y tracking data con código real
- StatsBomb / Opta blogs — estado del arte en métricas
