"""Figuras de cancha (mplsoccer) reutilizables por notebooks y dashboard."""

import pandas as pd
from mplsoccer import Pitch

# Par categórico azul/naranja: distinguible con visión normal y con daltonismo
COLOR_A, COLOR_B = "#1a78cf", "#e66100"
INK = "#212529"
PITCH_KW = dict(pitch_type="statsbomb", pitch_color="#f8f9fa", line_color="#495057", linewidth=1)


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


def shot_map_fig(shots: pd.DataFrame, team_a: str, team_b: str, title: str = "",
                 nicks: dict | None = None):
    """Shot map de un partido: team_a ataca a la derecha, team_b a la izquierda.

    `shots` requiere columnas: team, x, y, xg, outcome, player, minute.
    """
    shots = shots.copy()
    mask_b = shots.team == team_b
    shots.loc[mask_b, "x"] = 120 - shots.loc[mask_b, "x"]
    shots.loc[mask_b, "y"] = 80 - shots.loc[mask_b, "y"]

    pitch = Pitch(**PITCH_KW)
    fig, ax = pitch.draw(figsize=(11, 7.5))
    for team, color in ((team_a, COLOR_A), (team_b, COLOR_B)):
        t = shots[shots.team == team]
        goals, misses = t[t.outcome == "Goal"], t[t.outcome != "Goal"]
        pitch.scatter(misses.x, misses.y, s=misses.xg * 900 + 40, facecolor="none",
                      edgecolor=color, linewidth=1.6, ax=ax, label=f"{team} (fallo)")
        pitch.scatter(goals.x, goals.y, s=goals.xg * 900 + 40, color=color,
                      edgecolor=INK, linewidth=0.8, ax=ax, label=f"{team} (gol)")
        # etiquetas alternadas arriba/abajo para que no colisionen en zonas densas
        for i, (_, g) in enumerate(goals.sort_values("y").iterrows()):
            dy = 10 if i % 2 == 0 else -16
            ax.annotate(f"{short_name(g.player, nicks)} {g.minute}'", (g.x, g.y),
                        xytext=(0, dy), textcoords="offset points",
                        ha="center", fontsize=8, color=INK)
    if title:
        ax.set_title(title, fontsize=12, color=INK)
    ax.legend(loc="lower center", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.06))
    return fig


def pass_network_fig(events: pd.DataFrame, team: str, color: str = COLOR_A,
                     nicks: dict | None = None):
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
                        alpha=0.35, zorder=1, ax=ax)
    pitch.scatter(avg_pos.x, avg_pos.y, s=volume.reindex(avg_pos.index) * 14,
                  color=color, edgecolor=INK, linewidth=1, zorder=2, ax=ax)
    for name, pos in avg_pos.iterrows():
        ax.annotate(jersey.get(name, "?"), (pos.x, pos.y), ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white", zorder=3)
        ax.annotate(short_name(name, nicks), (pos.x, pos.y), xytext=(0, -14),
                    textcoords="offset points", ha="center", fontsize=8, color=INK, zorder=3)
    ax.set_title(f"{team} ({formation}) · hasta la primera sustitución (min {first_sub})",
                 fontsize=12, color=INK)
    return fig


def touch_map_fig(events: pd.DataFrame, player: str, color: str = COLOR_A,
                  display_name: str | None = None):
    """Mapa de toques de un jugador: dónde intervino a lo largo del partido."""
    g = events[(events.player_name == player) & events.location.notna()].copy()
    g[["x", "y"]] = pd.DataFrame(g.location.tolist(), index=g.index)

    pitch = Pitch(**PITCH_KW)
    fig, ax = pitch.draw(figsize=(9, 6.2))
    if len(g) >= 10:
        pitch.kdeplot(g.x, g.y, ax=ax, fill=True, levels=40, thresh=0.05,
                      cmap="Blues", alpha=0.5, zorder=0.5)
    pitch.scatter(g.x, g.y, s=28, color=color, edgecolor="white", linewidth=0.5,
                  alpha=0.8, zorder=2, ax=ax)
    ax.set_title(f"Toques de {display_name or player} ({len(g)} acciones) · ataca a la derecha",
                 fontsize=11, color=INK)
    return fig


def pass_map_fig(events: pd.DataFrame, player: str, color: str = COLOR_A,
                 display_name: str | None = None):
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
                     color="#adb5bd", alpha=0.7, zorder=1, ax=ax, label=f"Fallado ({len(fail)})")
    if len(done):
        pitch.arrows(done.x, done.y, done.ex, done.ey, width=1.4, headwidth=6, headlength=6,
                     color=color, alpha=0.75, zorder=2, ax=ax, label=f"Completado ({len(done)})")
    ax.legend(loc="lower center", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.07))
    ax.set_title(f"Pases de {display_name or player} · ataca a la derecha", fontsize=11, color=INK)
    return fig
