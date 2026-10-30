"""Edge cases of the entities: missing values, switches without an identity or vendor."""

from __future__ import annotations

from aiosnmpswitch import Interface, Lldp, LldpRemote, Poe, PsePort, SystemInfo
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.managed_switch.coordinator import get_hub
from custom_components.managed_switch.devices import Connected, connected, summary
from custom_components.managed_switch.entity import firmware, model, vendor

from .conftest import make_entry, state, transport

OPER = "1.3.6.1.2.1.2.2.1.8"


def system(descr: str | None, object_id: str | None) -> SystemInfo:
    return SystemInfo(descr, object_id, None, None, None, None)


def test_vendor_model_firmware() -> None:
    assert vendor(system(None, "1.3.6.1.4.1.4526.100")) == "Netgear"
    assert vendor(system(None, "1.3.6.1.4.1.99999.1")) is None
    assert vendor(system(None, "1.3.6.1.4.1.x")) is None
    assert vendor(system(None, None)) is None
    assert model(system("GS108T", None)) == "GS108T"
    assert model(system(None, None)) is None
    assert firmware(system("GS108T", None)) is None
    assert firmware(system("GS108T, ", None)) is None
    assert firmware(system("GS108T, 7.0.1", None)) == "7.0.1"


def test_summary() -> None:
    assert summary([]) is None
    assert summary([Connected(None, None)]) == "?"
    assert (
        summary([Connected("02:00:00:00:00:01", None), Connected(None, "b")])
        == "02:00:00:00:00:01 +1"
    )


async def setup(hass: HomeAssistant, host: str = "192.0.2.1") -> object:
    entry = make_entry(host)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_unknown_link_and_vanished_port(hass: HomeAssistant) -> None:
    entry = await setup(hass)
    fake = transport("192.0.2.1")
    fake._values.pop(f"{OPER}.1")
    fake.set(f"{OPER}.99", 1)  # a new interface: no rate yet
    await entry.runtime_data.fast.async_refresh()  # type: ignore[attr-defined]
    await hass.async_block_till_done()
    assert state(hass, "binary_sensor.switch_1_port_1_link").state == "unknown"
    for oid in [k for k in fake._values if k.endswith(".2") and k.startswith("1.3.6.1.2.1.2.2.1.")]:
        fake._values.pop(oid)
    for oid in [
        k for k in fake._values if k.endswith(".2") and k.startswith("1.3.6.1.2.1.31.1.1.1.")
    ]:
        fake._values.pop(oid)
    await entry.runtime_data.fast.async_refresh()  # type: ignore[attr-defined]
    await hass.async_block_till_done()
    assert state(hass, "sensor.switch_1_port_2_speed").state == "unavailable"


async def test_poe_port_without_status_or_row(hass: HomeAssistant) -> None:
    entry = await setup(hass)
    slow = entry.runtime_data.slow  # type: ignore[attr-defined]
    slow.data.poe = Poe(supplies=slow.data.poe.supplies, ports=[PsePort(1, 1, None, None, 2)])
    slow.async_update_listeners()
    await hass.async_block_till_done()
    poe = state(hass, "sensor.switch_1_port_1_poe")
    assert poe.state == "unknown"
    assert poe.attributes["power_class"] == 1
    assert "enabled" not in state(hass, "sensor.switch_1_port_2_poe").attributes
    slow.data.poe = None
    slow.async_update_listeners()
    await hass.async_block_till_done()
    assert state(hass, "sensor.switch_1_port_1_poe").state == "unknown"


async def test_switch_without_unique_id(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.3")
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, unique_id=None)  # set up without an identity
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    link = er.async_get(hass).async_get("binary_sensor.switch_3_port_1_link")
    assert link is not None
    assert link.unique_id == f"{entry.entry_id}_1_link"


async def test_lldp_neighbour_without_mac(hass: HomeAssistant) -> None:
    entry = await setup(hass)
    slow = entry.runtime_data.slow  # type: ignore[attr-defined]
    remote = LldpRemote(0, 1, 1, chassis_id_subtype=7, chassis_id="core", sys_name="core")
    slow.data.lldp = Lldp(4, "02:00:00:00:00:02", "switch-1", slow.data.lldp.ports, [remote])
    devices = connected(hass, entry, 1)  # type: ignore[arg-type]
    assert devices[0] == Connected(None, "core", (), lldp=True)
    assert len(get_hub(hass).entries) == 1
    assert Interface(index=1).index == 1


async def test_unload_that_fails_keeps_the_switch(hass: HomeAssistant) -> None:
    from unittest.mock import patch  # noqa: PLC0415

    entry = await setup(hass)
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=False):
        assert not await hass.config_entries.async_unload(entry.entry_id)  # type: ignore[attr-defined]
    assert not transport("192.0.2.1").closed
