"""Figuras de cancha (mplsoccer) reutilizables por notebooks y dashboard.

Estilo broadcast: césped verde con líneas blancas. Sobre verde, las marcas de
los equipos son amarillo y blanco (par distinguible entre sí, con alto contraste
sobre el césped y seguro para daltonismo: el eje azul-amarillo se conserva en
las deficiencias rojo-verde). Los textos sobre césped llevan borde oscuro.
"""

import matplotlib.patheffects as pe
import pandas as pd
from mplsoccer import Pitch

# Para gráficos sobre fondo claro (plotly / matplotlib fuera de la cancha)
COLOR_A, COLOR_B = "#1a78cf", "#e66100"
INK = "#212529"

# Para marcas sobre césped
GRASS = "#2f7d3f"
PITCH_A, PITCH_B = "#ffd60a", "#ffffff"      # amarillo / blanco
PITCH_FAIL = "#212529"                        # marcas de acciones falladas
PITCH_TEXT = "#ffffff"
STROKE = [pe.withStroke(linewidth=2.2, foreground="#14532d")]
PITCH_KW = dict(pitch_type="statsbomb", pitch_color=GRASS, line_color="#ffffff",
                linewidth=1.2, line_alpha=0.85)

# Etiquetas por defecto (español); el dashboard pasa su propio dict según idioma
TR = {
    "goal": "gol", "miss": "fallo", "completed": "Completado", "failed": "Fallado",
    "touches_of": "Toques de", "passes_of": "Pases de", "actions": "acciones",
    "attacks_right": "ataca a la derecha", "until_sub": "hasta la primera sustitución (min {m})",
}


def short_name(name: str, nicks: dict | None = None) -> str:
    """Nombre corto reconocible: 'Lionel Andrés Messi Cuccittini' → 'Messi'.

    Usa el apodo de StatsBomb (lineups) quitando el nombre de pila; si no hay
    apodo, cae al último token del nombre completo.
    """
    nick = (nicks or {}).get(name)
    if nick and nick != name:
        parts = nick.split()
        return " ".join(parts[1:]) if len(parts) > 1 else nick
    return name.split()[-1]


def _grass_legend(ax, ncol: int):
    """Leyenda dentro de la cancha (sobre césped) para que el blanco sea visible."""
    leg = ax.legend(loc="lower center", ncol=ncol, fontsize=8, frameon=False,
                    bbox_to_anchor=(0.5, 0.005), labelcolor=PITCH_TEXT)
    for t in leg.get_texts():
        t.set_path_effects(STROKE)
    return leg


def shot_map_fig(shots: pd.DataFrame, team_a: str, team_b: str, title: str = "",
                 nicks: dict | None = None, tr: dict = TR):
    """Shot map de un partido: team_a (amarillo) ataca a la derecha, team_b (blanco) a la izquierda.

    `shots` requiere columnas: team, x, y, xg, outcome, player, minute.
    """
    shots = shots.copy()
    mask_b = shots.team == team_b
    shots.loc[mask_b, "x"] = 120 - shots.loc[mask_b, "x"]
    shots.loc[mask_b, "y"] = 80 - shots.loc[mask_b, "y"]

    pitch = Pitch(**PITCH_KW)
    fig, ax = pitch.draw(figsize=(11, 7.5))
    for team, color in ((team_a, PITCH_A), (team_b, PITCH_B)):
        t = shots[shots.team == team]
        goals, misses = t[t.outcome == "Goal"], t[t.outcome != "Goal"]
        pitch.scatter(misses.x, misses.y, s=misses.xg * 900 + 40, facecolor="none",
                      edgecolor=color, linewidth=1.7, ax=ax, label=f"{team} ({tr['miss']})")
        pitch.scatter(goals.x, goals.y, s=goals.xg * 900 + 40, color=color,
                      edgecolor="#14532d", linewidth=1, ax=ax, label=f"{team} ({tr['goal']})")
        # etiquetas alternadas arriba/abajo para que no colisionen en zonas densas
        for i, (_, g) in enumerate(goals.sort_values("y").iterrows()):
            dy = 10 if i % 2 == 0 else -16
            ax.annotate(f"{short_name(g.player, nicks)} {g.minute}'", (g.x, g.y),
                        xytext=(0, dy), textcoords="offset points", ha="center",
                        fontsize=8, color=PITCH_TEXT, path_effects=STROKE)
    if title:
        ax.set_title(title, fontsize=12, color=INK)
    _grass_legend(ax, ncol=4)
    return fig


