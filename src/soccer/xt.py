"""Expected Threat (xT) — modelo de Markov de Karun Singh.

La cancha se divide en una grilla de 16x12 celdas. Para cada celda se estima,
a partir del event data: la probabilidad de tirar desde ahí, la de gol si se
tira, y hacia dónde suele moverse el balón (pases completados y conducciones).
Iterando la ecuación de valor se obtiene V[celda] = cuánto "vale" tener el
balón en cada zona. El valor de una acción = V[destino] - V[origen]: eso es lo
que suma un pase progresivo aunque no termine en tiro — la base del gráfico de
match momentum de las transmisiones.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

W, H = 16, 12
X_MAX, Y_MAX = 120.0, 80.0
MODELS = Path(__file__).resolve().parent.parent.parent / "models"


def cell_of(x, y):
    cx = np.clip((np.asarray(x, dtype=float) / X_MAX * W).astype(int), 0, W - 1)
    cy = np.clip((np.asarray(y, dtype=float) / Y_MAX * H).astype(int), 0, H - 1)
    return cx, cy


def fit_grid(moves: pd.DataFrame, shots: pd.DataFrame, iters: int = 10) -> np.ndarray:
    """Ajusta la superficie de valor xT.

    moves: columnas x, y, ex, ey (origen y destino de pases completados y conducciones)
    shots: columnas x, y, is_goal
    """
    sx, sy = cell_of(shots.x, shots.y)
    shot_cnt = np.zeros((W, H))
    goal_cnt = np.zeros((W, H))
    np.add.at(shot_cnt, (sx, sy), 1)
    np.add.at(goal_cnt, (sx, sy), shots.is_goal.astype(float).values)

    mx, my = cell_of(moves.x, moves.y)
    ex, ey = cell_of(moves.ex, moves.ey)
    move_cnt = np.zeros((W, H))
    np.add.at(move_cnt, (mx, my), 1)
    trans = np.zeros((W, H, W, H))
    np.add.at(trans, (mx, my, ex, ey), 1)

    total = shot_cnt + move_cnt
    total[total == 0] = 1
    p_shot = shot_cnt / total
    p_move = move_cnt / total
    p_goal = np.divide(goal_cnt, shot_cnt, out=np.zeros_like(goal_cnt),
                       where=shot_cnt > 0)
    move_norm = move_cnt.copy()
    move_norm[move_norm == 0] = 1
    T = trans / move_norm[:, :, None, None]  # P(destino | origen, mover)

    V = np.zeros((W, H))
    for _ in range(iters):
        V = p_shot * p_goal + p_move * np.einsum("ijkl,kl->ij", T, V)
    return V


def save_grid(V: np.ndarray) -> Path:
    MODELS.mkdir(exist_ok=True)
    path = MODELS / "xt_grid.json"
    path.write_text(json.dumps(V.round(6).tolist()), encoding="utf-8")
    return path


def load_grid() -> np.ndarray | None:
    path = MODELS / "xt_grid.json"
    if not path.exists():
        return None
    return np.array(json.loads(path.read_text(encoding="utf-8")))


def _moves_from_events(events: pd.DataFrame) -> pd.DataFrame:
    """Pases completados y conducciones con origen/destino, desde eventos aplanados."""
    frames = []
    passes = events[(events.type_name == "Pass") & events.location.notna()]
    if "pass_outcome_name" in passes:
        passes = passes[passes.pass_outcome_name.isna()]
    if len(passes):
        p = pd.DataFrame(passes.location.tolist(), columns=["x", "y"], index=passes.index)
        p[["ex", "ey"]] = pd.DataFrame(passes.pass_end_location.tolist(), index=passes.index)
        p["team"], p["minute"], p["period"] = passes.team_name, passes.minute, passes.period
        frames.append(p)
    carries = events[(events.type_name == "Carry") & events.location.notna()]
    if len(carries):
        c = pd.DataFrame(carries.location.tolist(), columns=["x", "y"], index=carries.index)
        c[["ex", "ey"]] = pd.DataFrame(carries.carry_end_location.tolist(), index=carries.index)
        c["team"], c["minute"], c["period"] = carries.team_name, carries.minute, carries.period
        frames.append(c)
    return pd.concat(frames) if frames else pd.DataFrame()


def xt_momentum(events: pd.DataFrame, team_a: str, grid: np.ndarray,
                window: int = 4) -> pd.DataFrame:
    """Momentum del partido: diferencia por minuto de amenaza (xT) generada,
    suavizada con media móvil — el equivalente abierto del gráfico de las TVs."""
    moves = _moves_from_events(events)
    if moves.empty:
        return pd.DataFrame(columns=["minute", "momentum"])
    moves = moves[moves.period <= 4]
    cx, cy = cell_of(moves.x, moves.y)
    ex, ey = cell_of(moves.ex, moves.ey)
    moves["gain"] = np.clip(grid[ex, ey] - grid[cx, cy], 0, None)

    per_min = (moves.groupby(["minute", "team"]).gain.sum().unstack(fill_value=0.0)
               .reindex(range(int(moves.minute.max()) + 1), fill_value=0.0))
    team_b = [c for c in per_min.columns if c != team_a]
    diff = per_min.get(team_a, 0.0) - (per_min[team_b[0]] if team_b else 0.0)
    smooth = diff.rolling(window, center=True, min_periods=1).mean()
    return pd.DataFrame({"minute": smooth.index, "momentum": smooth.values})
