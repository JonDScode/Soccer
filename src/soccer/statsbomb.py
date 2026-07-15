"""Carga de datos de StatsBomb Open Data ya descargados en data/raw/statsbomb/."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw" / "statsbomb"
PROCESSED = ROOT / "data" / "processed"


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
        import requests
        url = ("https://raw.githubusercontent.com/statsbomb/open-data/master/"
               f"data/events/{match_id}.json")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        events = r.json()
    return pd.json_normalize(events, sep="_")
