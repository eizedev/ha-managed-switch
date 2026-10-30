"""Setup, entities and device locations across the three recorded switches."""

from __future__ import annotations

from aiosnmpswitch import (
    AuthProtocol,
    CommunityAuth,
    PrivProtocol,
    SnmpAuthError,
    SnmpError,
    SnmpTimeoutError,
    UsmAuth,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.managed_switch import auth_from
from custom_components.managed_switch.coordinator import get_hub

from .conftest import FakeTransport, entry_data, make_entry, state, transport


async def setup(hass: HomeAssistant, *hosts: str) -> list[MockConfigEntry]:
    entries = []
    for host in hosts:
        entry = make_entry(host)
        entry.add_to_hass(hass)
        entries.append(entry)
    # Setting up one entry loads the integration, which sets up all of its entries.
    assert await hass.config_entries.async_setup(entries[0].entry_id)
    await hass.async_block_till_done()
    return entries


ALL = ("192.0.2.1", "192.0.2.2", "192.0.2.3")


async def test_entities_and_devices(hass: HomeAssistant) -> None:
    await setup(hass, *ALL)
    devices = dr.async_get(hass)
    [switch] = devices.async_get_devices(
        connections={(dr.CONNECTION_NETWORK_MAC, "02:00:00:00:00:02")}
    )
    assert (switch.manufacturer, switch.name) == ("HPE", "switch-1")
    assert switch.model == "HPE OfficeConnect Switch 1920S 8G PPoE+ (65W) JL383A"
    assert switch.sw_version == "PD.02.22"

    assert state(hass, "binary_sensor.switch_1_port_1_link").state == "on"
    assert state(hass, "binary_sensor.switch_1_port_4_link").state == "off"
    assert state(hass, "sensor.switch_1_port_1_speed").state == "1000"
    assert state(hass, "sensor.switch_1_port_4_speed").state == "0"
    assert state(hass, "binary_sensor.switch_1_port_trk_1_link").state == "on"  # trunk
    assert hass.states.get("binary_sensor.switch_1_port_trk_3_link") is None  # no members
    assert hass.states.get("binary_sensor.switch_1_port_cpu_link") is None
    assert state(hass, "sensor.switch_1_poe_budget").state == "65"
    assert state(hass, "sensor.switch_1_poe_consumption").state == "0"
    assert state(hass, "sensor.switch_1_port_1_poe").state == "searching"
    assert state(hass, "sensor.switch_1_port_1_poe").attributes["enabled"] is True
    assert hass.states.get("sensor.switch_1_port_5_poe") is None  # no PoE on port 5
    assert hass.states.get("sensor.switch_3_poe_budget") is None  # the 1930 has no PoE
    assert state(hass, "sensor.switch_1_last_restart").state != "unknown"
    entities = er.async_get(hass)
    for disabled in ("sensor.switch_1_port_1_received", "sensor.switch_1_port_1_errors"):
        entry = entities.async_get(disabled)
        assert entry is not None
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_connected_devices(hass: HomeAssistant) -> None:
    entries = await setup(hass, *ALL)
    # LLDP neighbours by name
    assert state(hass, "sensor.switch_1_port_7_device").state == "switch-2"
    assert state(hass, "sensor.switch_3_port_1_device").state == "switch-1"
    # one device on a port, unknown to Home Assistant: its MAC address
    single = state(hass, "sensor.switch_3_port_2_device")
    assert single.attributes["device_count"] == 1
    mac = single.attributes["devices"][0]["mac"]
    assert single.state == mac
    assert (single.attributes["port"], single.attributes["if_index"]) == ("2", 2)
    assert (single.attributes["link"], single.attributes["speed"]) == (True, 100)
    down = state(hass, "sensor.switch_1_port_4_device")
    assert (down.attributes["link"], down.attributes["speed"]) == (False, 0)
    # an access point with its Wi-Fi clients
    assert state(hass, "sensor.switch_2_port_4_device").attributes["device_count"] == 9
    assert state(hass, "sensor.switch_2_port_4_device").state.endswith(" +8")
    assert state(hass, "sensor.switch_1_port_4_device").state == "unknown"  # nothing there
    # a name from another integration's device with that MAC address
    other = MockConfigEntry(domain="other")
    other.add_to_hass(hass)
    dr.async_get(hass).async_get_or_create(
        config_entry_id=other.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac)},
        name="Living room TV",
    )
    get_hub(hass).async_update()
    await hass.async_block_till_done()
    assert state(hass, "sensor.switch_3_port_2_device").state == "Living room TV"
    assert len(get_hub(hass).entries) == len(entries)


