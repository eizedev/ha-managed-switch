"""Polling: traffic rates, optional reads that fail, errors, the remembered devices."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from aiosnmpswitch import Interface, SnmpAuthError, SnmpError, SnmpTimeoutError
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.managed_switch.coordinator import _rate, get_hub, map_error

from .conftest import FakeTransport, make_entry, transport

HC_IN = "1.3.6.1.2.1.31.1.1.1.6"
HC_OUT = "1.3.6.1.2.1.31.1.1.1.10"


async def setup(hass: HomeAssistant, host: str = "192.0.2.1", **options: Any) -> Any:
    entry = make_entry(host, **options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_traffic_rates(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    entry = await setup(hass)
    fast = entry.runtime_data.fast
    assert fast.data.rates == {}  # the first reading has nothing to compare with
    fake = transport("192.0.2.1")
    before_in = fake._values[f"{HC_IN}.1"]
    before_out = fake._values[f"{HC_OUT}.1"]
    assert isinstance(before_in, int)
    assert isinstance(before_out, int)
    fast._previous = (fast._previous[0] - 10, fast._previous[1])  # ten seconds earlier
    fake.set(f"{HC_IN}.1", before_in + 1_250_000)  # 1 Mbit/s over ten seconds
    fake.set(f"{HC_OUT}.1", before_out + 2_500_000)
    fake.set(f"{HC_IN}.2", 0)  # a counter that went backwards: no rate
    await fast.async_refresh()
    received, sent = fast.data.rates[1]
    assert received == pytest.approx(1_000_000, rel=0.01)
    assert sent == pytest.approx(2_000_000, rel=0.01)
    assert 2 not in fast.data.rates


def test_rate_needs_both_counters() -> None:
    old, new = Interface(index=1, hc_in_octets=1), Interface(index=1, hc_in_octets=2)
    assert _rate(old, new, 1.0) is None


async def test_optional_reads_keep_their_last_value(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    entry = await setup(hass)
    slow = entry.runtime_data.slow
    fdb = slow.data.fdb
    FakeTransport.errors = {"192.0.2.1": {"1.3.6.1.2.1.17.7.1.2.2.1": SnmpError("tooBig")}}
    await slow.async_refresh()
    await slow.async_refresh()
    assert slow.last_update_success
    assert slow.data.fdb == fdb
    assert caplog.text.count("fdb failed, keeping the last value") == 1  # once, not every time
    FakeTransport.errors = {}
    await slow.async_refresh()
    assert slow._failed == set()


async def test_an_optional_read_failing_at_setup_is_empty(hass: HomeAssistant) -> None:
    FakeTransport.errors = {"192.0.2.1": {"1.0.8802.1.1.2.1.3": SnmpError("genErr")}}
    entry = await setup(hass)
    assert entry.runtime_data.slow.data.lldp is None


async def test_rejected_credentials_start_reauth(hass: HomeAssistant) -> None:
    entry = await setup(hass)
    FakeTransport.errors = {"192.0.2.1": {"1.3.6.1.2.1.17.1.4.1.2": SnmpAuthError("WrongDigest")}}
    await entry.runtime_data.slow.async_refresh()
    await hass.async_block_till_done()
    assert any(
        f["context"]["source"] == "reauth" for f in hass.config_entries.flow.async_progress()
    )


async def test_boot_time_is_stable(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    entry = await setup(hass)
    slow = entry.runtime_data.slow
    boot = slow.data.boot_time
    freezer.tick(timedelta(seconds=30))  # sysUpTime in the recording does not move
    await slow.async_refresh()
    assert slow.data.boot_time == boot  # 30 seconds off: still the same boot
    freezer.tick(timedelta(hours=1))
    await slow.async_refresh()
    assert slow.data.boot_time != boot


async def test_no_uptime_no_boot_time(hass: HomeAssistant) -> None:
    entry = await setup(hass)
    transport("192.0.2.1")._values.pop("1.3.6.1.2.1.1.3.0")
    await entry.runtime_data.slow.async_refresh()
    assert entry.runtime_data.slow.data.boot_time is None


async def test_intervals_from_options(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    entry = await setup(hass, fast_interval=15, slow_interval=90)
    assert entry.runtime_data.fast.update_interval == timedelta(seconds=15)
    assert entry.runtime_data.slow.update_interval == timedelta(seconds=90)
    FakeTransport.errors = {"192.0.2.1": {"1.3.6.1.2.1.2.2.1": SnmpTimeoutError("no answer")}}
    freezer.tick(timedelta(seconds=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert not entry.runtime_data.fast.last_update_success
    assert entry.state is ConfigEntryState.LOADED


def test_map_error() -> None:
    error = map_error(SnmpError("genErr"))
    assert isinstance(error, UpdateFailed)
    assert error.translation_placeholders == {"error": "genErr"}


async def test_new_devices_are_remembered(hass: HomeAssistant) -> None:
    entry = await setup(hass)
    hub = get_hub(hass)
    assert hub._known  # the first run remembers without events
    await hass.config_entries.async_unload(entry.entry_id)
    hub._known = None
    await hub.async_load()
    assert hub._known  # read back from storage
    await hub.async_forget()
    assert hub._known is None
