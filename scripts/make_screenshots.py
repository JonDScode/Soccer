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

        # 3. Match momentum (xT): captura del elemento del gráfico, completo.
        # OJO: streamlit deja en el DOM los charts de las pestañas ocultas, así
        # que el índice es global: 0-1 son de la pestaña Torneo (mapa, goleadores)
        # y en Partido a fondo siguen 2 carrera de xG, 3 posesión, 4 momentum
        charts = page.locator('[data-testid="stPlotlyChart"]')
        charts.nth(4).scroll_into_view_if_needed()
        page.wait_for_timeout(2500)
        charts.nth(4).screenshot(path=OUT / "03_momentum_xt.png")
        print("3/5 momentum xT")

        # 4. Shot map: la imagen del pyplot completa, sin recortes
        # (las stImage del tab son: 0 shot map, 1-2 redes, 3-4 mapas del jugador)
        imgs = page.locator('[data-testid="stImage"] img')
        imgs.nth(0).scroll_into_view_if_needed()
        page.wait_for_timeout(2000)
        imgs.nth(0).screenshot(path=OUT / "04_shot_map.png")
        print("4/5 shot map")

        # 5. Las dos redes de pases: el bloque horizontal que las contiene
        block = (page.locator('[data-testid="stHorizontalBlock"]')
                 .filter(has=page.locator('[data-testid="stImage"]')).first)
        block.scroll_into_view_if_needed()
        page.wait_for_timeout(2000)
        block.screenshot(path=OUT / "05_redes_de_pases.png")
        print("5/5 redes de pases")

        browser.close()
    print(f"Listo -> {OUT}")


if __name__ == "__main__":
    main()
