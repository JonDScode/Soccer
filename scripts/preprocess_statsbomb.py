"""Convierte los JSON crudos de StatsBomb en tablas Parquet para el dashboard.

Escanea TODOS los torneos descargados (cada matches_<comp>_<season>.json en
data/raw/statsbomb/) y produce en data/processed/:
- matches.parquet  — un partido por fila, con torneo y temporada
- shots.parquet    — un tiro por fila con coordenadas, xG y resultado
- players.parquet  — mapa jugador → apodo reconocible

Uso:
    python scripts/preprocess_statsbomb.py
"""

import json
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "statsbomb"
OUT = Path(__file__).resolve().parent.parent / "data" / "processed"


def build_matches() -> pd.DataFrame:
    rows = []
    for path in sorted(RAW.glob("matches_*.json")):
        for m in json.load(open(path, encoding="utf-8")):
            rows.append({
                "match_id": m["match_id"],
                "competition_id": m["competition"]["competition_id"],
                "season_id": m["season"]["season_id"],
                "competition": m["competition"]["competition_name"],
                "season": m["season"]["season_name"],
                "date": m["match_date"],
                "stage": m["competition_stage"]["name"],
                "home_team": m["home_team"]["home_team_name"],
                "away_team": m["away_team"]["away_team_name"],
                "home_score": m["home_score"],
                "away_score": m["away_score"],
            })
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
                "competition_id": m.competition_id,
                "season_id": m.season_id,
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
                # features para el modelo de xG propio (Fase 2)
                "under_pressure": bool(e.get("under_pressure", False)),
                "first_time": bool(e["shot"].get("first_time", False)),
                "one_on_one": bool(e["shot"].get("one_on_one", False)),
                "open_goal": bool(e["shot"].get("open_goal", False)),
                "technique": e["shot"].get("technique", {}).get("name"),
                "play_pattern": e.get("play_pattern", {}).get("name"),
            })
    return pd.DataFrame(rows)


def build_players() -> pd.DataFrame:
    """Mapa jugador → apodo (el nombre reconocible: 'Lionel Messi', no 'Cuccittini')."""
    rows = {}
    for path in (RAW / "lineups").glob("*.json"):
        for team in json.load(open(path, encoding="utf-8")):
            for p in team["lineup"]:
                rows[p["player_name"]] = {
                    "player": p["player_name"],
                    "nickname": p.get("player_nickname") or p["player_name"],
                    "team": team["team_name"],
                    "jersey": p.get("jersey_number"),
                }
    return pd.DataFrame(rows.values())


def build_results() -> pd.DataFrame:
    """Resultados completos de todos los Mundiales 1930-2022 (Fjelstul database)."""
    path = RAW.parent / "fjelstul_matches.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    pens = df.penalty_shootout == 1
    # El dataset trae masculinos y femeninos; el nombre del torneo los distingue.
    # Se usan los mismos nombres de competición que StatsBomb para que el
    # selector una ambas fuentes.
    comp = df.tournament_name.str.contains("Women").map(
        {True: "Women's World Cup", False: "FIFA World Cup"})
    return pd.DataFrame({
        "competition": comp,
        "season": df.tournament_name.str.extract(r"^(\d{4})")[0],
        "stage": df.stage_name,
        "date": df.match_date,
        "home_team": df.home_team_name,
        "away_team": df.away_team_name,
        "home_score": df.home_team_score,
        "away_score": df.away_team_score,
        "pen_home": df.home_team_score_penalties.where(pens),
        "pen_away": df.away_team_score_penalties.where(pens),
    })


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matches = build_matches()
    shots = build_shots(matches)
    players = build_players()
    results = build_results()
    with_events = matches.match_id.isin(shots.match_id.unique())
    matches["has_events"] = with_events
    matches.to_parquet(OUT / "matches.parquet", index=False)
    shots.to_parquet(OUT / "shots.parquet", index=False)
    players.to_parquet(OUT / "players.parquet", index=False)
    if not results.empty:
        results.to_parquet(OUT / "results_matches.parquet", index=False)

    print(f"{len(matches)} partidos ({with_events.sum()} con eventos), "
          f"{len(shots)} tiros, {len(players)} jugadores")
    print(f"Resultados Fjelstul: {len(results)} partidos, "
          f"{results.season.nunique() if not results.empty else 0} Mundiales "
          f"({int(results.pen_home.notna().sum()) if not results.empty else 0} con tanda de penales)")
    resumen = matches.groupby(["competition", "season"]).size()
    print(resumen.to_string())


if __name__ == "__main__":
    main()
