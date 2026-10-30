"""The WebSocket command the switch card uses."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from .conftest import make_entry


async def setup(hass: HomeAssistant, *hosts: str) -> None:
    entries = [make_entry(host) for host in hosts]
    for entry in entries:
        entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entries[0].entry_id)
    await hass.async_block_till_done()


def device_id(hass: HomeAssistant, mac: str) -> str:
    [device] = dr.async_get(hass).async_get_devices(connections={(dr.CONNECTION_NETWORK_MAC, mac)})
    return device.id


async def test_ports(hass: HomeAssistant, hass_ws_client: WebSocketGenerator) -> None:
    await setup(hass, "192.0.2.1", "192.0.2.2", "192.0.2.3")
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "managed_switch/ports", "device_id": device_id(hass, "02:00:00:00:00:02")}
    )
    result = (await client.receive_json())["result"]
    switch = result["switch"]
    assert (switch["name"], switch["vendor"], switch["firmware"]) == ("switch-1", "HPE", "PD.02.22")
    assert switch["object_id"] == "1.3.6.1.4.1.11.2.3.7.11.186"
    assert switch["entities"]["poe_budget"] == "sensor.switch_1_poe_budget"
    assert switch["entities"]["port_event"] == "event.switch_1_switch_events"
    ports = {p["name"]: p for p in result["ports"]}
    assert list(ports) == ["1", "2", "3", "4", "5", "6", "7", "8", "TRK 1", "TRK 2"]
    one = ports["1"]
    assert (one["kind"], one["poe"], one["uplink"], one["trunk"]) == ("ethernet", True, False, None)
    assert one["entities"]["link"] == "binary_sensor.switch_1_port_1_link"
    assert one["entities"]["device"] == "sensor.switch_1_port_1_device"
    assert one["entities"]["received"] == "sensor.switch_1_port_1_received"  # disabled, listed
    assert ports["5"]["poe"] is False
    assert ports["7"]["uplink"] is True
    assert ports["5"]["uplink"] is True
    trunk = ports["TRK 1"]
    assert (trunk["kind"], trunk["members"]) == ("trunk", [2, 3])
    assert ports["2"]["trunk"] == trunk["if_index"]
    assert trunk["entities"]["poe"] is None


async def test_unknown_or_foreign_device(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup(hass, "192.0.2.1")
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "managed_switch/ports", "device_id": "nope"})
    reply = await client.receive_json()
    assert reply["error"]["code"] == "not_found"
    other = MockConfigEntry(domain="other")
    other.add_to_hass(hass)
    foreign = dr.async_get(hass).async_get_or_create(
        config_entry_id=other.entry_id, identifiers={("other", "x")}
    )
    await client.send_json_auto_id({"type": "managed_switch/ports", "device_id": foreign.id})
    assert (await client.receive_json())["error"]["code"] == "not_found"


async def test_unloaded_switch_or_bad_request(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup(hass, "192.0.2.1")
    client = await hass_ws_client(hass)
    switch = device_id(hass, "02:00:00:00:00:02")
    [entry] = hass.config_entries.async_entries("managed_switch")
    assert await hass.config_entries.async_unload(entry.entry_id)
    await client.send_json_auto_id({"type": "managed_switch/ports", "device_id": switch})
    assert (await client.receive_json())["error"]["code"] == "not_found"
    await client.send_json_auto_id({"type": "managed_switch/ports"})
    assert (await client.receive_json())["error"]["code"] == "invalid_format"
