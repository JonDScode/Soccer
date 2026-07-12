"""Convierte los JSON crudos de StatsBomb en tablas Parquet para el dashboard.

Produce en data/processed/:
- matches.parquet  — un partido por fila (equipos, marcador, fase, fecha)
- shots.parquet    — un tiro por fila con coordenadas, xG y resultado

Uso:
    python scripts/preprocess_statsbomb.py
"""

import json
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "statsbomb"
OUT = Path(__file__).resolve().parent.parent / "data" / "processed"

COMPETITION_ID, SEASON_ID = 43, 106  # World Cup 2022


def build_matches() -> pd.DataFrame:
    matches = json.load(open(RAW / f"matches_{COMPETITION_ID}_{SEASON_ID}.json", encoding="utf-8"))
    rows = [{
        "match_id": m["match_id"],
        "date": m["match_date"],
        "stage": m["competition_stage"]["name"],
        "home_team": m["home_team"]["home_team_name"],
        "away_team": m["away_team"]["away_team_name"],
        "home_score": m["home_score"],
        "away_score": m["away_score"],
    } for m in matches]
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def build_shots(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, m in matches.iterrows():
        path = RAW / "events" / f"{m.match_id}.json"
        if not path.exists():
            continue
        events = json.load(open(path, encoding="utf-8"))
        for e in events:
            if e["type"]["name"] != "Shot":
                continue
            rows.append({
                "match_id": m.match_id,
                "team": e["team"]["name"],
                "player": e["player"]["name"],
                "minute": e["minute"],
                "period": e["period"],
                "x": e["location"][0],
                "y": e["location"][1],
                "xg": e["shot"]["statsbomb_xg"],
                "outcome": e["shot"]["outcome"]["name"],
                "body_part": e["shot"].get("body_part", {}).get("name"),
                "shot_type": e["shot"].get("type", {}).get("name"),
                "is_goal": e["shot"]["outcome"]["name"] == "Goal",
            })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matches = build_matches()
    shots = build_shots(matches)
    n_events = matches.match_id.isin(shots.match_id.unique()).sum()
    matches.to_parquet(OUT / "matches.parquet", index=False)
    shots.to_parquet(OUT / "shots.parquet", index=False)
    print(f"{len(matches)} partidos ({n_events} con eventos descargados), {len(shots)} tiros")
    print(f"-> {OUT / 'matches.parquet'}\n-> {OUT / 'shots.parquet'}")


if __name__ == "__main__":
    main()
