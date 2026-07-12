"""Descarga la Fjelstul World Cup Database: resultados completos de TODOS los
Mundiales masculinos 1930-2022 (1.248 partidos con fase, fecha y penales).

Fuente: github.com/jfjelstul/worldcup (licencia CC-BY 4.0).
Complementa a StatsBomb: Fjelstul da los cuadros completos de cada Mundial;
StatsBomb da el event data (tiro a tiro) solo de algunos torneos.

Uso:
    python scripts/download_results.py
"""

from pathlib import Path

import requests

URL = "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/matches.csv"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "fjelstul_matches.csv"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    OUT.write_bytes(r.content)
    print(f"{len(r.content):,} bytes -> {OUT}")


if __name__ == "__main__":
    main()
