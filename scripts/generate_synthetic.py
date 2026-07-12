"""Genera una liga de fútbol sintética pero estadísticamente coherente.

Modelo:
- 20 equipos con fuerzas latentes de ataque y defensa (lognormal alrededor de 1).
- Calendario doble round-robin (380 partidos por temporada).
- Cada equipo genera tiros ~ Poisson según su ataque vs la defensa rival (+ ventaja local).
- Cada tiro tiene coordenadas en el área ofensiva; su xG sale de un modelo logístico
  de distancia y ángulo al arco (misma forma funcional que los xG reales).
- El resultado del tiro se muestrea Bernoulli(xG), así los goles, la tabla y las
  métricas xG-vs-goles son coherentes entre sí, como en datos reales.

Salida (CSV en data/synthetic/): teams.csv, matches.csv, shots.csv, standings.csv

Uso:
    python scripts/generate_synthetic.py                    # 1 temporada, seed 42
    python scripts/generate_synthetic.py --seasons 3 --seed 7
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"

TEAM_NAMES = [
    "Atlético Cumbre", "Real Páramo", "Deportivo Nevado", "Unión Cafetera",
    "Sporting Manglar", "CD Guadual", "Andes FC", "Marea Roja",
    "Cóndor United", "Halcones del Valle", "Tricolor SC", "Puerto Dorado",
    "Fortaleza Andina", "Ciclón del Norte", "Estrella del Sur", "Bravos de Sierra",
    "Leones del Río", "Volcán FC", "Tormenta Verde", "Titanes de la Costa",
]

# Arco en (105, 34) sobre una cancha de 105x68 (coordenadas estilo Wyscout/StatsBomb)
GOAL_X, GOAL_Y = 105.0, 34.0
GOAL_WIDTH = 7.32


def shot_xg(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """xG logístico en función de distancia y ángulo visible del arco."""
    dist = np.hypot(GOAL_X - x, GOAL_Y - y)
    # ángulo subtendido por los postes desde la posición del tiro
    a = np.hypot(GOAL_X - x, GOAL_Y - GOAL_WIDTH / 2 - y)
    b = np.hypot(GOAL_X - x, GOAL_Y + GOAL_WIDTH / 2 - y)
    cos_angle = np.clip((a**2 + b**2 - GOAL_WIDTH**2) / (2 * a * b), -1, 1)
    angle = np.arccos(cos_angle)
    # coeficientes calibrados para xG medio ~0.10 y ~2.7 goles/partido (valores reales)
    logit = -1.9 - 0.08 * dist + 2.0 * angle
    return 1 / (1 + np.exp(-logit))


def sample_shot_locations(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Tiros concentrados cerca del área, con dispersión realista."""
    x = np.clip(GOAL_X - rng.gamma(shape=2.0, scale=8.5, size=n), 55, 104.5)
    y = np.clip(rng.normal(GOAL_Y, 11.0, size=n), 2, 66)
    return x, y


def generate_season(rng: np.random.Generator, season: int, teams: pd.DataFrame):
    matches, shots = [], []
    match_id = season * 1000
    n = len(teams)
    for home in range(n):
        for away in range(n):
            if home == away:
                continue
            match_id += 1
            row_h, row_a = teams.iloc[home], teams.iloc[away]
            # tiros esperados: media liga ~12.5 por equipo, ajustada por fuerzas
            mu_home = 12.5 * row_h["attack"] / row_a["defense"] * 1.15  # ventaja local
            mu_away = 12.5 * row_a["attack"] / row_h["defense"] * 0.90
            goals = {}
            for team_row, mu, is_home in ((row_h, mu_home, True), (row_a, mu_away, False)):
                n_shots = rng.poisson(mu)
                x, y = sample_shot_locations(rng, n_shots)
                xg = shot_xg(x, y)
                goal = rng.random(n_shots) < xg
                goals[is_home] = int(goal.sum())
                minutes = np.sort(rng.integers(1, 95, size=n_shots))
                for j in range(n_shots):
                    shots.append({
                        "season": season, "match_id": match_id,
                        "team": team_row["team"], "is_home": is_home,
                        "minute": int(minutes[j]),
                        "x": round(float(x[j]), 2), "y": round(float(y[j]), 2),
                        "xg": round(float(xg[j]), 4), "is_goal": bool(goal[j]),
                    })
            matches.append({
                "season": season, "match_id": match_id,
                "home_team": row_h["team"], "away_team": row_a["team"],
                "home_goals": goals[True], "away_goals": goals[False],
            })
    return matches, shots


def build_standings(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (season, team), _ in matches.groupby(["season", "home_team"]).size().items():
        home = matches[(matches.season == season) & (matches.home_team == team)]
        away = matches[(matches.season == season) & (matches.away_team == team)]
        gf = home.home_goals.sum() + away.away_goals.sum()
        ga = home.away_goals.sum() + away.home_goals.sum()
        wins = (home.home_goals > home.away_goals).sum() + (away.away_goals > away.home_goals).sum()
        draws = (home.home_goals == home.away_goals).sum() + (away.away_goals == away.home_goals).sum()
        played = len(home) + len(away)
        rows.append({
            "season": season, "team": team, "played": played,
            "wins": int(wins), "draws": int(draws), "losses": int(played - wins - draws),
            "gf": int(gf), "ga": int(ga), "gd": int(gf - ga),
            "points": int(3 * wins + draws),
        })
    return (
        pd.DataFrame(rows)
        .sort_values(["season", "points", "gd"], ascending=[True, False, False])
        .reset_index(drop=True)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    teams = pd.DataFrame({
        "team": TEAM_NAMES,
        "attack": np.round(rng.lognormal(mean=0.0, sigma=0.18, size=len(TEAM_NAMES)), 3),
        "defense": np.round(rng.lognormal(mean=0.0, sigma=0.18, size=len(TEAM_NAMES)), 3),
    })

    all_matches, all_shots = [], []
    for season in range(1, args.seasons + 1):
        m, s = generate_season(rng, season, teams)
        all_matches += m
        all_shots += s

    matches = pd.DataFrame(all_matches)
    shots = pd.DataFrame(all_shots)
    standings = build_standings(matches)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    teams.to_csv(OUT_DIR / "teams.csv", index=False)
    matches.to_csv(OUT_DIR / "matches.csv", index=False)
    shots.to_csv(OUT_DIR / "shots.csv", index=False)
    standings.to_csv(OUT_DIR / "standings.csv", index=False)

    print(f"{args.seasons} temporada(s), seed {args.seed}")
    print(f"  {len(matches)} partidos, {len(shots)} tiros -> {OUT_DIR}")
    print(f"  goles/partido: {(matches.home_goals + matches.away_goals).mean():.2f} "
          f"(real ~2.7) | xG medio por tiro: {shots.xg.mean():.3f} (real ~0.10)")
    print("\nTop 5 de la temporada 1:")
    print(standings[standings.season == 1].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
