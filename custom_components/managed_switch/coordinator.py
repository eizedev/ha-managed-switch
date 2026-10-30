"""Data update coordinators and the hub that locates devices across all switches."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
from typing import Any

from aiosnmpswitch import (
    Chassis,
    FdbEntry,
    Interface,
    Lldp,
    NeighborEntry,
    Poe,
    SnmpAuthError,
    SnmpError,
    SnmpSwitch,
    SnmpTimeoutError,
    StpInfo,
    SystemInfo,
)
from aiosnmpswitch.helpers import MacLocation, SwitchData, locate_macs
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.hass_dict import HassKey

from .const import (
    CONF_FAST_INTERVAL,
    CONF_SLOW_INTERVAL,
    DEFAULT_FAST_INTERVAL,
    DEFAULT_SLOW_INTERVAL,
    DOMAIN,
    LOGGER,
)

SIGNAL_LOCATIONS = f"{DOMAIN}_locations"
SIGNAL_NEW_DEVICE = f"{DOMAIN}_new_device"
STORE_VERSION = 1
HUB_KEY: HassKey[NetworkHub] = HassKey(DOMAIN)
# Devices remembered for new_device; the oldest are forgotten beyond this.
MAX_KNOWN = 5000
# sysUpTime wraps after 2**32 hundredths of a second (about 497 days).
_UPTIME_WRAP = timedelta(seconds=2**32 / 100)
# A counter that goes backwards (wrap, reset, restart) gives no rate for that interval.
_TICKS_PER_SECOND = 100

type SwitchConfigEntry = ConfigEntry[SwitchRuntimeData]


@dataclass(kw_only=True)
class FastData:
    """What changes quickly: the interfaces with link, speed and counters."""

    interfaces: dict[int, Interface]
    rates: dict[int, tuple[float, float]] = field(default_factory=dict)
    """Received and sent bits per second since the previous update, by ``ifIndex``."""


@dataclass(kw_only=True)
class SlowData:
    """What changes slowly. Everything but the system information is optional."""

    system: SystemInfo
    boot_time: datetime | None = None
    chassis: Chassis | None = None
    bridge_ports: dict[int, int] = field(default_factory=dict)
    fdb: list[FdbEntry] = field(default_factory=list)
    lldp: Lldp | None = None
    lag_ports: dict[int, int] = field(default_factory=dict)
    poe: Poe | None = None
    stp: StpInfo | None = None
    neighbors: list[NeighborEntry] = field(default_factory=list)


# Optional reads of the slow coordinator: SlowData field and client getter.
SLOW_READS: tuple[tuple[str, str], ...] = (
    ("chassis", "get_chassis"),
    ("bridge_ports", "get_bridge_ports"),
    ("fdb", "get_fdb"),
    ("lldp", "get_lldp"),
    ("lag_ports", "get_lag_ports"),
    ("poe", "get_poe"),
    ("stp", "get_stp"),
    ("neighbors", "get_neighbors"),
)


@dataclass(kw_only=True)
class SwitchRuntimeData:
    """Everything one config entry keeps while it is loaded."""

    switch: SnmpSwitch
    fast: FastCoordinator
    slow: SlowCoordinator


def map_error(err: SnmpError) -> Exception:
    """Translate a library error into what Home Assistant expects from an update."""
    if isinstance(err, SnmpAuthError):
        return ConfigEntryAuthFailed(translation_domain=DOMAIN, translation_key="auth")
    if isinstance(err, SnmpTimeoutError):
        return UpdateFailed(translation_domain=DOMAIN, translation_key="timeout")
    return UpdateFailed(
        translation_domain=DOMAIN,
        translation_key="error",
        translation_placeholders={"error": str(err)},
    )


async def _read[T](read: Callable[[], Awaitable[T]]) -> T:
    """Run one read and map its errors."""
    try:
        return await read()
    except SnmpError as err:
        raise map_error(err) from err


class FastCoordinator(DataUpdateCoordinator[FastData]):
    """Polls the interfaces."""

    config_entry: SwitchConfigEntry

    def __init__(self, hass: HomeAssistant, entry: SwitchConfigEntry, switch: SnmpSwitch) -> None:
        """Poll every fast interval."""
        seconds = entry.options.get(CONF_FAST_INTERVAL, DEFAULT_FAST_INTERVAL.total_seconds())
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{entry.title} ports",
            update_interval=timedelta(seconds=seconds),
        )
        self.switch = switch
        self._previous: tuple[float, dict[int, Interface]] | None = None

    async def _async_update_data(self) -> FastData:
        interfaces = await _read(self.switch.get_interfaces)
        now = time.monotonic()
        rates = {}
        if self._previous is not None:
            then, before = self._previous
            elapsed = max(now - then, 0.001)
            for index, interface in interfaces.items():
                old = before.get(index)
                rate = _rate(old, interface, elapsed) if old is not None else None
                if rate is not None:
                    rates[index] = rate
        self._previous = (now, interfaces)
        return FastData(interfaces=interfaces, rates=rates)


def _rate(old: Interface, new: Interface, seconds: float) -> tuple[float, float] | None:
    """Received and sent bits per second between two readings of the 64-bit counters."""
    pairs = ((old.hc_in_octets, new.hc_in_octets), (old.hc_out_octets, new.hc_out_octets))
    deltas = []
    for before, after in pairs:
        if before is None or after is None or after < before:
            return None
        deltas.append((after - before) * 8 / seconds)
    return deltas[0], deltas[1]


class SlowCoordinator(DataUpdateCoordinator[SlowData]):
    """Polls system, address table, LLDP, trunks, PoE, spanning tree and neighbour cache.

    The system information must succeed; an optional read that fails keeps its last value.
    """

    config_entry: SwitchConfigEntry

    def __init__(self, hass: HomeAssistant, entry: SwitchConfigEntry, switch: SnmpSwitch) -> None:
        """Poll every slow interval."""
        seconds = entry.options.get(CONF_SLOW_INTERVAL, DEFAULT_SLOW_INTERVAL.total_seconds())
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{entry.title} tables",
            update_interval=timedelta(seconds=seconds),
        )
        self.switch = switch
        self._failed: set[str] = set()

    async def _async_update_data(self) -> SlowData:
        system = await _read(self.switch.get_system)
        boot_time = None
        if system.up_time is not None:
            boot_time = dt_util.utcnow() - timedelta(seconds=system.up_time / _TICKS_PER_SECOND)
            boot_time = boot_time.replace(microsecond=0)
            previous = self.data.boot_time if self.data else None
            # sysUpTime is read a moment later each time: keep the boot time unless it moved.
            # A jump of about 497 days is sysUpTime wrapping around, not a restart.
            moved = (boot_time - previous) if previous else None
            if moved is not None:
                wraps = round(moved / _UPTIME_WRAP)  # 0, or how often it wrapped meanwhile
                if abs((moved - wraps * _UPTIME_WRAP).total_seconds()) < (
                    60 if wraps == 0 else 3600
                ):
                    boot_time = previous
        values: dict[str, Any] = {}
        for name, getter in SLOW_READS:
            try:
                values[name] = await getattr(self.switch, getter)()
            except SnmpAuthError as err:
                raise map_error(err) from err
            except SnmpError as err:
                if name not in self._failed:
                    LOGGER.info("%s: %s failed, keeping the last value: %s", self.name, name, err)
                    self._failed.add(name)
                if self.data is not None:
                    values[name] = getattr(self.data, name)
            else:
                self._failed.discard(name)
        return SlowData(system=system, boot_time=boot_time, **values)


class NetworkHub:
    """Combines the address tables of all switches into device locations.

    It also remembers every device it has located, so ``new_device`` is sent once per device and
    not again after a restart.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Start empty; :meth:`async_load` reads the remembered devices."""
        self.hass = hass
        self.entries: dict[str, SwitchConfigEntry] = {}
        self.locations: dict[str, MacLocation] = {}
        self._store: Store[dict[str, list[str]]] = Store(hass, STORE_VERSION, f"{DOMAIN}.devices")
        self._known: dict[str, None] | None = None
        """Every device located so far, oldest first (a dict keeps the order)."""
        self._with_fdb: set[str] = set()
        """Entries whose address table was read with entries at least once."""

    async def async_load(self) -> None:
        """Read the remembered devices once."""
        if self._known is None:
            stored = await self._store.async_load()
            self._known = dict.fromkeys(stored["known"]) if stored else {}

    @callback
    def async_add(self, entry: SwitchConfigEntry) -> None:
        """Include a loaded entry and update the locations whenever its tables change."""
        self.entries[entry.entry_id] = entry
        entry.async_on_unload(entry.runtime_data.slow.async_add_listener(self.async_update))
        # A switch that joins shows devices that were there all along (before only seen on an
        # uplink, or on a switch that was not loaded yet): remember them without announcing.
        self.async_update(announce=False)

    @callback
    def async_remove(self, entry: SwitchConfigEntry) -> None:
        """Leave out an unloaded entry."""
        self.entries.pop(entry.entry_id, None)
        self._with_fdb.discard(entry.entry_id)
        self.async_update()

    @callback
    def async_update(self, announce: bool = True) -> None:
        """Locate all devices again and tell the entities; announce devices never seen before."""
        switches = {
            entry_id: switch_data(entry)
            for entry_id, entry in self.entries.items()
            if entry.runtime_data.slow.data is not None and entry.runtime_data.fast.data is not None
        }
        self.locations = locate_macs(switches)
        known = self._known if self._known is not None else {}
        new = [loc for mac, loc in self.locations.items() if mac not in known]
        for mac in self.locations.keys() & known.keys():  # seen again: the newest to keep
            del known[mac]
            known[mac] = None
        if new:
            announce = announce and bool(known)  # the very first run only learns
            for location in new:
                known[location.address] = None
            while len(known) > MAX_KNOWN:  # devices with changing random MACs would pile up
                del known[next(iter(known))]
            # New devices are rare after the first run: save right away, no delayed write.
            self.hass.async_create_task(self._store.async_save({"known": list(known)}))
            for location in new if announce else ():
                # A switch whose address table was empty or unreadable until now shows devices
                # that were there all along.
                if location.switch in self._with_fdb:
                    async_dispatcher_send(self.hass, SIGNAL_NEW_DEVICE, location)
        self._with_fdb.update(entry_id for entry_id, data in switches.items() if any(data.fdb))
        self._known = known
        async_dispatcher_send(self.hass, SIGNAL_LOCATIONS)

    async def async_forget(self) -> None:
        """Forget the remembered devices (the last switch was removed)."""
        self._known = None
        await self._store.async_remove()


def switch_data(entry: SwitchConfigEntry) -> SwitchData:
    """Return the reads of one loaded entry, as the library's helpers take them."""
    fast, slow = entry.runtime_data.fast.data, entry.runtime_data.slow.data
    return SwitchData(
        interfaces=fast.interfaces,
        bridge_ports=slow.bridge_ports,
        fdb=slow.fdb,
        lldp=slow.lldp,
        lag_ports=slow.lag_ports,
        neighbors=slow.neighbors,
    )


def get_hub(hass: HomeAssistant) -> NetworkHub:
    """Return the hub shared by all entries."""
    if HUB_KEY not in hass.data:
        hass.data[HUB_KEY] = NetworkHub(hass)
    return hass.data[HUB_KEY]
