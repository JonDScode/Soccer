"""Ajusta la superficie de valor xT con TODOS los eventos descargados y la
guarda en models/xt_grid.json (artefacto pequeño, versionado en git).

Uso:
    python scripts/fit_xt.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from soccer import xt  # noqa: E402

EVENTS = ROOT / "data" / "raw" / "statsbomb" / "events"


def main() -> None:
    moves_all, shots_all = [], []
    files = sorted(EVENTS.glob("*.json"))
    for i, path in enumerate(files, 1):
        events = pd.json_normalize(json.load(open(path, encoding="utf-8")), sep="_")
        m = xt._moves_from_events(events)
        if not m.empty:
            moves_all.append(m[["x", "y", "ex", "ey"]])
        sh = events[(events.type_name == "Shot") & (events.period < 5)
                    & (events.shot_type_name != "Penalty")]
        if len(sh):
            s = pd.DataFrame(sh.location.tolist(), columns=["x", "y"], index=sh.index)
            s["is_goal"] = (sh.shot_outcome_name == "Goal").values
            shots_all.append(s)
        if i % 50 == 0:
            print(f"  {i}/{len(files)} partidos procesados")

    moves = pd.concat(moves_all, ignore_index=True)
    shots = pd.concat(shots_all, ignore_index=True)
    print(f"{len(moves):,} movimientos (pases+conducciones), {len(shots):,} tiros")

    V = xt.fit_grid(moves, shots)
    path = xt.save_grid(V)
    print(f"Superficie xT {V.shape} -> {path}")
    print(f"  valor máximo (frente al arco): {V.max():.3f}")
    print(f"  valor en campo propio (esquina defensiva): {V[0, 0]:.4f}")


if __name__ == "__main__":
    main()
