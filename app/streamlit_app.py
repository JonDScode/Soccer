"""Soccer Analytics Lab — dashboard bilingüe (ES/EN).

Cuatro vistas:
1. Partido a fondo  — event data del Mundial 2022 (StatsBomb): shot map, carrera de xG,
   redes de pases, posesión y análisis por jugador
2. Torneo 2022      — agregados: mapa de equipos por xG, goleadores vs xG
3. Mundial 2026     — resultados y goleadores en vivo vía football-data.org (API key gratuita)
4. Metodología      — de dónde salen los datos, qué es el xG y cómo replicar lo que se ve en TV

Ejecutar:  streamlit run app/streamlit_app.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from soccer import metrics, statsbomb, viz  # noqa: E402
from soccer.flags import flag  # noqa: E402


def _load_dotenv() -> None:
    """Carga ROOT/.env (KEY=VALUE por línea) sin dependencias externas."""
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

st.set_page_config(page_title="Soccer Analytics Lab",
                   page_icon=":material/sports_soccer:", layout="wide")

BLUE, ORANGE, INK, MUTED = viz.COLOR_A, viz.COLOR_B, "#212529", "#6c757d"
PLOTLY_LAYOUT = dict(
    template="plotly_white", font=dict(color=INK), margin=dict(l=40, r=20, t=50, b=40),
    hovermode="x unified",
)

# ---------- Textos ES / EN ----------

STR = {
    "es": {
        "tabs": [":material/trophy: Torneo",
                 ":material/query_stats: Partido a fondo",
                 ":material/menu_book: Metodología"],
        "competition": "Torneo / Liga", "season": "Temporada",
        "live_wc": "FIFA World Cup · en vivo",
        "live_cap": "Datos en vivo del torneo en curso (resultados, tablas y goleadores — sin event data todavía)",
        "groups": "Fase de grupos", "bracket": "Fase eliminatoria", "group": "Grupo",
        "col_team": "Equipo", "col_pj": "PJ", "col_dg": "DG", "col_pts": "Pts",
        "stages": {"LAST_32": "Dieciseisavos", "LAST_16": "Octavos",
                   "QUARTER_FINALS": "Cuartos", "SEMI_FINALS": "Semifinales",
                   "THIRD_PLACE": "3er puesto", "FINAL": "Final"},
        "stages_sb": {"Round of 32": "Dieciseisavos", "Round of 16": "Octavos",
                      "Quarter-finals": "Cuartos", "Semi-finals": "Semifinales",
                      "3rd Place Final": "3er puesto", "Final": "Final",
                      "Second Group Stage": "2ª fase de grupos", "Play-offs": "Repechaje",
                      "Group Stage": "Fase de grupos",
                      "group stage": "Fase de grupos", "first group stage": "1ª fase de grupos",
                      "second group stage": "2ª fase de grupos", "first round": "1ª ronda",
                      "second round": "2ª ronda", "final round": "Ronda final",
                      "round of 16": "Octavos", "quarter-finals": "Cuartos",
                      "semi-finals": "Semifinales", "third-place match": "3er puesto",
                      "final": "Final"},
        "results_only": "Este torneo tiene resultados completos pero sin event data público — "
                        "el análisis de xG, redes y jugadores no está disponible.",
        "no_event_2026": "El event data tiro a tiro del Mundial 2026 aún no es público — "
                         "StatsBomb suele liberarlo meses después de la final. Cuando salga, "
                         "esta pestaña tendrá el análisis completo (xG, redes de pases, "
                         "jugador a jugador) igual que los demás torneos. Por ahora, "
                         "resultados y calendario:",
        "sel_cap": "{n} partidos con event data de StatsBomb",
        "add_more": "Agregar más torneos o ligas",
        "add_more_body": "StatsBomb Open Data tiene más competiciones (Mundiales, Euros, "
                         "La Liga de la era Messi, Mundial femenino...). Para sumar una:\n"
                         "```\npython scripts/download_statsbomb.py --list\n"
                         "python scripts/download_statsbomb.py --competition <id> --season <id>\n"
                         "python scripts/preprocess_statsbomb.py\n```\n"
                         "Al recargar, aparece en los selectores.",
        "no_data": "No hay event data descargado para esta selección.",
        "match": "Partido", "shots": "Tiros", "stage": "Fase",
        "pens_note": "El partido se definió por penales; la tanda se excluye de tiros y xG.",
        "race_title": "Carrera de xG (los puntos son goles)",
        "minute": "Minuto", "cum_xg": "xG acumulado", "goal": "Gol",
        "shot_map": "Shot map",
        "shot_map_cap": "{a} (amarillo) ataca a la derecha · área del punto = xG del tiro · goles rellenos",
        "networks": "Redes de pases", "possession": "Posesión",
        "flow_title": "Flujo de posesión por tramos de 5 min (azul = domina {a})",
        "flow_pct": "% de posesión",
        "flow_cap": "Posesión aproximada por proporción de pases en cada ventana — el proxy "
                    "estándar con event data. Las líneas punteadas marcan los goles.",
        "player_sec": "Análisis por jugador", "player": "Jugador",
        "m_passes": "Pases", "m_pass_pct": "% pase", "m_key": "Pases clave", "m_shots": "Tiros",
        "m_goals": "Goles", "m_carries": "Conducciones", "m_dribbles": "Regates",
        "m_press": "Presiones", "m_recov": "Recuperaciones", "m_assists": "Asistencias",
        "m_actions": "Acciones",
        "involvement": "Participación por tramos de 5 min", "actions_y": "Acciones",
        "map_title": "Mapa del torneo: producción vs concesión de peligro (por 90 min)",
        "xg_for": "xG a favor por 90'", "xg_against": "xG en contra por 90'",
        "map_cap": "Arriba-derecha = genera mucho y concede poco. Tamaño del punto = partidos jugados.",
        "scorers_title": "Goleadores (3+): goles reales vs esperados", "goals_lbl": "Goles",
        "scorers_cap": "Goles muy por encima del xG = definición excepcional (o suerte); "
                       "por debajo = mala puntería o mala fortuna.",
        "wc_intro": "Datos del **Mundial 2026 en curso** vía [football-data.org](https://www.football-data.org/) "
                    "(free tier, registro gratuito sin tarjeta). Pega tu API key o expórtala como `FOOTBALL_DATA_TOKEN`.",
        "api_key": "API key",
        "no_key": "Sin API key no puedo consultar la API. El registro gratuito toma un minuto: "
                  "https://www.football-data.org/client/register",
        "api_err": "La API respondió {c}: revisa la key o el rate limit (10 req/min).",
        "no_matches": "La API no devolvió partidos del Mundial 2026.",
        "results": "Últimos resultados ({n} jugados)", "upcoming": "Próximos partidos",
        "date": "fecha", "home": "local", "away": "visitante", "stage_col": "fase",
        "top_scorers_26": "Goleadores del Mundial 2026",
        "scorers_fail": "No pude cargar los goleadores (posible rate limit — espera un minuto).",
        "viz_tr": {"goal": "gol", "miss": "fallo", "completed": "Completado", "failed": "Fallado",
                   "touches_of": "Toques de", "passes_of": "Pases de", "actions": "acciones",
                   "attacks_right": "ataca a la derecha",
                   "until_sub": "hasta la primera sustitución (min {m})"},
    },
    "en": {
        "tabs": [":material/trophy: Tournament",
                 ":material/query_stats: Match deep dive",
                 ":material/menu_book: Methodology"],
        "competition": "Tournament / League", "season": "Season",
        "live_wc": "FIFA World Cup · live",
        "live_cap": "Live data from the ongoing tournament (results, tables and scorers — no event data yet)",
        "groups": "Group stage", "bracket": "Knockout bracket", "group": "Group",
        "col_team": "Team", "col_pj": "P", "col_dg": "GD", "col_pts": "Pts",
        "stages": {"LAST_32": "Round of 32", "LAST_16": "Round of 16",
                   "QUARTER_FINALS": "Quarter-finals", "SEMI_FINALS": "Semi-finals",
                   "THIRD_PLACE": "Third place", "FINAL": "Final"},
        "stages_sb": {"group stage": "Group stage", "first group stage": "First group stage",
                      "second group stage": "Second group stage", "first round": "First round",
                      "second round": "Second round", "final round": "Final round",
                      "round of 16": "Round of 16", "quarter-finals": "Quarter-finals",
                      "semi-finals": "Semi-finals", "third-place match": "Third place",
                      "final": "Final"},
        "results_only": "This tournament has complete results but no public event data — "
                        "xG, network and player analysis is not available.",
        "no_event_2026": "Shot-by-shot event data for the 2026 World Cup is not public yet — "
                         "StatsBomb usually releases it months after the final. Once it lands, "
                         "this tab will offer the full deep dive (xG, pass networks, "
                         "player analysis) like the other tournaments. For now, "
                         "results and fixtures:",
        "sel_cap": "{n} matches with StatsBomb event data",
        "add_more": "Add more tournaments or leagues",
        "add_more_body": "StatsBomb Open Data has more competitions (World Cups, Euros, "
                         "Messi-era La Liga, Women's World Cup...). To add one:\n"
                         "```\npython scripts/download_statsbomb.py --list\n"
                         "python scripts/download_statsbomb.py --competition <id> --season <id>\n"
                         "python scripts/preprocess_statsbomb.py\n```\n"
                         "Reload and it shows up in the selectors.",
        "no_data": "No event data downloaded for this selection.",
        "match": "Match", "shots": "Shots", "stage": "Stage",
        "pens_note": "Decided on penalties; the shootout is excluded from shots and xG.",
        "race_title": "xG race (dots are goals)",
        "minute": "Minute", "cum_xg": "Cumulative xG", "goal": "Goal",
        "shot_map": "Shot map",
        "shot_map_cap": "{a} (yellow) attacks right · dot area = shot xG · goals are filled",
        "networks": "Pass networks", "possession": "Possession",
        "flow_title": "Possession flow in 5-min windows (blue = {a} dominates)",
        "flow_pct": "% possession",
        "flow_cap": "Possession approximated by pass share per window — the standard proxy "
                    "with event data. Dotted lines mark goals.",
        "player_sec": "Player analysis", "player": "Player",
        "m_passes": "Passes", "m_pass_pct": "Pass %", "m_key": "Key passes", "m_shots": "Shots",
        "m_goals": "Goals", "m_carries": "Carries", "m_dribbles": "Dribbles",
        "m_press": "Pressures", "m_recov": "Recoveries", "m_assists": "Assists",
        "m_actions": "Actions",
        "involvement": "Involvement per 5-min window", "actions_y": "Actions",
        "map_title": "Tournament map: danger created vs conceded (per 90 min)",
        "xg_for": "xG for per 90'", "xg_against": "xG against per 90'",
        "map_cap": "Top-right = creates a lot, concedes little. Dot size = matches played.",
        "scorers_title": "Top scorers (3+): actual vs expected goals", "goals_lbl": "Goals",
        "scorers_cap": "Goals well above xG = exceptional finishing (or luck); "
                       "below = poor finishing or bad luck.",
        "wc_intro": "Data from the **ongoing 2026 World Cup** via [football-data.org](https://www.football-data.org/) "
                    "(free tier, free signup, no card). Paste your API key or export it as `FOOTBALL_DATA_TOKEN`.",
        "api_key": "API key",
        "no_key": "I need an API key to query the API. Free signup takes a minute: "
                  "https://www.football-data.org/client/register",
        "api_err": "API returned {c}: check your key or the rate limit (10 req/min).",
        "no_matches": "The API returned no 2026 World Cup matches.",
        "results": "Latest results ({n} played)", "upcoming": "Upcoming matches",
        "date": "date", "home": "home", "away": "away", "stage_col": "stage",
        "top_scorers_26": "2026 World Cup top scorers",
        "scorers_fail": "Could not load scorers (possible rate limit — wait a minute).",
        "viz_tr": {"goal": "goal", "miss": "miss", "completed": "Completed", "failed": "Failed",
                   "touches_of": "Touches by", "passes_of": "Passes by", "actions": "actions",
                   "attacks_right": "attacks right",
                   "until_sub": "until first substitution (min {m})"},
    },
}

METODOLOGIA_ES = """
## ¿De dónde salen los datos de fútbol?

