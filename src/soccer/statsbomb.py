"""Carga e ingesta de datos de StatsBomb Open Data.

Los loaders leen los Parquet de data/processed/. La ingesta incremental
(download_and_ingest) descarga un torneo del repo abierto de StatsBomb y lo
AÑADE a los Parquet existentes — pensada para el botón del dashboard, y
funciona igual en local que en Streamlit Cloud (donde no hay data/raw).
"""

import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw" / "statsbomb"
PROCESSED = ROOT / "data" / "processed"
BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


def load_matches() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "matches.parquet")


def load_shots() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "shots.parquet")


def load_nicknames() -> dict:
    """Mapa nombre completo → apodo reconocible ('...Messi Cuccittini' → 'Lionel Messi')."""
    players = pd.read_parquet(PROCESSED / "players.parquet")
    return dict(zip(players.player, players.nickname))


def load_events(match_id: int) -> pd.DataFrame:
    """Eventos crudos de un partido, aplanados con json_normalize (sep='_').

    Si el JSON no está en disco (p. ej. en un deploy sin data/raw), se descarga
    al vuelo desde el repo de StatsBomb Open Data.
    """
    path = RAW / "events" / f"{match_id}.json"
    if path.exists():
        events = json.load(open(path, encoding="utf-8"))
    else:
        events = _fetch(f"{BASE}/events/{match_id}.json")
    return pd.json_normalize(events, sep="_")


# ---------- Ingesta incremental (botón "Agregar torneo" del dashboard) ----------

def _fetch(url: str):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def list_competitions() -> pd.DataFrame:
    """Catálogo del open data: una fila por (competición, temporada)."""
    comps = pd.DataFrame(_fetch(f"{BASE}/competitions.json"))
    return (comps[["competition_id", "season_id", "competition_name", "season_name"]]
            .drop_duplicates(subset=["competition_id", "season_id"]))


def _merge_parquet(path: Path, new_df: pd.DataFrame, subset) -> None:
    old = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    combo = pd.concat([old, new_df], ignore_index=True)
    combo = combo.drop_duplicates(subset=subset, keep="first")
    combo.to_parquet(path, index=False)


def download_and_ingest(competition_id: int, season_id: int, progress=None) -> int:
    """Descarga un torneo y lo añade a los Parquet. Devuelve partidos añadidos.

    Idempotente: los partidos ya presentes se saltan. `progress(i, n, texto)`
    permite reportar avance a la UI.
    """
    matches = _fetch(f"{BASE}/matches/{competition_id}/{season_id}.json")
    existing = (set(load_matches().match_id)
                if (PROCESSED / "matches.parquet").exists() else set())
    todo = [m for m in matches if m["match_id"] not in existing]
    if not todo:
        return 0

    events_dir, lineups_dir = RAW / "events", RAW / "lineups"
    events_dir.mkdir(parents=True, exist_ok=True)
    lineups_dir.mkdir(parents=True, exist_ok=True)
    (RAW / f"matches_{competition_id}_{season_id}.json").write_text(
        json.dumps(matches, ensure_ascii=False), encoding="utf-8")

    m_rows, s_rows, p_rows = [], [], {}
    for i, m in enumerate(todo, 1):
        match_id = m["match_id"]
        if progress:
            progress(i, len(todo),
                     f"{m['home_team']['home_team_name']} vs {m['away_team']['away_team_name']}")
        events = _fetch(f"{BASE}/events/{match_id}.json")
        lineups = _fetch(f"{BASE}/lineups/{match_id}.json")
        (events_dir / f"{match_id}.json").write_text(
            json.dumps(events, ensure_ascii=False), encoding="utf-8")
        (lineups_dir / f"{match_id}.json").write_text(
            json.dumps(lineups, ensure_ascii=False), encoding="utf-8")

        m_rows.append({
            "match_id": match_id,
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
            "has_events": True,
        })
        for e in events:
            if e["type"]["name"] != "Shot":
                continue
            s_rows.append({
                "match_id": match_id,
                "competition_id": m["competition"]["competition_id"],
                "season_id": m["season"]["season_id"],
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
                "under_pressure": bool(e.get("under_pressure", False)),
                "first_time": bool(e["shot"].get("first_time", False)),
                "one_on_one": bool(e["shot"].get("one_on_one", False)),
                "open_goal": bool(e["shot"].get("open_goal", False)),
                "technique": e["shot"].get("technique", {}).get("name"),
                "play_pattern": e.get("play_pattern", {}).get("name"),
            })
        for team in lineups:
            for p in team["lineup"]:
                p_rows[p["player_name"]] = {
                    "player": p["player_name"],
                    "nickname": p.get("player_nickname") or p["player_name"],
                    "team": team["team_name"],
                    "jersey": p.get("jersey_number"),
                }

    _merge_parquet(PROCESSED / "matches.parquet", pd.DataFrame(m_rows), ["match_id"])
    _merge_parquet(PROCESSED / "shots.parquet", pd.DataFrame(s_rows),
                   ["match_id", "team", "minute", "x", "y"])
    _merge_parquet(PROCESSED / "players.parquet", pd.DataFrame(p_rows.values()), ["player"])
    return len(m_rows)
