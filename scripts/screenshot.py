import time
from playwright.sync_api import sync_playwright

pages = [
    ("http://localhost:3000/", "/tmp/shots2/01_livres.png"),
    ("http://localhost:3000/utilisateurs", "/tmp/shots2/02_utilisateurs.png"),
    ("http://localhost:3000/emprunts", "/tmp/shots2/03_emprunts.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    for url, out in pages:
        page.goto(url, wait_until="networkidle")
        time.sleep(0.8)
        page.screenshot(path=out, full_page=True)
        print("Capturé:", out)
    browser.close()