| Tipo de dato | Cómo se produce | Quién lo hace |
|---|---|---|
| **Event data** (pases, tiros, duelos con coordenadas) | Codificadores humanos viendo el video con software de tagging: 2.000-3.500 eventos por partido, cada vez más asistido por IA | Opta (Stats Perform), StatsBomb/Hudl |
| **Tracking data** (posición de los 22 + balón, 25 veces/seg) | Sistemas multicámara en el estadio, o visión por computador sobre la señal de TV | TRACAB, Second Spectrum, SkillCorner |
| **Datos físicos** (distancias, sprints, cargas) | Chalecos GPS de 10 Hz con acelerómetro | Catapult, STATSports, WIMU |

Este dashboard usa **event data abierto de StatsBomb** (Mundial 2022 completo, tiro a tiro) y la **API gratuita de football-data.org** para el Mundial 2026.

## ¿Qué es el xG y cómo funciona?

El **xG (expected goals, goles esperados)** es la probabilidad —entre 0 y 1— de que un tiro concreto termine en gol, estimada **antes de saber el resultado del tiro**.

**Cómo se construye:** se toman cientos de miles de tiros históricos y se entrena un modelo de clasificación (regresión logística o gradient boosting) que aprende qué proporción de tiros similares terminó en gol. Las variables típicas:

