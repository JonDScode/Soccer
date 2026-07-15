"""Capturas del dashboard para publicaciones (LinkedIn, README).

Requiere la app corriendo en localhost:8501 y playwright con chromium:
    pip install playwright && python -m playwright install chromium
    streamlit run app/streamlit_app.py   (en otra terminal)
    python scripts/make_screenshots.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "reports" / "linkedin"
URL = "http://localhost:8501"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 860},
                                device_scale_factor=2)
        page.goto(URL)
        page.wait_for_timeout(12000)  # streamlit renderiza por websocket

        # 1. Cuadro de llaves del Mundial 2022 (pestaña Torneo, vista por defecto)
        page.get_by_text("Fase eliminatoria").first.scroll_into_view_if_needed()
        page.wait_for_timeout(1500)
        page.screenshot(path=OUT / "01_llaves_2022.png")
        print("1/4 llaves 2022")

        # 2. Partido a fondo: la final con carrera de xG (bajamos hasta el gráfico)
        page.get_by_role("tab").filter(has_text="Partido a fondo").click()
        page.wait_for_timeout(9000)
        scroll = "document.querySelector('[data-testid=\"stMain\"]').scrollTo(0, {y})"
        page.evaluate(scroll.format(y=620))
        page.wait_for_timeout(1500)
        page.screenshot(path=OUT / "02_final_xg_race.png")
        print("2/4 final + carrera de xG")

        # 3. Match momentum (xT) — el título vive dentro del SVG de plotly,
        # así que anclamos en el caption de texto que está debajo
        page.get_by_text("Modelo xT (expected threat)").first.scroll_into_view_if_needed()
        page.wait_for_timeout(2500)
        page.screenshot(path=OUT / "03_momentum_xt.png")
        print("3/4 momentum xT")

        # 4. Red de pases + posesión (scroll intermedio)
        page.get_by_text("Redes de pases").first.scroll_into_view_if_needed()
        page.wait_for_timeout(2000)
        page.screenshot(path=OUT / "04_redes_de_pases.png")
        print("4/4 redes de pases")

        browser.close()
    print(f"Listo -> {OUT}")


if __name__ == "__main__":
    main()