def pass_network_fig(events: pd.DataFrame, team: str, color: str = PITCH_A,
                     nicks: dict | None = None, tr: dict = TR):
    """Red de pases del once inicial hasta la primera sustitución.

    `events` es el DataFrame aplanado de eventos de StatsBomb (sep='_').
    """
    xi = events[(events.type_name == "Starting XI") & (events.team_name == team)].iloc[0]
    formation = "-".join(str(int(xi.tactics_formation)))
    jersey = {p["player"]["name"]: p["jersey_number"] for p in xi.tactics_lineup}

    subs = events[(events.type_name == "Substitution") & (events.team_name == team)]
    first_sub = subs.minute.min() if len(subs) else events.minute.max()
    passes = events[(events.type_name == "Pass") & (events.team_name == team)
                    & events.pass_recipient_name.notna() & (events.minute < first_sub)].copy()
    passes[["x", "y"]] = pd.DataFrame(passes.location.tolist(), index=passes.index)

    avg_pos = passes.groupby("player_name")[["x", "y"]].mean()
    volume = passes.player_name.value_counts()
    links = (passes.groupby(["player_name", "pass_recipient_name"]).size()
             .reset_index(name="n").query("n >= 3"))

    pitch = Pitch(**PITCH_KW)
    fig, ax = pitch.draw(figsize=(11, 7.5))
    for _, l in links.iterrows():
        if l.player_name in avg_pos.index and l.pass_recipient_name in avg_pos.index:
            p1, p2 = avg_pos.loc[l.player_name], avg_pos.loc[l.pass_recipient_name]
            pitch.lines(p1.x, p1.y, p2.x, p2.y, lw=l.n * 0.55, color=color,
                        alpha=0.45, zorder=1, ax=ax)
    pitch.scatter(avg_pos.x, avg_pos.y, s=volume.reindex(avg_pos.index) * 14,
                  color=color, edgecolor="#14532d", linewidth=1, zorder=2, ax=ax)
    for name, pos in avg_pos.iterrows():
        ax.annotate(jersey.get(name, "?"), (pos.x, pos.y), ha="center", va="center",
                    fontsize=9, fontweight="bold", color="#14532d", zorder=3)
        ax.annotate(short_name(name, nicks), (pos.x, pos.y), xytext=(0, -14),
                    textcoords="offset points", ha="center", fontsize=8,
                    color=PITCH_TEXT, path_effects=STROKE, zorder=3)
    ax.set_title(f"{team} ({formation}) · {tr['until_sub'].format(m=first_sub)}",
                 fontsize=12, color=INK)
    return fig


def touch_map_fig(events: pd.DataFrame, player: str, color: str = PITCH_A,
                  display_name: str | None = None, tr: dict = TR):
    """Mapa de toques de un jugador: dónde intervino a lo largo del partido."""
    g = events[(events.player_name == player) & events.location.notna()].copy()
    g[["x", "y"]] = pd.DataFrame(g.location.tolist(), index=g.index)

    pitch = Pitch(**PITCH_KW)
    fig, ax = pitch.draw(figsize=(9, 6.2))
    if len(g) >= 10:
        pitch.kdeplot(g.x, g.y, ax=ax, fill=True, levels=40, thresh=0.05,
                      cmap="YlOrRd", alpha=0.55, zorder=0.5)
    pitch.scatter(g.x, g.y, s=28, color=color, edgecolor="#14532d", linewidth=0.5,
                  alpha=0.9, zorder=2, ax=ax)
    ax.set_title(f"{tr['touches_of']} {display_name or player} ({len(g)} {tr['actions']}) "
                 f"· {tr['attacks_right']}", fontsize=11, color=INK)
    return fig


def pass_map_fig(events: pd.DataFrame, player: str, color: str = PITCH_A,
                 display_name: str | None = None, tr: dict = TR):
    """Mapa de pases de un jugador: flechas origen→destino, completados vs fallados."""
    p = events[(events.type_name == "Pass") & (events.player_name == player)].copy()
    p[["x", "y"]] = pd.DataFrame(p.location.tolist(), index=p.index)
    p[["ex", "ey"]] = pd.DataFrame(p.pass_end_location.tolist(), index=p.index)
    ok = p.pass_outcome_name.isna() if "pass_outcome_name" in p else p.index == p.index

    pitch = Pitch(**PITCH_KW)
    fig, ax = pitch.draw(figsize=(9, 6.2))
    done, fail = p[ok], p[~ok]
    if len(fail):
        pitch.arrows(fail.x, fail.y, fail.ex, fail.ey, width=1.2, headwidth=6, headlength=6,
                     color=PITCH_FAIL, alpha=0.55, zorder=1, ax=ax,
                     label=f"{tr['failed']} ({len(fail)})")
    if len(done):
        pitch.arrows(done.x, done.y, done.ex, done.ey, width=1.4, headwidth=6, headlength=6,
                     color=color, alpha=0.85, zorder=2, ax=ax,
                     label=f"{tr['completed']} ({len(done)})")
    _grass_legend(ax, ncol=2)
    ax.set_title(f"{tr['passes_of']} {display_name or player} · {tr['attacks_right']}",
                 fontsize=11, color=INK)
    return fig
