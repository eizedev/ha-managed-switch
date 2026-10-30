"""Switch events: uplink or trunk down, slower port, restart, new device."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant

from custom_components.managed_switch.coordinator import get_hub

from .conftest import make_entry, state, transport

OPER = "1.3.6.1.2.1.2.2.1.8"
HIGH_SPEED = "1.3.6.1.2.1.31.1.1.1.15"
UPTIME = "1.3.6.1.2.1.1.3.0"
EVENT = "event.switch_1_switch_events"


async def setup(hass: HomeAssistant, *hosts: str) -> list[Any]:
    entries = [make_entry(host) for host in hosts]
    for entry in entries:
        entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entries[0].entry_id)
    await hass.async_block_till_done()
    return entries


def last(hass: HomeAssistant) -> dict[str, Any]:
    state = hass.states.get(EVENT)
    assert state is not None
    return dict(state.attributes)


async def test_nothing_fires_at_startup(hass: HomeAssistant) -> None:
    await setup(hass, "192.0.2.1", "192.0.2.2")
    assert state(hass, EVENT).state == "unknown"


async def test_uplink_and_trunk_down(hass: HomeAssistant) -> None:
    [entry, _] = await setup(hass, "192.0.2.1", "192.0.2.2")
    fake = transport("192.0.2.1")
    fake.set(f"{OPER}.7", 2)  # the uplink to switch-2
    await entry.runtime_data.fast.async_refresh()
    await hass.async_block_till_done()
    assert last(hass)["event_type"] == "uplink_down"
    assert last(hass)["port"] == "7"
    fake.set(f"{OPER}.3", 2)  # a member of trunk 1
    await entry.runtime_data.fast.async_refresh()
    await hass.async_block_till_done()
    assert (last(hass)["event_type"], last(hass)["port"]) == ("uplink_down", "3")
    fake.set(f"{OPER}.1", 2)  # an ordinary port: no event
    await entry.runtime_data.fast.async_refresh()
    await hass.async_block_till_done()
    assert last(hass)["port"] == "3"


async def test_speed_dropped(hass: HomeAssistant) -> None:
    [entry] = await setup(hass, "192.0.2.1")
    fake = transport("192.0.2.1")
    fake.set(f"{OPER}.1", 2)
    await entry.runtime_data.fast.async_refresh()
    fake.set(f"{OPER}.1", 1)
    fake.set(f"{HIGH_SPEED}.1", 100)  # came back at 100 Mbit/s instead of 1000
    await entry.runtime_data.fast.async_refresh()
    await hass.async_block_till_done()
    attributes = last(hass)
    assert attributes["event_type"] == "speed_dropped"
    assert (attributes["speed"], attributes["previous"]) == (100, 1000)


async def test_restarted(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    [entry] = await setup(hass, "192.0.2.1")
    transport("192.0.2.1").set(UPTIME, 100)  # one second since boot
    freezer.tick(timedelta(minutes=5))
    await entry.runtime_data.slow.async_refresh()
    await hass.async_block_till_done()
    assert last(hass)["event_type"] == "restarted"


async def test_new_device(hass: HomeAssistant) -> None:
    [entry] = await setup(hass, "192.0.2.1")
    hub = get_hub(hass)
    forgotten = sorted(hub.locations)[0]
    location = hub.locations[forgotten]
    assert hub._known is not None
    hub._known.discard(forgotten)
    hub.async_update()
    await hass.async_block_till_done()
    attributes = last(hass)
    assert attributes["event_type"] == "new_device"
    assert (attributes["mac"], attributes["port"]) == (forgotten, location.port_name)
    assert entry.entry_id == location.switch


async def test_new_device_on_another_switch(hass: HomeAssistant) -> None:
    await setup(hass, "192.0.2.1", "192.0.2.3")
    hub = get_hub(hass)
    on_3 = next(
        mac for mac, loc in hub.locations.items() if loc.switch != hub_entry(hass, "switch-1")
    )
    assert hub._known is not None
    hub._known.discard(on_3)
    hub.async_update()
    await hass.async_block_till_done()
    assert state(hass, EVENT).state == "unknown"  # fired on switch-3, not on switch-1
    assert state(hass, "event.switch_3_switch_events").attributes["mac"] == on_3


def hub_entry(hass: HomeAssistant, title: str) -> str:
    return next(
        e.entry_id for e in hass.config_entries.async_entries("managed_switch") if e.title == title
    )


async def test_adding_a_switch_announces_nothing(hass: HomeAssistant) -> None:
    from .conftest import make_entry as entry_for  # noqa: PLC0415

    await setup(hass, "192.0.2.1")
    hub = get_hub(hass)
    assert hub._known is not None
    hub._known.clear()  # as if switch-1 had never seen any of them,
    hub._known.add("02:00:00:00:00:ff")  # after the first run
    second = entry_for("192.0.2.3")
    second.add_to_hass(hass)
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()
    # devices that were there all along, newly seen because a switch joined: not announced
    assert state(hass, "event.switch_3_switch_events").state == "unknown"
    assert state(hass, EVENT).state == "unknown"
