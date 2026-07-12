"""Soccer Analytics Lab — dashboard.

Tres vistas:
1. Partido a fondo  — event data del Mundial 2022 (StatsBomb): shot map, carrera de xG, redes de pases
2. Torneo 2022      — agregados: mapa de equipos por xG, goleadores vs xG
3. Mundial 2026     — resultados y goleadores en vivo vía football-data.org (API key gratuita)

Ejecutar:  streamlit run app/streamlit_app.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from soccer import statsbomb, viz  # noqa: E402

st.set_page_config(page_title="Soccer Analytics Lab", page_icon="⚽", layout="wide")

BLUE, ORANGE, INK, MUTED = viz.COLOR_A, viz.COLOR_B, "#212529", "#6c757d"
PLOTLY_LAYOUT = dict(
    template="plotly_white", font=dict(color=INK), margin=dict(l=40, r=20, t=50, b=40),
    hovermode="x unified",
)


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


@st.cache_data(ttl=600)
def fd_api(path: str, token: str) -> dict:
    """football-data.org v4 (free tier: 10 req/min). Cachea 10 minutos."""
    r = requests.get(f"https://api.football-data.org/v4{path}",
                     headers={"X-Auth-Token": token}, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------- Tab 1: Partido a fondo ----------

def tab_match():
    m = matches()
    m["label"] = m.stage + " · " + m.home_team + " " + m.home_score.astype(str) \
        + "-" + m.away_score.astype(str) + " " + m.away_team
    label = st.selectbox("Partido", m.label, index=len(m) - 1)
    row = m[m.label == label].iloc[0]
    team_a, team_b = row.home_team, row.away_team

    s = shots()[shots().match_id == row.match_id]
    if (s.period == 5).any():
        st.caption("⚠️ El partido se definió por penales; la tanda se excluye de tiros y xG.")
    s = s[s.period < 5]  # la tanda de penales no cuenta en las estadísticas del partido
    xg_a, xg_b = s[s.team == team_a].xg.sum(), s[s.team == team_b].xg.sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(team_a, row.home_score, f"xG {xg_a:.2f}", delta_color="off")
    c2.metric(team_b, row.away_score, f"xG {xg_b:.2f}", delta_color="off")
    c3.metric("Tiros", f"{(s.team == team_a).sum()} - {(s.team == team_b).sum()}")
    c4.metric("Fase", row.stage)

    # Carrera de xG: cuánta "producción de peligro" acumuló cada equipo minuto a minuto
    fig = go.Figure()
    for team, color in ((team_a, BLUE), (team_b, ORANGE)):
        t = s[s.team == team].sort_values(["period", "minute"])
        x = [0] + t.minute.tolist()
        y = [0] + t.xg.cumsum().round(3).tolist()
        fig.add_trace(go.Scatter(x=x, y=y, name=team, mode="lines",
                                 line=dict(color=color, width=2, shape="hv")))
        g = t[t.is_goal]
        fig.add_trace(go.Scatter(
            x=g.minute, y=t.xg.cumsum()[g.index].round(3), mode="markers",
            marker=dict(color=color, size=11, symbol="circle", line=dict(color=INK, width=1)),
            name=f"Gol {team}", text=g.player, hovertemplate="⚽ %{text} %{x}'<extra></extra>"))
    fig.update_layout(title="Carrera de xG (los puntos son goles)",
                      xaxis_title="Minuto", yaxis_title="xG acumulado", **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Shot map")
    st.caption(f"{team_a} ataca a la derecha · área del punto = xG del tiro · goles rellenos")
    st.pyplot(viz.shot_map_fig(s, team_a, team_b), use_container_width=True)

    st.subheader("Redes de pases")
    ev = events(int(row.match_id))
    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(viz.pass_network_fig(ev, team_a, BLUE), use_container_width=True)
    with col2:
        st.pyplot(viz.pass_network_fig(ev, team_b, ORANGE), use_container_width=True)


# ---------- Tab 2: Torneo 2022 ----------

def tab_tournament():
    # las tandas de penales (period 5) no cuentan como tiros ni goles en las stats oficiales
    s, m = shots().query("period < 5"), matches()

    # xG a favor / en contra por equipo
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
        hovertemplate="<b>%{text}</b><br>xG a favor/90: %{x:.2f}<br>xG en contra/90: %{y:.2f}<extra></extra>"))
    fig.add_hline(y=teams.xg_against_90.median(), line=dict(color=MUTED, dash="dot", width=1))
    fig.add_vline(x=teams.xg_for_90.median(), line=dict(color=MUTED, dash="dot", width=1))
    fig.update_layout(title="Mapa del torneo: producción vs concesión de peligro (por 90 min)",
                      xaxis_title="xG a favor por 90'", yaxis_title="xG en contra por 90'",
                      height=560, **{**PLOTLY_LAYOUT, "hovermode": "closest"})
    fig.update_yaxes(autorange="reversed")  # arriba = conceder poco (mejor)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Arriba-derecha = genera mucho y concede poco. Tamaño del punto = partidos jugados.")

    # Goleadores: goles vs xG
    players = (s.groupby("player").agg(goles=("is_goal", "sum"), xg=("xg", "sum"),
                                       tiros=("xg", "size"), equipo=("team", "first"))
               .query("goles >= 3").sort_values("goles", ascending=False))
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=players.index, y=players.goles, name="Goles", marker_color=BLUE))
    fig2.add_trace(go.Bar(x=players.index, y=players.xg.round(2), name="xG", marker_color=ORANGE))
    fig2.update_layout(title="Goleadores (3+): goles reales vs esperados",
                       barmode="group", bargap=0.25,
                       **{**PLOTLY_LAYOUT, "hovermode": "x"})
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Goles muy por encima del xG = definición excepcional (o suerte); por debajo = mala puntería o mala fortuna.")


# ---------- Tab 3: Mundial 2026 en vivo ----------

def tab_worldcup_2026():
    st.markdown(
        "Datos del **Mundial 2026 en curso** vía [football-data.org](https://www.football-data.org/) "
        "(free tier). Regístrate gratis y pega tu API key — o expórtala como `FOOTBALL_DATA_TOKEN`.")
    token = os.getenv("FOOTBALL_DATA_TOKEN") or st.text_input("API key", type="password")
    if not token:
        st.info("Sin API key no puedo consultar la API. El registro gratuito toma un minuto.")
        return

    try:
        data = fd_api("/competitions/WC/matches", token)
    except requests.HTTPError as e:
        st.error(f"La API respondió {e.response.status_code}: revisa la key o el rate limit (10 req/min).")
        return

    ms = pd.json_normalize(data.get("matches", []), sep="_")
    if ms.empty:
        st.warning("La API no devolvió partidos del Mundial 2026.")
        return
    ms["fecha"] = pd.to_datetime(ms.utcDate).dt.strftime("%Y-%m-%d %H:%M")
    ms["marcador"] = ms.score_fullTime_home.astype("Int64").astype(str) + " - " \
        + ms.score_fullTime_away.astype("Int64").astype(str)

    played = ms[ms.status == "FINISHED"]
    upcoming = ms[ms.status.isin(["SCHEDULED", "TIMED"])]

    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Últimos resultados ({len(played)} jugados)")
        st.dataframe(played.sort_values("utcDate", ascending=False)
                     [["fecha", "stage", "homeTeam_name", "marcador", "awayTeam_name"]]
                     .rename(columns={"homeTeam_name": "local", "awayTeam_name": "visitante",
                                      "stage": "fase"}).head(15),
                     use_container_width=True, hide_index=True)
    with c2:
        st.subheader("Próximos partidos")
        st.dataframe(upcoming.sort_values("utcDate")
                     [["fecha", "stage", "homeTeam_name", "awayTeam_name"]]
                     .rename(columns={"homeTeam_name": "local", "awayTeam_name": "visitante",
                                      "stage": "fase"}).head(15),
                     use_container_width=True, hide_index=True)

    try:
        scorers = fd_api("/competitions/WC/scorers?limit=15", token)
        sc = pd.json_normalize(scorers.get("scorers", []), sep="_")
        if not sc.empty:
            st.subheader("Goleadores del Mundial 2026")
            fig = go.Figure(go.Bar(
                x=sc.player_name, y=sc.goals, marker_color=BLUE,
                text=sc.team_name, hovertemplate="<b>%{x}</b> (%{text})<br>%{y} goles<extra></extra>"))
            fig.update_layout(yaxis_title="Goles", **{**PLOTLY_LAYOUT, "hovermode": "x"})
            st.plotly_chart(fig, use_container_width=True)
    except requests.HTTPError:
        st.caption("No pude cargar los goleadores (posible rate limit — espera un minuto).")


# ---------- Layout ----------

st.title("⚽ Soccer Analytics Lab")
t1, t2, t3 = st.tabs(["🔬 Partido a fondo (2022)", "🏆 Torneo 2022", "🔴 Mundial 2026 en vivo"])
with t1:
    tab_match()
with t2:
    tab_tournament()
with t3:
    tab_worldcup_2026()
