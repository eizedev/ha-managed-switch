"""The switch card ships with the integration and loads in the frontend."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.managed_switch.const import DOMAIN
from custom_components.managed_switch.frontend import CARD_FILE, CARD_URL

MANIFEST = Path(CARD_FILE).parents[1] / "manifest.json"


async def test_card_served_and_loaded(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    assert await async_setup_component(hass, "http", {})
    hass.config.components.add("frontend")  # the real one needs the frontend package
    with patch("custom_components.managed_switch.frontend.add_extra_js_url") as add:
        assert await async_setup_component(hass, DOMAIN, {})
    version = json.loads(MANIFEST.read_text())["version"]
    add.assert_called_once_with(hass, f"{CARD_URL}?v={version}")

    response = await (await hass_client()).get(CARD_URL)
    assert response.status == 200
    assert "managed-switch-card" in await response.text()


async def test_without_frontend(hass: HomeAssistant) -> None:
    with patch("custom_components.managed_switch.frontend.add_extra_js_url") as add:
        assert await async_setup_component(hass, DOMAIN, {})
    add.assert_not_called()


def test_bundle_has_the_integration_version() -> None:
    """card/build.mjs takes the version from the manifest; a stale bundle fails here."""
    version = json.loads(MANIFEST.read_text())["version"]
    assert f"MANAGED-SWITCH-CARD %c {version} " in CARD_FILE.read_text()
