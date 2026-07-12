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
    """Eventos crudos de un partido, aplanados con json_normalize (sep='_')."""
    events = json.load(open(RAW / "events" / f"{match_id}.json", encoding="utf-8"))
    return pd.json_normalize(events, sep="_")
