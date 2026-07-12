"""Bandera por selección nacional (nombres tal como aparecen en StatsBomb).

Devuelve una etiqueta <img> con la bandera servida por flagcdn.com (Flagpedia),
porque los emojis de bandera no se renderizan en Windows. Cubre los participantes
de los Mundiales 1958-2023 (M y F) y la Euro 2024. Selecciones desaparecidas
usan la bandera del estado sucesor más cercano.
"""

ISO = {
    "Albania": "al", "Algeria": "dz", "Angola": "ao", "Argentina": "ar",
    "Australia": "au", "Austria": "at", "Belgium": "be", "Bolivia": "bo",
    "Bosnia and Herzegovina": "ba", "Brazil": "br", "Bulgaria": "bg",
    "Cameroon": "cm", "Canada": "ca", "Chile": "cl", "China PR": "cn",
    "Colombia": "co", "Costa Rica": "cr", "Croatia": "hr", "Cuba": "cu",
    "Czech Republic": "cz", "Czechoslovakia": "cz", "Denmark": "dk",
    "East Germany": "de", "German DR": "de", "Ecuador": "ec", "Egypt": "eg",
    "El Salvador": "sv", "England": "gb-eng", "France": "fr", "Georgia": "ge",
    "Germany": "de", "Ghana": "gh", "Greece": "gr", "Haiti": "ht",
    "Honduras": "hn", "Hungary": "hu", "Iceland": "is", "Iran": "ir",
    "Iraq": "iq", "Israel": "il", "Italy": "it", "Ivory Coast": "ci",
    "Jamaica": "jm", "Japan": "jp", "Jordan": "jo", "Korea Republic": "kr",
    "Kuwait": "kw", "Mexico": "mx", "Morocco": "ma", "Netherlands": "nl",
    "New Zealand": "nz", "Nigeria": "ng", "North Korea": "kp",
    "Northern Ireland": "gb-nir", "Norway": "no", "Panama": "pa",
    "Paraguay": "py", "Peru": "pe", "Philippines": "ph", "Poland": "pl",
    "Portugal": "pt", "Qatar": "qa", "Republic of Ireland": "ie",
    "Romania": "ro", "Russia": "ru", "Saudi Arabia": "sa",
    "Scotland": "gb-sct", "Senegal": "sn", "Serbia": "rs", "Slovakia": "sk",
    "Slovenia": "si", "South Africa": "za", "South Korea": "kr",
    "Soviet Union": "ru", "Spain": "es", "Sweden": "se", "Switzerland": "ch",
    "Thailand": "th", "Togo": "tg", "Trinidad and Tobago": "tt",
    "Tunisia": "tn", "Turkey": "tr", "Ukraine": "ua",
    "United Arab Emirates": "ae", "United States": "us", "Uruguay": "uy",
    "Vietnam": "vn", "Wales": "gb-wls", "West Germany": "de",
    "Yugoslavia": "rs", "Zaire": "cd", "Zambia": "zm",
}


def flag(team: str, width: int = 18) -> str:
    """Etiqueta <img> con la bandera del equipo, o cadena vacía si no hay mapeo.

    Las selecciones femeninas de StatsBomb llevan sufijo ("Spain Women's",
    "Zambia W") — se recorta antes de buscar.
    """
    for suffix in (" Women's", " W"):
        if team.endswith(suffix):
            team = team[: -len(suffix)]
            break
    code = ISO.get(team)
    if not code:
        return ""
    return (f'<img src="https://flagcdn.com/w40/{code}.png" width="{width}" '
            f'style="vertical-align:-3px;border-radius:2px">')
