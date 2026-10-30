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
    hub._known.pop(forgotten, None)
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
    hub._known.pop(on_3, None)
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
    hub._known["02:00:00:00:00:ff"] = None  # after the first run
    second = entry_for("192.0.2.3")
    second.add_to_hass(hass)
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()
    # devices that were there all along, newly seen because a switch joined: not announced
    assert state(hass, "event.switch_3_switch_events").state == "unknown"
    assert state(hass, EVENT).state == "unknown"


async def test_two_uplinks_down_in_one_update_are_both_seen(hass: HomeAssistant) -> None:
    [entry, _, _] = await setup(hass, "192.0.2.1", "192.0.2.2", "192.0.2.3")
    seen: list[str] = []
    hass.bus.async_listen(
        "state_changed",
        lambda event: (
            seen.append(event.data["new_state"].attributes.get("port"))
            if event.data["entity_id"] == EVENT and event.data["new_state"].state != "unavailable"
            else None
        ),
    )
    fake = transport("192.0.2.1")
    fake.set(f"{OPER}.5", 2)
    fake.set(f"{OPER}.7", 2)
    await entry.runtime_data.fast.async_refresh()
    await hass.async_block_till_done()
    assert seen == ["5", "7"]


async def test_uplink_down_after_lldp_forgot_the_neighbour(hass: HomeAssistant) -> None:
    [entry, _] = await setup(hass, "192.0.2.1", "192.0.2.2")
    await entry.runtime_data.fast.async_refresh()  # remembers port 7 as an uplink
    fake = transport("192.0.2.1")
    for oid in [k for k in fake._values if k.startswith("1.0.8802.1.1.2.1.4.")]:
        fake._values.pop(oid)  # the neighbour is gone from LLDP first
    await entry.runtime_data.slow.async_refresh()
    fake.set(f"{OPER}.7", 2)
    await entry.runtime_data.fast.async_refresh()
    await hass.async_block_till_done()
    assert (last(hass)["event_type"], last(hass)["port"]) == ("uplink_down", "7")


async def test_a_second_uptime_wrap_is_no_restart(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    [entry] = await setup(hass, "192.0.2.1")
    slow = entry.runtime_data.slow
    before = slow.data.boot_time
    fake = transport("192.0.2.1")
    uptime = fake._values[UPTIME]
    assert isinstance(uptime, int)
    fake.set(UPTIME, uptime - 2 * 2**32 + 1000)  # as if it had wrapped twice
    freezer.tick(timedelta(seconds=10))
    await slow.async_refresh()
    await hass.async_block_till_done()
    assert slow.data.boot_time == before
    assert state(hass, EVENT).state == "unknown"


async def test_uptime_wrap_is_no_restart(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    [entry] = await setup(hass, "192.0.2.1")
    slow = entry.runtime_data.slow
    before = slow.data.boot_time
    fake = transport("192.0.2.1")
    uptime = fake._values[UPTIME]
    assert isinstance(uptime, int)
    fake.set(UPTIME, uptime - 2**32 + 1000)  # wrapped: ten seconds past the counter's end
    freezer.tick(timedelta(seconds=10))
    await slow.async_refresh()
    await hass.async_block_till_done()
    assert slow.data.boot_time == before
    assert state(hass, EVENT).state == "unknown"


async def test_a_switch_whose_table_comes_late_announces_nothing(hass: HomeAssistant) -> None:
    from aiosnmpswitch import SnmpError  # noqa: PLC0415

    from .conftest import FakeTransport  # noqa: PLC0415

    FakeTransport.errors = {"192.0.2.3": {"1.3.6.1.2.1.17.7.1.2.2.1": SnmpError("tooBig")}}
    entries = await setup(hass, "192.0.2.1", "192.0.2.3")
    hub = get_hub(hass)
    assert hub._known is not None
    for mac, location in list(hub.locations.items()):
        if location.port_name in ("2", "3", "4"):
            hub._known.pop(mac, None)
    hub._known["02:00:00:00:00:ff"] = None
    FakeTransport.errors = {}
    await entries[1].runtime_data.slow.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "event.switch_3_switch_events").state == "unknown"


async def test_remembered_devices_are_capped(hass: HomeAssistant, monkeypatch: Any) -> None:
    from custom_components.managed_switch import coordinator  # noqa: PLC0415

    monkeypatch.setattr(coordinator, "MAX_KNOWN", 3)
    await setup(hass, "192.0.2.1")
    hub = get_hub(hass)
    assert hub._known is not None
    assert len(hub._known) == 3


async def test_devices_seen_again_are_kept_longest(hass: HomeAssistant, monkeypatch: Any) -> None:
    from custom_components.managed_switch import coordinator  # noqa: PLC0415

    await setup(hass, "192.0.2.1")
    hub = get_hub(hass)
    assert hub._known is not None
    located = list(hub.locations)
    old = [f"02:00:00:00:ff:{n:02x}" for n in range(3)]  # devices gone for good, seen later
    hub._known = dict.fromkeys(located[1:] + old)  # located[0] comes as new and fills it up
    monkeypatch.setattr(coordinator, "MAX_KNOWN", len(located))
    hub.async_update()
    await hass.async_block_till_done()
    assert set(hub._known) == set(located)  # the old ones go, though the others came first