- **Distancia** al arco y **ángulo** visible entre los postes (las dos que más pesan)
- Parte del cuerpo (pie vs cabeza), tipo de jugada (juego abierto, contragolpe, balón parado, penal)
- Tipo de asistencia previa (centro, pase raso, balón dividido)
- En modelos avanzados: presión del defensor y posición del portero (requiere datos 360/tracking)

**Valores de referencia:** un penal ≈ 0.78 (históricamente se convierte el 78%) · mano a mano en el área chica ≈ 0.3-0.6 · tiro desde fuera del área ≈ 0.03-0.06. El xG medio de *todos* los tiros ronda 0.10: solo 1 de cada 10 tiros es gol.

**Cómo se lee:**
- **Por partido**: sumar el xG de cada equipo dice quién generó más peligro real, más allá del marcador (un 1-0 con xG 0.4 - 2.1 fue un robo). Es la base de la "carrera de xG" de la pestaña 1.
- **Por jugador**: comparar goles reales vs xG acumulado separa a los definidores de élite de los que tuvieron suerte. Mbappé 2022: 8 goles con 4.2 xG = definición excepcional.
- **Por qué importa**: el xG es más **repetible** que los goles — predice el rendimiento futuro mejor que los goles pasados, por eso los clubes fichan con xG y no con goles.

**Limitaciones honestas:** no sabe quién patea (el modelo básico le da el mismo xG a Messi que a un defensa central), la suma por partido ignora que los tiros no son independientes, y modelos de distintos proveedores dan números distintos (no compares xG de Opta con xG de StatsBomb).

**En este proyecto:** usamos el xG oficial de StatsBomb (incluido en su event data), y el generador sintético (`scripts/generate_synthetic.py`) implementa un mini-modelo logístico de distancia y ángulo — el esqueleto de cualquier modelo de xG real. La Fase 2 del roadmap es entrenar el nuestro y compararlo.

## Lo que ves en la TV del Mundial 2026 vs lo que replicamos aquí

| Análisis en TV | Dato que lo alimenta en 2026 | Aquí |
|---|---|---|
| Posesión oficial | Tracking óptico de FIFA (tiempo real de control del balón) | Proporción de pases por ventana de 5 min — correlaciona >0.95 |
| xG y carrera de xG | Modelos sobre millones de tiros (Opta/StatsBomb) | xG oficial de StatsBomb (event data abierto) |
| Mapas de toques/pases por jugador | Event data | Idéntico |
| Redes de pases y formaciones | Event data + alineaciones | Idéntico |
| Distancias, velocidades, sprints | Tracking óptico + GPS | **Requiere tracking** — muestras gratis: Metrica, SkillCorner |
| Rupturas de línea, presión, espacios | FIFA Football Intelligence sobre tracking con esqueleto | Fase avanzada: pitch control con sample de Metrica |

**Regla general:** si el análisis es *dónde ocurrió una acción con balón* → event data (lo tenemos). Si es *dónde estaban los otros 21* o *cuánto corrió alguien* → tracking (solo muestras abiertas).

## ¿Dónde ver stats públicas del Mundial 2026 y la API es gratis?

