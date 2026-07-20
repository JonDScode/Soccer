# %% [markdown]
# # Mundial 2026 — análisis de grafos de la final (uso local y educativo)
#
# Event data del Mundial 2026 scrapeado de WhoScored por [nlbair/wc2026-events](https://github.com/nlbair/wc2026-events).
# **Los datos son propiedad de Opta**: viven solo en `data/raw/wc2026/` (gitignoreado),
# no se redistribuyen ni se exponen en la app pública. Este notebook es material de
# estudio personal.
#
# La pregunta que respondemos: la **red de pases** que dibujamos en el dashboard es
# una *visualización* (posiciones medias + volumen). El **análisis de grafos** de
# verdad — el que usan los papers y los buenos análisis tácticos — modela al equipo
# como un grafo dirigido ponderado y calcula métricas:
#
# - **Centralidad de grado**: quién participa en más circuitos de pase (volumen)
# - **Centralidad de intermediación** (betweenness): quién *conecta* circuitos que
#   sin él quedarían separados — a quién presionar para partir al equipo
# - **Centralidad de autovector** (eigenvector): quién es influyente por combinarse
#   con los influyentes
# - **Densidad**: cuántas de las conexiones posibles existen — coral vs dependiente

# %%
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from mplsoccer import Pitch

STROKE = [pe.withStroke(linewidth=2, foreground="#14532d")]

RAW = Path("..") / "data" / "raw" / "wc2026"
FINAL = RAW / "wc2026_spain_vs_argentina_2026-07-19_events.csv"
INK, GRASS = "#212529", "#2f7d3f"
STROKE_KW = dict(pitch_type="statsbomb", pitch_color=GRASS, line_color="white",
                 linewidth=1.2, line_alpha=0.85)

ev = pd.read_csv(FINAL, low_memory=False)
print(f"{ev.home_team[0]} {ev.home_score[0]} - {ev.away_score[0]} {ev.away_team[0]} "
      f"· {ev.match_date[0]} · {len(ev)} eventos")

# %% [markdown]
# ## Adaptador Opta → nuestro pipeline
#
# WhoScored usa coordenadas Opta (0-100, y hacia arriba); nuestro stack usa
# StatsBomb (120x80, y hacia abajo). El resto es mapear nombres de eventos.

# %%
def to_sb(x, y):
    return x * 1.2, (100 - y) * 0.8


ev["x_sb"], ev["y_sb"] = to_sb(ev.x, ev.y)
ev["ex_sb"], ev["ey_sb"] = to_sb(ev.endX, ev.endY)

# ¿Quién ganó la tanda? — limitación conocida: este scrape solo llega hasta la
# prórroga (no trae período de penales), así que el desenlace no está en el CSV
pens = ev[ev.period_name == "PenaltyShootout"]
if len(pens):
    tanda = pens[pens.isGoal.eq(True)].groupby("team").size()
    print("Tanda de penales:", dict(tanda))
else:
    print("La tanda de penales no está en este scrape (períodos hasta la prórroga).")

# %% [markdown]
# ## La red de pases como grafo dirigido ponderado
#
# WhoScored no trae receptor del pase: se infiere con el siguiente toque del mismo
# equipo (la aproximación estándar con estos datos).

# %%
def pass_graph(events: pd.DataFrame, team: str) -> nx.DiGraph:
    d = events.sort_values("id").reset_index(drop=True)
    passes = []
    for i, row in d[(d.event == "Pass") & (d.outcome == "Successful")
                    & (d.team == team)].iterrows():
        nxt = d.iloc[i + 1] if i + 1 < len(d) else None
        if nxt is not None and nxt.team == team and isinstance(nxt.player, str):
            passes.append((row.player, nxt.player))
    G = nx.DiGraph()
    for a, b in passes:
        if G.has_edge(a, b):
            G[a][b]["weight"] += 1
        else:
            G.add_edge(a, b, weight=1)
    return G


def graph_metrics(G: nx.DiGraph) -> pd.DataFrame:
    dist = {(a, b): 1 / d["weight"] for a, b, d in G.edges(data=True)}
    nx.set_edge_attributes(G, dist, "dist")
    return (pd.DataFrame({
        "grado (vol.)": dict(G.degree(weight="weight")),
        "intermediación": nx.betweenness_centrality(G, weight="dist"),
        "autovector": nx.eigenvector_centrality(G.to_undirected(), weight="weight",
                                                max_iter=2000),
    }).round(3).sort_values("intermediación", ascending=False))


teams = [ev.home_team[0], ev.away_team[0]]
for team in teams:
    G = pass_graph(ev, team)
    m = graph_metrics(G)
    dens = nx.density(G)
    print(f"\n=== {team} · densidad de la red: {dens:.3f} ===")
    print(m.head(6).to_string())

# %% [markdown]
# ## Grafo sobre la cancha: tamaño del nodo = INTERMEDIACIÓN (no volumen)
#
# Esta es la diferencia con la viz del dashboard: aquí el nodo grande no es quien
# más pases dio, sino quien más *conecta* — el jugador cuya anulación parte al
# equipo en dos.

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
colors = ("#ffd60a", "#ffffff")
for ax, team, color in zip(axes, teams, colors):
    pitch = Pitch(**STROKE_KW)
    pitch.draw(ax=ax)
    G = pass_graph(ev, team)
    m = graph_metrics(G)
    pos = (ev[(ev.team == team) & (ev.event == "Pass") & (ev.outcome == "Successful")]
           .groupby("player")[["x_sb", "y_sb"]].mean())
    for a, b, d in G.edges(data=True):
        if d["weight"] >= 4 and a in pos.index and b in pos.index:
            pitch.lines(pos.loc[a].x_sb, pos.loc[a].y_sb,
                        pos.loc[b].x_sb, pos.loc[b].y_sb,
                        lw=d["weight"] * 0.35, color=color, alpha=0.35, ax=ax, zorder=1)
    common = [p for p in m.index if p in pos.index]
    bet = m.loc[common, "intermediación"]
    pitch.scatter(pos.loc[common].x_sb, pos.loc[common].y_sb,
                  s=200 + bet * 2600, color=color, edgecolor="#14532d",
                  linewidth=1, ax=ax, zorder=2)
    for p in common:
        ax.annotate(p.split()[-1], (pos.loc[p].x_sb, pos.loc[p].y_sb),
                    xytext=(0, -13), textcoords="offset points", ha="center",
                    fontsize=7.5, color="white", path_effects=STROKE, zorder=3)
    ax.set_title(f"{team} · nodo = centralidad de intermediación", fontsize=11, color=INK)
fig.suptitle(f"Final Mundial 2026 · {teams[0]} 0-0 {teams[1]} · análisis de grafos",
             fontsize=13, color=INK)
fig.savefig(Path("..") / "reports" / "figures" / "wc2026_final_grafos_LOCAL.png",
            dpi=180, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## Lectura
#
# - **Volumen ≠ influencia estructural**: el ranking por grado (volumen) y por
#   intermediación no coinciden — el jugador "pulmón" que conecta defensa con
#   ataque no siempre es el que más pases acumula.
# - **La densidad** compara estilos: una red densa reparte la creación (difícil de
#   anular con marcas individuales); una red rala depende de pocos conectores.
# - Con esto, nuestra caja de herramientas cubre el repertorio completo del
#   análisis de redes en fútbol: la viz táctica (dashboard) + las métricas de
#   grafo (este notebook). Siguiente paso natural: correr estas métricas para los
#   104 partidos y rankear los "conectores" del Mundial.
