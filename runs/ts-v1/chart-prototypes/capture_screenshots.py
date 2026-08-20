from pathlib import Path

from playwright.sync_api import sync_playwright


RUN_DIR = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8765/compute-over-time.html"


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=1.5)
    problems = []
    page.on("console", lambda message: problems.append(f"console {message.type}: {message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: problems.append(f"pageerror: {error}"))
    response = page.goto(URL, wait_until="networkidle")
    if response is None or not response.ok:
        raise RuntimeError(f"Page load failed: {None if response is None else response.status}")

    page.wait_for_selector("#chart-4 svg")
    sections = page.locator(".prototype")
    if sections.count() != 4:
        raise RuntimeError(f"Expected four prototypes; found {sections.count()}")
    for index in range(4):
        sections.nth(index).screenshot(path=RUN_DIR / f"variant-{index + 1}.png")

    page.set_viewport_size({"width": 390, "height": 844})
    page.reload(wait_until="networkidle")
    if page.locator("body").evaluate("el => el.scrollWidth > document.documentElement.clientWidth"):
        raise RuntimeError("Mobile layout has horizontal overflow")
    page.locator(".prototype").nth(2).screenshot(path=RUN_DIR / "variant-3-mobile.png")

    browser.close()

if problems:
    raise RuntimeError("Browser errors:\n" + "\n".join(problems))

print("Captured four desktop variants and one mobile QA screenshot with no browser errors")
