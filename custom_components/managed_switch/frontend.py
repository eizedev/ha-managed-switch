"""The switch card: served by the integration and loaded in the frontend.

The card (built from `card/` into `www/`) works with this integration only, so it ships with it
instead of as a dashboard repository of its own. It is loaded as an extra frontend module rather
than added to the dashboards' resources: that works for dashboards in storage and in YAML mode,
leaves the user's resource list alone, and goes away with the integration.
"""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_FILE = Path(__file__).parent / "www" / "managed-switch-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILE.name}"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card and load it in the frontend, if Home Assistant runs one."""
    if "frontend" not in hass.config.components:
        return
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(CARD_FILE))])
    # The version in the URL makes browsers fetch the card again after an update.
    version = (await async_get_integration(hass, DOMAIN)).version
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
