"""Ingesta de los resultados finales del Mundial 2026 desde football-data.org.

Los resultados de partidos son hechos públicos (sin problema de licencia).
Se añaden a data/processed/results_matches.parquet con el mismo esquema que
la base Fjelstul, para que 'FIFA World Cup → 2026' aparezca en el dashboard
con su cuadro de llaves y banderas como cualquier otro Mundial, sin depender
de la API en runtime.

Requiere FOOTBALL_DATA_TOKEN en .env o en el entorno.

Uso:
    python scripts/ingest_wc2026_results.py
"""

import os
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "results_matches.parquet"

STAGE_MAP = {
    "GROUP_STAGE": "group stage", "LAST_32": "round of 32", "LAST_16": "round of 16",
    "QUARTER_FINALS": "quarter-finals", "SEMI_FINALS": "semi-finals",
    "THIRD_PLACE": "third-place match", "FINAL": "final",
}


def _token() -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ["FOOTBALL_DATA_TOKEN"]


def main() -> None:
    r = requests.get("https://api.football-data.org/v4/competitions/WC/matches",
                     headers={"X-Auth-Token": _token()}, timeout=60)
    r.raise_for_status()
    rows = []
    for m in r.json()["matches"]:
        if m["status"] != "FINISHED":
            continue
        pens = m["score"].get("penalties") or {}
        rows.append({
            "competition": "FIFA World Cup",
            "season": "2026",
            "stage": STAGE_MAP.get(m["stage"], m["stage"].lower()),
            "date": m["utcDate"][:10],
            "home_team": m["homeTeam"]["name"],
            "away_team": m["awayTeam"]["name"],
            "home_score": m["score"]["fullTime"]["home"],
            "away_score": m["score"]["fullTime"]["away"],
            "pen_home": pens.get("home"),
            "pen_away": pens.get("away"),
        })
    new = pd.DataFrame(rows)

    old = pd.read_parquet(OUT)
    old = old[~((old.competition == "FIFA World Cup") & (old.season == "2026"))]
    combo = pd.concat([old, new], ignore_index=True)
    combo.to_parquet(OUT, index=False)
    print(f"{len(new)} partidos del Mundial 2026 ingresados "
          f"({int(new.pen_home.notna().sum())} con tanda) -> {OUT}")
    final = new[new.stage == "final"].iloc[0]
    print(f"Final: {final.home_team} {final.home_score}-{final.away_score} {final.away_team}")


if __name__ == "__main__":
    main()