- **Sitios públicos con stats del 2026** (sin registro): [FBref](https://fbref.com/en/comps/1/World-Cup-Stats) (stats básicas), FOX Sports (xG por equipo), xGscore y FootyStats (xG por partido), FotMob y SofaScore (apps, muy completas).
- **La API de football-data.org es gratuita**: registro en 1 minuto, sin tarjeta, key por email. El free tier (10 req/min) incluye el Mundial: resultados, calendario, tablas y goleadores. Lo que NO incluye gratis: minuto a minuto en vivo y estadísticas finas (son add-ons de pago). Alternativa gratuita: API-Football (100 req/día).
- **Event data tiro a tiro del 2026**: aún no es público. StatsBomb suele liberar los Mundiales meses después de la final — cuando pase, este dashboard lo absorbe cambiando dos IDs (`competition_id`/`season_id`).
"""

METODOLOGIA_EN = """
## Where does football data come from?

| Data type | How it is produced | Who makes it |
|---|---|---|
| **Event data** (passes, shots, duels with coordinates) | Human coders tagging video: 2,000-3,500 events per match, increasingly AI-assisted | Opta (Stats Perform), StatsBomb/Hudl |
| **Tracking data** (all 22 players + ball, 25 fps) | Multi-camera stadium systems, or computer vision on the broadcast feed | TRACAB, Second Spectrum, SkillCorner |
| **Physical data** (distances, sprints, load) | 10 Hz GPS vests with accelerometer | Catapult, STATSports, WIMU |

This dashboard uses **StatsBomb open event data** (full 2022 World Cup, shot by shot) and the **free football-data.org API** for the 2026 World Cup.

## What is xG and how does it work?

**xG (expected goals)** is the probability — between 0 and 1 — that a given shot ends up as a goal, estimated **before knowing the outcome**.

**How it is built:** take hundreds of thousands of historical shots and train a classification model (logistic regression or gradient boosting) that learns what share of similar shots were scored. Typical features:

- **Distance** to goal and visible **angle** between the posts (the two heaviest)
- Body part (foot vs header), play pattern (open play, counter, set piece, penalty)
- Assist type (cross, through ball, loose ball)
- Advanced models: defender pressure and goalkeeper position (needs 360/tracking data)

**Reference values:** a penalty ≈ 0.78 (78% historical conversion) · one-on-one in the six-yard box ≈ 0.3-0.6 · shot from outside the box ≈ 0.03-0.06. The average shot is worth ≈ 0.10: only 1 in 10 shots scores.

**How to read it:**
- **Per match**: summing each team's xG tells you who created real danger regardless of the score (a 1-0 with xG 0.4 - 2.1 was a heist). This powers the xG race in tab 1.
- **Per player**: actual goals vs cumulative xG separates elite finishers from lucky ones. Mbappé 2022: 8 goals on 4.2 xG = exceptional finishing.
- **Why it matters**: xG is more **repeatable** than goals — it predicts future output better than past goals do, which is why clubs scout on xG.

**Honest limitations:** it does not know who is shooting (a basic model gives Messi and a centre-back the same xG), summing per match ignores that shots are not independent, and different providers' models disagree (never compare Opta xG with StatsBomb xG).

**In this project:** we use StatsBomb's official xG (included in their event data), and the synthetic generator (`scripts/generate_synthetic.py`) implements a mini logistic model of distance and angle — the skeleton of any real xG model. Roadmap Phase 2 is training our own and benchmarking it.

## What you see on 2026 World Cup TV vs what we replicate here

| TV analysis | Data behind it in 2026 | Here |
|---|---|---|
| Official possession | FIFA optical tracking (real ball-control time) | Pass share per 5-min window — correlates >0.95 |
| xG and xG race | Models trained on millions of shots (Opta/StatsBomb) | StatsBomb official xG (open event data) |
| Player touch/pass maps | Event data | Identical |
| Pass networks and formations | Event data + lineups | Identical |
| Distances, speeds, sprints | Optical tracking + GPS | **Needs tracking** — free samples: Metrica, SkillCorner |
| Line breaks, pressure, space creation | FIFA Football Intelligence on skeletal tracking | Advanced phase: pitch control with the Metrica sample |

**Rule of thumb:** if the analysis is about *where an on-ball action happened* → event data (we have it). If it is about *where the other 21 players were* or *how much someone ran* → tracking (open samples only).

## Where to find public 2026 stats — and is the API really free?

- **Public sites with 2026 stats** (no signup): [FBref](https://fbref.com/en/comps/1/World-Cup-Stats) (basic stats), FOX Sports (team xG), xGscore and FootyStats (per-match xG), FotMob and SofaScore (apps, very complete).
- **The football-data.org API is free**: 1-minute signup, no card, key by email. The free tier (10 req/min) covers the World Cup: results, fixtures, standings and scorers. NOT included for free: live minute-by-minute and fine-grained stats (paid add-ons). Free alternative: API-Football (100 req/day).
- **Shot-by-shot 2026 event data**: not public yet. StatsBomb usually releases World Cups months after the final — when it lands, this dashboard absorbs it by changing two IDs (`competition_id`/`season_id`).
"""


# ---------- Carga de datos (cacheada) ----------

@st.cache_data
def matches() -> pd.DataFrame:
    return statsbomb.load_matches()


@st.cache_data
def shots() -> pd.DataFrame:
    return statsbomb.load_shots()


@st.cache_data
def events(match_id: int) -> pd.DataFrame:
    return statsbomb.load_events(match_id)


@st.cache_data
def nicknames() -> dict:
    return statsbomb.load_nicknames()


@st.cache_data
def results() -> pd.DataFrame:
    """Resultados completos de todos los Mundiales 1930-2022 (Fjelstul database)."""
    path = statsbomb.PROCESSED / "results_matches.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


@st.cache_data(ttl=600)
def fd_api(path: str, token: str) -> dict:
    """football-data.org v4 (free tier: 10 req/min). Cachea 10 minutos.

    Respeta el throttling que documenta la API: si responde 429, espera lo que
    indique X-RequestCounter-Reset / Retry-After (una sola vez) y reintenta.
    """
    import time

    for attempt in range(2):
        r = requests.get(f"https://api.football-data.org/v4{path}",
                         headers={"X-Auth-Token": token}, timeout=30)
        if r.status_code == 429 and attempt == 0:
            wait = int(r.headers.get("Retry-After")
                       or r.headers.get("X-RequestCounter-Reset") or 60)
            time.sleep(min(wait, 65))
            continue
        r.raise_for_status()
        return r.json()
    return {}


# ---------- Tab 1: Partido a fondo ----------

def tab_match(t: dict, m: pd.DataFrame, s_all: pd.DataFrame):
    if m.empty:
        st.info(t["no_data"])
        return
    m = m.copy()
    m["label"] = m.stage + " · " + m.home_team + " " + m.home_score.astype(str) \
        + "-" + m.away_score.astype(str) + " " + m.away_team
    label = st.selectbox(t["match"], m.label, index=len(m) - 1)
    row = m[m.label == label].iloc[0]
    team_a, team_b = row.home_team, row.away_team

    s = s_all[s_all.match_id == row.match_id]
    if (s.period == 5).any():
        st.caption(t["pens_note"])
    s = s[s.period < 5]  # la tanda de penales no cuenta en las estadísticas del partido
    xg_a, xg_b = s[s.team == team_a].xg.sum(), s[s.team == team_b].xg.sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(team_a, row.home_score, f"xG {xg_a:.2f}", delta_color="off")
    c2.metric(team_b, row.away_score, f"xG {xg_b:.2f}", delta_color="off")
    c3.metric(t["shots"], f"{(s.team == team_a).sum()} - {(s.team == team_b).sum()}")
    c4.metric(t["stage"], row.stage)

    # Carrera de xG
    fig = go.Figure()
    for team, color in ((team_a, BLUE), (team_b, ORANGE)):
        tt = s[s.team == team].sort_values(["period", "minute"])
        x = [0] + tt.minute.tolist()
        y = [0] + tt.xg.cumsum().round(3).tolist()
        fig.add_trace(go.Scatter(x=x, y=y, name=team, mode="lines",
                                 line=dict(color=color, width=2, shape="hv")))
        g = tt[tt.is_goal]
        fig.add_trace(go.Scatter(
            x=g.minute, y=tt.xg.cumsum()[g.index].round(3), mode="markers",
            marker=dict(color=color, size=11, symbol="circle", line=dict(color=INK, width=1)),
            name=f"{t['goal']} {team}", text=g.player.map(lambda p: nicknames().get(p, p)),
            hovertemplate=t["goal"] + ": %{text} %{x}'<extra></extra>"))
    fig.update_layout(title=t["race_title"], xaxis_title=t["minute"],
                      yaxis_title=t["cum_xg"], **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(t["shot_map"])
    st.caption(t["shot_map_cap"].format(a=team_a))
    st.pyplot(viz.shot_map_fig(s, team_a, team_b, nicks=nicknames(), tr=t["viz_tr"]),
              use_container_width=True)

    st.subheader(t["networks"])
    ev = events(int(row.match_id))
    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(viz.pass_network_fig(ev, team_a, viz.PITCH_A, nicks=nicknames(),
                                       tr=t["viz_tr"]), use_container_width=True)
    with col2:
        st.pyplot(viz.pass_network_fig(ev, team_b, viz.PITCH_B, nicks=nicknames(),
                                       tr=t["viz_tr"]), use_container_width=True)

    # ---- Posesión ----
    st.subheader(t["possession"])
    pos_a = metrics.possession_share(ev, team_a)
    c1, c2 = st.columns(2)
    c1.metric(team_a, f"{pos_a:.0f}%")
    c2.metric(team_b, f"{100 - pos_a:.0f}%")

    flow = metrics.possession_flow(ev, team_a)
    colors = [BLUE if v >= 50 else ORANGE for v in flow.pct_a]
    fig = go.Figure(go.Bar(
        x=flow.tbin + 2.5, y=flow.pct_a - 50, base=50, width=4.6, marker_color=colors,
        customdata=flow.pct_a.round(0),
        hovertemplate="min %{x:.0f}: " + team_a + " %{customdata:.0f}%<extra></extra>"))
    for _, g in s[s.is_goal].iterrows():
        fig.add_vline(x=g.minute, line=dict(color=INK, width=1, dash="dot"),
                      annotation_text=viz.short_name(g.player, nicknames()),
                      annotation_font_size=9, annotation_position="top")
    fig.add_hline(y=50, line=dict(color=MUTED, width=1))
    fig.update_layout(title=t["flow_title"].format(a=team_a),
                      xaxis_title=t["minute"], yaxis_title=t["flow_pct"],
                      yaxis=dict(range=[0, 100]), height=340,
                      **{**PLOTLY_LAYOUT, "hovermode": "closest"})
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t["flow_cap"])

    # ---- Jugador a jugador ----
    st.subheader(t["player_sec"])
    players = (ev[ev.player_name.notna()].groupby("player_name")
               .agg(team=("team_name", "first"), n=("player_name", "size"))
               .sort_values(["team", "n"], ascending=[True, False]))
    player = st.selectbox(t["player"], players.index,
                          format_func=lambda p: f"{nicknames().get(p, p)} ({players.loc[p, 'team']})")
    display = nicknames().get(player, player)
    color = viz.PITCH_A if players.loc[player, "team"] == team_a else viz.PITCH_B

    ps = metrics.player_match_stats(ev, player)
    r1 = st.columns(6)
    r1[0].metric(t["m_passes"], f"{ps['pases_completados']}/{ps['pases']}")
    r1[1].metric(t["m_pass_pct"], f"{ps['pct_pase']:.0f}%")
    r1[2].metric(t["m_key"], ps["pases_clave"])
    r1[3].metric(t["m_shots"], ps["tiros"])
    r1[4].metric("xG", ps["xg"])
    r1[5].metric(t["m_goals"], ps["goles"])
    r2 = st.columns(6)
    r2[0].metric(t["m_carries"], ps["conducciones"])
    r2[1].metric(t["m_dribbles"], ps["regates"])
    r2[2].metric(t["m_press"], ps["presiones"])
    r2[3].metric(t["m_recov"], ps["recuperaciones"])
    r2[4].metric(t["m_assists"], ps["asistencias"])
    r2[5].metric(t["m_actions"], ps["acciones"])

    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(viz.touch_map_fig(ev, player, color, display_name=display, tr=t["viz_tr"]),
                  use_container_width=True)
    with col2:
        st.pyplot(viz.pass_map_fig(ev, player, color, display_name=display, tr=t["viz_tr"]),
                  use_container_width=True)

    act = metrics.player_activity(ev, player)
    fig = go.Figure(go.Bar(x=act.tbin + 2.5, y=act.acciones, width=4.6, marker_color=BLUE,
                           hovertemplate="min %{x:.0f}: %{y}<extra></extra>"))
    fig.update_layout(title=t["involvement"], xaxis_title=t["minute"],
                      yaxis_title=t["actions_y"], height=300,
                      **{**PLOTLY_LAYOUT, "hovermode": "closest"})
    st.plotly_chart(fig, use_container_width=True)


# ---------- Tab 2: Torneo 2022 ----------

def tab_tournament(t: dict, m: pd.DataFrame, s_all: pd.DataFrame, r: pd.DataFrame):
    if m.empty and r.empty:
        st.info(t["no_data"])
        return

    # Cuadro primero, como en las coberturas: Fjelstul (completo) si existe,
    # si no, los partidos de StatsBomb normalizados
    src = r if not r.empty else _sb_results(m, s_all)
    rounds = results_bracket_rounds(src, t)
    if rounds:
        st.subheader(t["bracket"])
        st.markdown(bracket_html(rounds), unsafe_allow_html=True)

    if m.empty or s_all.empty:
        st.info(t["results_only"])
        return

    # las tandas de penales (period 5) no cuentan como tiros ni goles en las stats oficiales
    s = s_all.query("period < 5")

    xg_for = s.groupby("team").xg.sum()
    against = []
    for _, r in m.iterrows():
        ms = s[s.match_id == r.match_id]
        against.append({"team": r.home_team, "xg": ms[ms.team == r.away_team].xg.sum()})
        against.append({"team": r.away_team, "xg": ms[ms.team == r.home_team].xg.sum()})
    xg_against = pd.DataFrame(against).groupby("team").xg.sum()
    played = pd.concat([m.home_team, m.away_team]).value_counts()

    teams = pd.DataFrame({"xg_for": xg_for, "xg_against": xg_against, "pj": played}).dropna()
    teams["xg_for_90"], teams["xg_against_90"] = teams.xg_for / teams.pj, teams.xg_against / teams.pj

    fig = go.Figure(go.Scatter(
        x=teams.xg_for_90, y=teams.xg_against_90, mode="markers+text",
        text=teams.index, textposition="top center", textfont=dict(size=9, color=MUTED),
        marker=dict(color=BLUE, size=teams.pj * 1.6 + 4, line=dict(color="white", width=1)),
        hovertemplate="<b>%{text}</b><br>" + t["xg_for"] + ": %{x:.2f}<br>"
                      + t["xg_against"] + ": %{y:.2f}<extra></extra>"))
    fig.add_hline(y=teams.xg_against_90.median(), line=dict(color=MUTED, dash="dot", width=1))
    fig.add_vline(x=teams.xg_for_90.median(), line=dict(color=MUTED, dash="dot", width=1))
    fig.update_layout(title=t["map_title"], xaxis_title=t["xg_for"], yaxis_title=t["xg_against"],
                      height=560, **{**PLOTLY_LAYOUT, "hovermode": "closest"})
    fig.update_yaxes(autorange="reversed")  # arriba = conceder poco (mejor)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t["map_cap"])

    players = (s.groupby("player").agg(goles=("is_goal", "sum"), xg=("xg", "sum"),
                                       tiros=("xg", "size"), equipo=("team", "first"))
               .query("goles >= 3").sort_values("goles", ascending=False))
    players.index = [nicknames().get(p, p) for p in players.index]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=players.index, y=players.goles, name=t["goals_lbl"], marker_color=BLUE))
    fig2.add_trace(go.Bar(x=players.index, y=players.xg.round(2), name="xG", marker_color=ORANGE))
    fig2.update_layout(title=t["scorers_title"], barmode="group", bargap=0.25,
                       **{**PLOTLY_LAYOUT, "hovermode": "x"})
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(t["scorers_cap"])


# ---------- Mundial 2026 en vivo (API, sin event data todavía) ----------

def _wc26_token(t: dict) -> str | None:
    token = os.getenv("FOOTBALL_DATA_TOKEN")
    if not token:
        st.info(t["no_key"])
    return token


def _wc26_matches_df(token: str) -> pd.DataFrame:
    ms = pd.json_normalize(fd_api("/competitions/WC/matches", token).get("matches", []), sep="_")
    if not ms.empty:
        ms["fecha"] = pd.to_datetime(ms.utcDate).dt.strftime("%Y-%m-%d %H:%M")
        ms["marcador"] = ms.score_fullTime_home.astype("Int64").astype(str) + " - " \
            + ms.score_fullTime_away.astype("Int64").astype(str)
    return ms


def _txt(row, key: str, fallback: str = "—") -> str:
    v = row.get(key)
    return v if isinstance(v, str) and v else fallback


# ---------- Cuadro de llaves (bracket) genérico, estilo tarjetas ----------

def _bracket_card(card: dict) -> str:
    rows = ""
    for name_html, score, win in card["rows"]:
        weight, opacity = ("700", "1") if win else ("400", ".8")
        rows += (f"<div style='display:flex;justify-content:space-between;gap:8px;"
                 f"font-weight:{weight};opacity:{opacity}'>"
                 f"<span style='white-space:nowrap;overflow:hidden;"
                 f"text-overflow:ellipsis'>{name_html}</span><span>{score}</span></div>")
    return (f"<div style='background:rgba(128,128,128,.13);border-radius:10px;"
            f"padding:7px 10px;margin:3px 0;font-size:.85rem'>"
            f"<div style='color:#8a8f98;font-size:.7rem;margin-bottom:3px'>{card['when']}</div>"
            f"{rows}</div>")


def bracket_html(rounds: list) -> str:
    """rounds = [(etiqueta, [tarjetas])] → columnas flexbox alineadas verticalmente,
    con las tarjetas de cada ronda distribuidas a la altura de sus llaves de origen."""
    n0 = max(len(cards) for _, cards in rounds)
    height = max(320, n0 * 96)
    cols = ""
    for label, cards in rounds:
        cards_html = "".join(_bracket_card(c) for c in cards)
        cols += (f"<div style='flex:1;min-width:0;display:flex;flex-direction:column'>"
                 f"<div style='font-weight:600;font-size:.9rem;margin-bottom:6px'>{label}</div>"
                 f"<div style='flex:1;display:flex;flex-direction:column;"
                 f"justify-content:space-around'>{cards_html}</div></div>")
    return f"<div style='display:flex;gap:12px;height:{height}px'>{cols}</div>"


def _sb_results(m_sel: pd.DataFrame, s_all: pd.DataFrame) -> pd.DataFrame:
    """Normaliza los partidos de StatsBomb al esquema de resultados, reconstruyendo
    la tanda de penales desde los tiros de period 5 del event data."""
    if m_sel.empty:
        return pd.DataFrame()
    pens = (s_all[s_all.period == 5].groupby(["match_id", "team"]).is_goal.sum()
            if not s_all.empty else pd.Series(dtype=int))
    rows = []
    for _, m in m_sel.iterrows():
        ph = pa = None
        if m.home_score == m.away_score and (m.match_id, m.home_team) in pens.index:
            ph = int(pens.get((m.match_id, m.home_team), 0))
            pa = int(pens.get((m.match_id, m.away_team), 0))
        rows.append({"stage": m.stage, "date": m.date,
                     "home_team": m.home_team, "away_team": m.away_team,
                     "home_score": m.home_score, "away_score": m.away_score,
                     "pen_home": ph, "pen_away": pa})
    return pd.DataFrame(rows)


def results_bracket_rounds(df: pd.DataFrame, t: dict, max_col: int = 12) -> list:
    """Rondas del cuadro desde una tabla de resultados (stage, date, equipos, marcador, penales).

    - Torneos chicos (≤ 40 partidos, los Mundiales de 16 equipos o datos parciales):
      se grafica TODO el torneo, fase de grupos incluida.
    - Columnas con más de `max_col` tarjetas se parten en varias.
    - Las rondas se ordenan cronológicamente (fecha del primer partido de cada fase).
    """
    if df.empty:
        return []
    d = df.copy()
    if len(d) > 40:  # torneo moderno completo: solo eliminatorias
        d = d[~d.stage.str.contains("group", case=False)]
    if d.empty:
        return []

    def pen_txt(p):
        return (f" <span style='font-size:.7rem;color:#8a8f98'>({int(p)})</span>"
                if pd.notna(p) else "")

    order = d.groupby("stage").date.min().sort_values().index
    rounds = []
    for stage in order:
        cards = []
        for _, m in d[d.stage == stage].sort_values("date").iterrows():
            hs, as_ = int(m.home_score), int(m.away_score)
            ph, pa = m.get("pen_home"), m.get("pen_away")
            win_h = hs > as_ or (pd.notna(ph) and ph > pa)
            win_a = as_ > hs or (pd.notna(pa) and pa > ph)
            cards.append({
                "when": pd.to_datetime(m.date).strftime("%d %b %Y"),
                "rows": [
                    (f"{flag(m.home_team)} {m.home_team}", f"{hs}{pen_txt(ph)}", win_h),
                    (f"{flag(m.away_team)} {m.away_team}", f"{as_}{pen_txt(pa)}", win_a),
                ],
            })
        label = t["stages_sb"].get(stage, stage.title() if stage.islower() else stage)
        n_chunks = -(-len(cards) // max_col)
        for i in range(n_chunks):
            chunk = cards[i * max_col:(i + 1) * max_col]
            rounds.append((label if n_chunks == 1 else f"{label} · {i + 1}", chunk))
    return rounds


def wc26_bracket_rounds(ms: pd.DataFrame, t: dict) -> list:
    """Rondas eliminatorias del 2026 desde la API (banderas = crests)."""
    rounds = []
    for stage, label in t["stages"].items():
        stage_ms = ms[ms.stage == stage]
        if stage_ms.empty:
            continue
        cards = []
        for _, m in stage_ms.sort_values("utcDate").iterrows():
            def side(prefix):
                name = _txt(m, f"{prefix}Team_shortName", _txt(m, f"{prefix}Team_name"))
                crest = m.get(f"{prefix}Team_crest")
                img = (f'<img src="{crest}" width="16" style="vertical-align:-3px"> '
                       if isinstance(crest, str) and crest else "")
                return f"{img}{name}"
            when = pd.to_datetime(m.utcDate).strftime("%d %b · %H:%M")
            if m.get("status") == "FINISHED":
                win = m.get("score_winner")
                cards.append({"when": when, "rows": [
                    (side("home"), int(m.score_fullTime_home), win == "HOME_TEAM"),
                    (side("away"), int(m.score_fullTime_away), win == "AWAY_TEAM")]})
            else:
                cards.append({"when": when, "rows": [
                    (side("home"), "", False), (side("away"), "", False)]})
        rounds.append((label, cards))
    return rounds


def tab_wc26_overview(t: dict):
    """Vista de torneo del Mundial 2026: grupos, llaves y goleadores (estilo FIFA)."""
    token = _wc26_token(t)
    if not token:
        return
    st.caption(t["live_cap"])

    try:
        standings = fd_api("/competitions/WC/standings", token)
        ms = _wc26_matches_df(token)
    except requests.HTTPError as e:
        st.error(t["api_err"].format(c=e.response.status_code))
        return

    # Llaves primero (el torneo va por eliminatorias)
    if not ms.empty:
        rounds = wc26_bracket_rounds(ms, t)
        if rounds:
            st.subheader(t["bracket"])
            st.markdown(bracket_html(rounds), unsafe_allow_html=True)

    # Fase de grupos con escudos
    st.subheader(t["groups"])
    groups = [g for g in standings.get("standings", []) if g.get("type") == "TOTAL"]
    cols = st.columns(3)
    for i, g in enumerate(groups):
        rows = [{
            "crest": e["team"].get("crest"),
            t["col_team"]: e["team"].get("shortName") or e["team"]["name"],
            t["col_pj"]: e["playedGames"],
            t["col_dg"]: e["goalDifference"],
            t["col_pts"]: e["points"],
        } for e in g["table"]]
        with cols[i % 3]:
            st.markdown(f"**{t['group']} {g.get('group', '').replace('GROUP_', '')}**")
            st.dataframe(pd.DataFrame(rows),
                         column_config={"crest": st.column_config.ImageColumn("", width=30)},
                         hide_index=True, use_container_width=True)

    try:
        sc = pd.json_normalize(
            fd_api("/competitions/WC/scorers?limit=15", token).get("scorers", []), sep="_")
        if not sc.empty:
            st.subheader(t["top_scorers_26"])
            fig = go.Figure(go.Bar(
                x=sc.player_name, y=sc.goals, marker_color=BLUE,
                text=sc.team_name,
                hovertemplate="<b>%{x}</b> (%{text})<br>%{y}<extra></extra>"))
            fig.update_layout(yaxis_title=t["goals_lbl"], **{**PLOTLY_LAYOUT, "hovermode": "x"})
            st.plotly_chart(fig, use_container_width=True)
    except requests.HTTPError:
        st.caption(t["scorers_fail"])


def tab_wc26_matches(t: dict):
    """'Partido a fondo' del 2026: sin event data aún — resultados y calendario."""
    token = _wc26_token(t)
    if not token:
        return
    st.info(t["no_event_2026"])

    try:
        ms = _wc26_matches_df(token)
    except requests.HTTPError as e:
        st.error(t["api_err"].format(c=e.response.status_code))
        return
    if ms.empty:
        st.warning(t["no_matches"])
        return

    played = ms[ms.status == "FINISHED"]
    upcoming = ms[ms.status.isin(["SCHEDULED", "TIMED"])]
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t["results"].format(n=len(played)))
        st.dataframe(played.sort_values("utcDate", ascending=False)
                     [["fecha", "stage", "homeTeam_name", "marcador", "awayTeam_name"]]
                     .rename(columns={"fecha": t["date"], "homeTeam_name": t["home"],
                                      "awayTeam_name": t["away"], "stage": t["stage_col"]})
                     .head(20), use_container_width=True, hide_index=True)
    with c2:
        st.subheader(t["upcoming"])
        st.dataframe(upcoming.sort_values("utcDate")
                     [["fecha", "stage", "homeTeam_name", "awayTeam_name"]]
                     .rename(columns={"fecha": t["date"], "homeTeam_name": t["home"],
                                      "awayTeam_name": t["away"], "stage": t["stage_col"]})
                     .head(20), use_container_width=True, hide_index=True)


# ---------- Layout ----------

lang_col, _ = st.columns([1, 4])
with lang_col:
    lang = st.radio("Idioma / Language", ["Español", "English"], horizontal=True,
                    label_visibility="collapsed")
LANG = "es" if lang == "Español" else "en"
T = STR[LANG]

st.title("Soccer Analytics Lab")

# Navegación jerárquica: torneo/liga → temporada → (torneo global | partido a fondo)
# El Mundial 2026 en curso es una entrada más del selector (vía API, sin event data aún).
m_all, r_all = matches(), results()
comps = sorted(set(m_all.competition.unique())
               | (set(r_all.competition.unique()) if not r_all.empty else set()))
col_c, col_s = st.columns([2, 1])
comp = col_c.selectbox(T["competition"], comps + [T["live_wc"]])
is_live = comp == T["live_wc"]

if is_live:
    col_s.selectbox(T["season"], ["2026"])
else:
    sb_seasons = set(m_all[m_all.competition == comp].season.unique())
    fj_seasons = (set(r_all[r_all.competition == comp].season.unique())
                  if not r_all.empty else set())
    seasons = sorted(sb_seasons | fj_seasons, key=lambda s: s[:4], reverse=True)
    season = col_s.selectbox(T["season"], seasons)
    m_sel = m_all[(m_all.competition == comp) & (m_all.season == season) & m_all.has_events]
    s_sel = shots()[shots().match_id.isin(m_sel.match_id)]
    r_sel = (r_all[(r_all.competition == comp) & (r_all.season == season)]
             if not r_all.empty else pd.DataFrame())
    cap_l, cap_r = st.columns([3, 2])
    cap_l.caption(T["sel_cap"].format(n=len(m_sel)) if len(m_sel) else T["results_only"])
    with cap_r.expander(T["add_more"]):
        st.markdown(T["add_more_body"])

t1, t2, t3 = st.tabs(T["tabs"])
with t1:
    tab_wc26_overview(T) if is_live else tab_tournament(T, m_sel, s_sel, r_sel)
with t2:
    tab_wc26_matches(T) if is_live else tab_match(T, m_sel, s_sel)
with t3:
    st.markdown(METODOLOGIA_ES if LANG == "es" else METODOLOGIA_EN)
