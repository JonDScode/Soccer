# ⚽ Soccer Analytics Lab

Proyecto de portafolio para explorar y explotar las posibilidades de la **ciencia de datos aplicada al fútbol**: desde datos de eventos (cada pase, tiro y duelo de un partido) hasta modelos predictivos, scouting de jugadores y pipelines en tiempo real.

## ¿Por qué fútbol + data science?

El fútbol es hoy una de las industrias más activas en analítica deportiva:

- **Clubes** (Liverpool, Brentford, Brighton) construyeron ventajas competitivas reales con equipos de data science: fichajes infravalorados, modelos de xG propios, análisis táctico.
- **Empresas del sector**: StatsBomb/Hudl, Opta (Stats Perform), SkillCorner, Zelus Analytics, Traits Insights — contratan data scientists constantemente.
- **Casas de apuestas y trading deportivo**: modelos de forecasting de resultados son el core del negocio.
- **Medios**: The Athletic, ESPN y similares consumen visualizaciones y métricas avanzadas.

Problemas típicos del dominio (y de este proyecto): modelos de **Expected Goals (xG)**, valoración de acciones (**VAEP**), redes de pases, **forecasting** de resultados (Poisson / Dixon-Coles / Elo), scouting por similitud de jugadores, y **pitch control** con datos de tracking.

## Estructura

```
Soccer/
├── data/
│   ├── raw/          # datos descargados tal cual (no se versionan)
│   ├── processed/    # datos limpios/derivados (no se versionan)
│   └── synthetic/    # datos sintéticos generados (no se versionan)
├── docs/
│   ├── DATA_SOURCES.md   # dónde conseguir datos (histórico + tiempo real)
│   └── ROADMAP.md        # plan por fases del proyecto
├── notebooks/        # exploración y análisis (Jupyter)
├── scripts/
│   ├── download_statsbomb.py   # baja datos de eventos reales (StatsBomb Open Data)
│   └── generate_synthetic.py   # genera una liga sintética coherente (partidos + tiros con xG)
├── src/soccer/       # código reutilizable (paquete Python)
└── requirements.txt
```

## Stack

| Capa | Herramienta | Por qué |
|------|-------------|---------|
| Lenguaje | Python 3.11+ | estándar de facto en sports analytics |
| Datos | pandas / numpy | manipulación tabular |
| Almacenamiento | DuckDB + Parquet | SQL analítico local, sin servidor |
| Acceso a datos fútbol | `statsbombpy`, `soccerdata`, `kloppy` | wrappers de las fuentes públicas |
| Visualización | `mplsoccer` + matplotlib | campos, shot maps, pass networks |
| ML | scikit-learn, XGBoost | xG models, clustering de jugadores |
| App/Dashboard | Streamlit | demo interactiva para el portafolio |

## Quickstart

```powershell
# 1. Entorno virtual (recomendado Python 3.11/3.12 por compatibilidad de librerías)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Datos reales: eventos del Mundial 2022 (StatsBomb Open Data)
python scripts/download_statsbomb.py --sample 5

# 3. O datos sintéticos: una liga completa de 20 equipos con tiros y xG
python scripts/generate_synthetic.py --seasons 3 --seed 42
```

Ver [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) para el catálogo completo de fuentes y [docs/ROADMAP.md](docs/ROADMAP.md) para el plan del proyecto.
