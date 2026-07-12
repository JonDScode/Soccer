"""Descarga datos de eventos reales de StatsBomb Open Data (github.com/statsbomb/open-data).

Sin dependencias más allá de `requests`. Por defecto baja el Mundial 2022
(competition_id=43, season_id=106): partidos + eventos de cada partido, en JSON crudo
a data/raw/statsbomb/.

Uso:
    python scripts/download_statsbomb.py                 # Mundial 2022 completo (64 partidos)
    python scripts/download_statsbomb.py --sample 5      # solo 5 partidos, para probar rápido
    python scripts/download_statsbomb.py --list          # ver competiciones disponibles
    python scripts/download_statsbomb.py --competition 11 --season 90   # La Liga 2020/21 (Messi)
"""

import argparse
import json
from pathlib import Path

import requests

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "statsbomb"


def fetch_json(url: str):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def list_competitions() -> None:
    comps = fetch_json(f"{BASE}/competitions.json")
    seen = set()
    for c in comps:
        key = (c["competition_id"], c["season_id"])
        if key in seen:
            continue
        seen.add(key)
        print(
            f"  comp {c['competition_id']:>4}  season {c['season_id']:>4}  "
            f"{c['competition_name']} — {c['season_name']}"
        )


def download(competition_id: int, season_id: int, sample: int | None) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    matches = fetch_json(f"{BASE}/matches/{competition_id}/{season_id}.json")
    matches_path = OUT_DIR / f"matches_{competition_id}_{season_id}.json"
    matches_path.write_text(json.dumps(matches, ensure_ascii=False), encoding="utf-8")
    print(f"{len(matches)} partidos -> {matches_path}")

    if sample:
        matches = matches[:sample]

    events_dir = OUT_DIR / "events"
    events_dir.mkdir(exist_ok=True)
    for i, m in enumerate(matches, 1):
        match_id = m["match_id"]
        out = events_dir / f"{match_id}.json"
        if out.exists():
            print(f"  [{i}/{len(matches)}] {match_id} ya existe, salto")
            continue
        events = fetch_json(f"{BASE}/events/{match_id}.json")
        out.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
        home, away = m["home_team"]["home_team_name"], m["away_team"]["away_team_name"]
        print(f"  [{i}/{len(matches)}] {home} vs {away}: {len(events)} eventos")

    print(f"\nListo. Eventos en {events_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competition", type=int, default=43, help="competition_id (default 43 = World Cup)")
    parser.add_argument("--season", type=int, default=106, help="season_id (default 106 = 2022)")
    parser.add_argument("--sample", type=int, default=None, help="descargar solo N partidos")
    parser.add_argument("--list", action="store_true", help="listar competiciones disponibles y salir")
    args = parser.parse_args()

    if args.list:
        list_competitions()
        return
    download(args.competition, args.season, args.sample)


if __name__ == "__main__":
    main()
