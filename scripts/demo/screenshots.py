r"""Take the documentation's screenshots from a running demo instance (run.py).

    uv run --no-project --with-requirements scripts/demo/requirements.txt \\
        python scripts/demo/screenshots.py [--browser msedge|chrome|chromium] [--scheme dark|light]

It shows the setup dialog, a switch's device page and the example dashboard, and saves the
pictures to docs/assets/screenshots/. With --browser chromium, run
`playwright install chromium` once; msedge and chrome use an installed browser.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import Locator, Page, async_playwright
import yaml

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "docs" / "assets" / "screenshots"
BASE = "http://127.0.0.1:8126"
DASHBOARD = HERE.parents[1] / "docs" / "assets" / "example-dashboard.yaml"
HASS = "document.querySelector('home-assistant').hass"


async def shoot(page: Page, name: str, target: Locator | None = None) -> None:
    """Save the page, or one element of it, as docs/assets/screenshots/<name>.png."""
    await page.wait_for_timeout(1500)  # let animations and values settle
    path = OUT / f"{name}.png"
    if target is not None:
        await target.screenshot(path=path)
    else:
        await page.screenshot(path=path)
    print("saved", path.relative_to(HERE.parents[1]), flush=True)


async def login(page: Page) -> None:
    """Log in through the login page, as a user would."""
    await page.goto(f"{BASE}/")
    await page.get_by_label("Username").fill("demo")
    await page.get_by_role("textbox", name="Password").fill("demo")
    await page.keyboard.press("Enter")
    await page.wait_for_url("**/home/**", timeout=60000)
    confirm = page.get_by_role("button", name="Confirm")  # the new HTTP settings, once
    await page.wait_for_timeout(2000)
    if await confirm.count():
        await confirm.first.click()


async def setup_dialog(page: Page) -> None:
    """Photograph the setup dialog's first two steps (SNMPv3); close it before it is submitted."""
    await page.goto(f"{BASE}/config/integrations/dashboard/add?domain=managed_switch")
    dialog = page.get_by_role("dialog")
    await page.get_by_role("button", name="OK", exact=True).click()  # "Set up ...?"
    await page.wait_for_timeout(3000)
    fields = page.locator("dialog-data-entry-flow ha-form input")
    await fields.nth(0).fill("192.0.2.10")
    await shoot(page, "setup-connection", dialog)
    await page.get_by_role("button", name="Submit", exact=True).last.click()
    await page.wait_for_timeout(2500)
    fields = page.locator("dialog-data-entry-flow ha-form input")
    await fields.nth(0).fill("monitor")
    await shoot(page, "setup-snmpv3", dialog)
    await page.keyboard.press("Escape")


async def main(args: argparse.Namespace) -> None:
    """Open a browser and take the tour."""
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            channel=None if args.browser == "chromium" else args.browser
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,
            color_scheme=args.scheme,
            locale="en-US",
        )
        page = await context.new_page()
        page.on("console", lambda m: print("console:", m.text) if m.type == "error" else None)
        try:
            await tour(page, args.card)
        except Exception:
            await page.screenshot(path=OUT / "failed.png")  # where it stopped; not committed
            raise
        finally:
            await browser.close()


async def tour(page: Page, card_bundle: Path | None) -> None:
    """Photograph the documented pages."""
    await login(page)
    await setup_dialog(page)

    device_id = await page.evaluate(
        f"async () => {HASS}.entities['event.switch_1_switch_events']?.device_id"
    )
    await page.goto(f"{BASE}/config/devices/device/{device_id}")
    await shoot(page, "device-switch")

    await page.evaluate(
        f"""async (config) => {{
            await {HASS}.callWS({{type: 'lovelace/dashboards/create', url_path: 'switch-ports',
                title: 'Switches', icon: 'mdi:switch', mode: 'storage', require_admin: false,
                show_in_sidebar: true}});
            await {HASS}.callWS({{type: 'lovelace/config/save', url_path: 'switch-ports', config}});
        }}""",
        yaml.safe_load(DASHBOARD.read_text()),
    )
    await page.set_viewport_size({"width": 1700, "height": 1250})
    await page.goto(f"{BASE}/switch-ports/ports")
    await shoot(page, "dashboard")

    if card_bundle is not None:
        await card(page, card_bundle)


async def card(page: Page, bundle: Path) -> None:
    """Load the switch card (a build of managed-switch-card) and photograph it for each switch."""
    target = HERE / ".config" / "www" / "managed-switch-card.js"  # run.py creates www/
    await asyncio.to_thread(target.write_bytes, await asyncio.to_thread(bundle.read_bytes))
    devices = await page.evaluate(
        f"""async () => ['switch_1', 'switch_2', 'switch_3'].map(
            (s) => {HASS}.entities[`event.${{s}}_switch_events`]?.device_id)"""
    )
    config = {
        "views": [
            {
                "title": "Card",
                "path": "card",
                "type": "masonry",
                "cards": [
                    {"type": "custom:managed-switch-card", "device_id": d, "show_rates": False}
                    for d in devices
                ],
            }
        ]
    }
    await page.evaluate(
        f"""async (config) => {{
            await {HASS}.callWS({{type: 'lovelace/resources/create', res_type: 'module',
                url: '/local/managed-switch-card.js?v=' + Date.now()}});
            await {HASS}.callWS({{type: 'lovelace/dashboards/create', url_path: 'switch-card',
                title: 'Switch card', icon: 'mdi:switch', mode: 'storage', require_admin: false,
                show_in_sidebar: true}});
            await {HASS}.callWS({{type: 'lovelace/config/save', url_path: 'switch-card', config}});
        }}""",
        config,
    )
    await page.set_viewport_size({"width": 1280, "height": 1000})
    await page.goto(f"{BASE}/switch-card/card")
    await page.reload()
    await shoot(page, "card")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else None)
    parser.add_argument("--browser", default="msedge", choices=["msedge", "chrome", "chromium"])
    parser.add_argument("--scheme", default="light", choices=["dark", "light"])
    parser.add_argument(
        "--card", type=Path, help="a build of managed-switch-card to photograph as well"
    )
    asyncio.run(main(parser.parse_args()))
