"""Métricas de partido derivadas de event data de StatsBomb."""

import pandas as pd


def possession_share(events: pd.DataFrame, team_a: str) -> float:
    """% de posesión de team_a, aproximado por proporción de pases (proxy estándar).

    La posesión "oficial" de FIFA se calcula con tracking (tiempo real de control);
    con event data la proporción de pases es el proxy aceptado y correlaciona >0.95.
    """
    p = events[(events.type_name == "Pass") & (events.period <= 4)]
    return float((p.team_name == team_a).mean() * 100)


def possession_flow(events: pd.DataFrame, team_a: str, bin_min: int = 5) -> pd.DataFrame:
    """Posesión por ventanas de `bin_min` minutos — el gráfico de 'momento' de las TV."""
    p = events[(events.type_name == "Pass") & (events.period <= 4)].copy()
    p["tbin"] = (p.minute // bin_min) * bin_min
    flow = p.groupby("tbin").agg(total=("team_name", "size"),
                                 a=("team_name", lambda s: int((s == team_a).sum())))
    flow["pct_a"] = flow.a / flow.total * 100
    return flow.reset_index()


def player_match_stats(events: pd.DataFrame, player: str) -> dict:
    """Resumen de la participación de un jugador en el partido."""
    g = events[events.player_name == player]
    passes = g[g.type_name == "Pass"]
    completed = passes.pass_outcome_name.isna() if "pass_outcome_name" in passes else passes.index.notna()
    col = lambda name: g[name] if name in g else pd.Series(dtype=object)  # noqa: E731
    return {
        "acciones": len(g),
        "pases": len(passes),
        "pases_completados": int(completed.sum()),
        "pct_pase": round(completed.mean() * 100, 1) if len(passes) else 0.0,
        "pases_clave": int(col("pass_shot_assist").fillna(False).sum()),
        "asistencias": int(col("pass_goal_assist").fillna(False).sum()),
        "conducciones": int((g.type_name == "Carry").sum()),
        "regates": int((g.type_name == "Dribble").sum()),
        "presiones": int((g.type_name == "Pressure").sum()),
        "recuperaciones": int((g.type_name == "Ball Recovery").sum()),
        "tiros": int((g.type_name == "Shot").sum()),
        "xg": round(float(col("shot_statsbomb_xg").fillna(0).sum()), 2),
        "goles": int((col("shot_outcome_name") == "Goal").sum()),
    }


def player_activity(events: pd.DataFrame, player: str, bin_min: int = 5) -> pd.DataFrame:
    """Acciones del jugador por ventana de tiempo — su 'pulso' a lo largo del partido."""
    g = events[(events.player_name == player) & (events.period <= 4)].copy()
    g["tbin"] = (g.minute // bin_min) * bin_min
    return g.groupby("tbin").size().reset_index(name="acciones")
