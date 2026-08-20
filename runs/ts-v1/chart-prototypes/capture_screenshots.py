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

    page.wait_for_selector("#chart-1c svg")
    bar_sections = page.locator(".bar-prototype")
    if bar_sections.count() != 3:
        raise RuntimeError(f"Expected three bar prototypes; found {bar_sections.count()}")
    if page.locator(".prototype").count() != 4:
        raise RuntimeError(f"Expected four original prototypes; found {page.locator('.prototype').count()}")
    for index, suffix in enumerate(("1a", "1b", "1c")):
        bar_sections.nth(index).screenshot(path=RUN_DIR / f"variant-{suffix}.png")

    page.set_viewport_size({"width": 390, "height": 844})
    page.reload(wait_until="networkidle")
    if page.locator("body").evaluate("el => el.scrollWidth > document.documentElement.clientWidth"):
        raise RuntimeError("Mobile layout has horizontal overflow")
    if page.locator(".bar-prototype").count() != 3:
        raise RuntimeError("Bar prototypes were lost at the mobile breakpoint")

    browser.close()

if problems:
    raise RuntimeError("Browser errors:\n" + "\n".join(problems))

print("Captured three desktop bar variants and verified mobile layout with no browser errors")
