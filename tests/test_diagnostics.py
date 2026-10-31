"""The diagnostics download holds no credentials, addresses or names."""

from __future__ import annotations

import json

from homeassistant.core import HomeAssistant

from custom_components.managed_switch.diagnostics import async_get_config_entry_diagnostics

from .conftest import make_entry


async def test_diagnostics(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1", version="3")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(result)
    for secret in ("auth-secret", "priv-secret", "monitor", "192.0.2.1", "02:00", "switch-1"):
        assert secret not in text
    assert result["address_table"] == 39
    assert result["poe"] == {"supplies": 1, "ports": 4}
    assert result["lldp"]["neighbours"] == 2
    assert result["interfaces"]["ports_with_entities"] == 10  # 8 ports, 2 trunks
    assert result["located_devices"] > 0


async def test_diagnostics_without_lldp_and_poe(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.3")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entry.runtime_data.slow.data.lldp = None
    entry.runtime_data.slow.data.poe = None
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["lldp"] == {"chassis_id_subtype": None, "local_ports": 0, "neighbours": 0}
    assert result["poe"] == {"supplies": 0, "ports": 0}
    assert result["temperatures"] == [
        {"index": 68420481, "celsius": 54.0, "status": 1},
        {"index": 68420482, "celsius": 55.0, "status": 1},
    ]
    assert "PHY" not in str(result)  # sensor names stay out, as all names do
