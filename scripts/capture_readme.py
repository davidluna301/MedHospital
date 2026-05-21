"""
Genera capturas para el README (producción Render o local).

  python scripts/capture_readme.py
  python scripts/capture_readme.py --base-url http://127.0.0.1:8000
"""
import argparse
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_BASE = "https://consultamed.onrender.com"
ADMIN_EMAIL = "admin@consultamed.local"
ADMIN_PASSWORD = "Admin123!"
OUT = Path(__file__).resolve().parent.parent / "capturas"

PAGES_AFTER_LOGIN = [
    ("03_panel_admin.png", "/panel/", "chartEspecialidad"),
    ("04_citas_listado.png", "/citas/", None),
    ("05_especialidades.png", "/especialidades/", None),
    ("06_medicos.png", "/medicos/", None),
    ("07_pacientes.png", "/pacientes/", None),
    ("08_historias_clinicas.png", "/historias/", None),
    ("09_horarios_disponibilidad.png", "/horarios/", None),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.set_default_timeout(120_000)

        page.goto(f"{base}/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(OUT / "01_landing.png"), full_page=True)

        page.goto(f"{base}/cuentas/iniciar-sesion/", wait_until="domcontentloaded")
        page.screenshot(path=str(OUT / "02_login.png"), full_page=True)

        page.fill('input[name="username"]', ADMIN_EMAIL)
        page.fill('input[name="password"]', ADMIN_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url(re.compile(r".*/panel/?"), timeout=120_000)

        for filename, path, chart_id in PAGES_AFTER_LOGIN:
            page.goto(f"{base}{path}", wait_until="domcontentloaded")
            if chart_id:
                page.wait_for_selector(f"#{chart_id}", state="visible", timeout=60_000)
                page.wait_for_timeout(2500)
            else:
                page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / filename), full_page=True)

        browser.close()

    print(f"Capturas guardadas en {OUT}")


if __name__ == "__main__":
    main()