async def test_a_single_switch_locates_through_its_own_ports(hass: HomeAssistant) -> None:
    await setup(hass, "192.0.2.1")
    # without the other switches, port 7 leads to an unknown device: everything behind it
    port_7 = state(hass, "sensor.switch_1_port_7_device")
    assert port_7.attributes["device_count"] > 1
    assert port_7.attributes["devices"][0]["lldp"] is True


async def test_unload_and_remove(hass: HomeAssistant) -> None:
    entries = await setup(hass, "192.0.2.1", "192.0.2.2")
    first = entries[0]
    assert await hass.config_entries.async_unload(first.entry_id)
    assert transport("192.0.2.1").closed
    assert first.entry_id not in get_hub(hass).entries
    await hass.config_entries.async_remove(first.entry_id)
    await hass.config_entries.async_remove(entries[1].entry_id)
    await hass.async_block_till_done()
    assert get_hub(hass).entries == {}


async def test_setup_errors(hass: HomeAssistant) -> None:
    unknown = MockConfigEntry(domain="managed_switch", unique_id="x", data=entry_data("192.0.2.9"))
    unknown.add_to_hass(hass)
    await hass.config_entries.async_setup(unknown.entry_id)
    assert unknown.state is ConfigEntryState.SETUP_RETRY

    FakeTransport.errors = {"192.0.2.1": {"1.3.6.1.2.1.1": SnmpTimeoutError("no answer")}}
    timeout = make_entry("192.0.2.1")
    timeout.add_to_hass(hass)
    await hass.config_entries.async_setup(timeout.entry_id)
    assert timeout.state is ConfigEntryState.SETUP_RETRY
    assert transport("192.0.2.1").closed

    FakeTransport.errors = {"192.0.2.2": {"1.3.6.1.2.1.1": SnmpAuthError("WrongDigest")}}
    rejected = make_entry("192.0.2.2", version="3")
    rejected.add_to_hass(hass)
    await hass.config_entries.async_setup(rejected.entry_id)
    assert rejected.state is ConfigEntryState.SETUP_ERROR
    assert [f["step_id"] for f in hass.config_entries.flow.async_progress()] == ["usm"]

    FakeTransport.errors = {"192.0.2.3": {"1.3.6.1.2.1.2.2.1": SnmpError("genErr")}}
    failing = make_entry("192.0.2.3")
    failing.add_to_hass(hass)
    await hass.config_entries.async_setup(failing.entry_id)
    assert failing.state is ConfigEntryState.SETUP_RETRY


def test_auth_from_data() -> None:
    assert auth_from(entry_data("192.0.2.1")) == CommunityAuth("secret")
    assert auth_from(entry_data("192.0.2.1", "1")) == CommunityAuth("secret", version="1")
    assert auth_from(entry_data("192.0.2.1", "3")) == UsmAuth(
        "monitor", "auth-secret", "priv-secret", AuthProtocol.SHA, PrivProtocol.DES
    )
    plain = {"host": "h", "snmp_version": "3", "user": "u", "auth_key": "", "priv_key": None}
    assert auth_from(plain) == UsmAuth("u")


async def test_device_cannot_be_removed(hass: HomeAssistant) -> None:
    [entry] = await setup(hass, "192.0.2.1")
    [device] = dr.async_get(hass).async_get_devices(
        connections={(dr.CONNECTION_NETWORK_MAC, "02:00:00:00:00:02")}
    )
    from custom_components.managed_switch import async_remove_config_entry_device  # noqa: PLC0415

    assert not await async_remove_config_entry_device(hass, entry, device)


async def test_ipv6_host(hass: HomeAssistant) -> None:
    from .conftest import HOSTS, UNIQUE_IDS  # noqa: PLC0415

    HOSTS["2001:db8::1"] = HOSTS["192.0.2.1"]
    try:
        entry = MockConfigEntry(
            domain="managed_switch",
            title="switch-1",
            unique_id=UNIQUE_IDS["192.0.2.1"],
            data=entry_data("2001:db8::1"),
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        [device] = dr.async_get(hass).async_get_devices(
            connections={(dr.CONNECTION_NETWORK_MAC, "02:00:00:00:00:02")}
        )
        assert device.configuration_url == "http://[2001:db8::1]/"
    finally:
        del HOSTS["2001:db8::1"]


async def test_setup_closes_the_switch_on_any_error(hass: HomeAssistant) -> None:
    from unittest.mock import patch  # noqa: PLC0415

    entry = make_entry("192.0.2.1")
    entry.add_to_hass(hass)
    with patch.object(
        hass.config_entries, "async_forward_entry_setups", side_effect=RuntimeError("boom")
    ):
        await hass.config_entries.async_setup(entry.entry_id)
    assert transport("192.0.2.1").closed
