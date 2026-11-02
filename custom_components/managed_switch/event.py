"""Events of a switch: uplink or trunk down, a slower port, a restart, a new device."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aiosnmpswitch import Interface, OperStatus
from aiosnmpswitch.helpers import MacLocation, lag_members, port_name, uplink_ports
from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import SPEED_HELD, SPEED_SETTLE_POLLS
from .coordinator import SIGNAL_NEW_DEVICE, FastCoordinator, SwitchConfigEntry, get_hub, switch_data
from .devices import registry_name
from .entity import SwitchEntity

PARALLEL_UPDATES = 0
EVENT_UPLINK_DOWN = "uplink_down"
EVENT_SPEED_DROPPED = "speed_dropped"
EVENT_RESTARTED = "restarted"
EVENT_NEW_DEVICE = "new_device"
DESCRIPTION = EventEntityDescription(
    key="port_event",
    translation_key="port_event",
    event_types=[EVENT_UPLINK_DOWN, EVENT_SPEED_DROPPED, EVENT_RESTARTED, EVENT_NEW_DEVICE],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the switch's event entity."""
    async_add_entities([SwitchEvent(entry, entry.runtime_data.fast, DESCRIPTION)])


def _is_up(interface: Interface | None) -> bool:
    return interface is not None and interface.oper_status is OperStatus.UP


@dataclass(slots=True)
class _PortSpeed:
    """A port's speed, settled before a drop counts (SPEED_SETTLE_POLLS, SPEED_HELD)."""

    held: int | None
    """The speed a drop is measured against: read at startup, held long enough, or reported."""
    speed: int | None = None
    """The current run of equal readings while the link is up."""
    since: datetime | None = None
    polls: int = 0

    def update(self, speed: int | None, now: datetime) -> int | None:
        """Take a reading, None while the link is down; return the held speed if it dropped."""
        if not speed:
            # A link that drops keeps its held speed: a cable plugged in again at a lower
            # speed is the drop worth reporting.
            self.speed, self.since, self.polls = None, None, 0
            return None
        if speed != self.speed or self.since is None:
            self.speed, self.since, self.polls = speed, now, 0
        self.polls += 1
        if self.polls == SPEED_SETTLE_POLLS and self.held and speed < self.held:
            previous, self.held = self.held, speed
            return previous
        if now - self.since >= SPEED_HELD:
            self.held = speed
        return None


class SwitchEvent(SwitchEntity[FastCoordinator], EventEntity):
    """Fires when something on the switch changes that may need attention."""

    _attr_should_poll = False

    def __init__(
        self,
        entry: SwitchConfigEntry,
        coordinator: FastCoordinator,
        description: EventEntityDescription,
    ) -> None:
        """Start from the current readings, so nothing fires for the state at startup."""
        super().__init__(entry, coordinator, description)
        self._interfaces = dict(coordinator.data.interfaces)
        # The speeds at startup count as held: they have most likely been there for a while.
        now = dt_util.utcnow()
        self._speeds = {
            index: _PortSpeed(i.high_speed, i.high_speed, now, 1)
            if _is_up(i) and i.high_speed
            else _PortSpeed(None)
            for index, i in self._interfaces.items()
        }
        self._boot_time: datetime | None = entry.runtime_data.slow.data.boot_time
        # Uplinks as they were while up: LLDP forgets a neighbour soon after its link drops, and
        # the slow tables may be read again before the port's link loss is seen.
        self._watched_before: set[int] = set()

    async def async_added_to_hass(self) -> None:
        """Watch the ports, the restarts and the hub's new devices."""
        await super().async_added_to_hass()
        self.async_on_remove(self.entry.runtime_data.slow.async_add_listener(self._slow_updated))
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_NEW_DEVICE, self._new_device)
        )

    def _watched(self) -> set[int]:
        """Uplinks to other switches, trunks and their members."""
        hub = get_hub(self.hass)
        uplinks = uplink_ports(
            {entry_id: switch_data(entry) for entry_id, entry in hub.entries.items()}
        ).get(self.entry.entry_id, set())
        data = switch_data(self.entry)
        members = lag_members(data.lag_ports, data.interfaces)
        return uplinks | set(members) | set(members.values())

    @callback
    def _handle_coordinator_update(self) -> None:
        """Compare each port with its previous reading."""
        interfaces = self.coordinator.data.interfaces
        current = self._watched()
        watched = current | self._watched_before
        self._watched_before = current
        read_at = dt_util.utcnow()
        for index, now in interfaces.items():
            before = self._interfaces.get(index)
            name = port_name(now)
            if index in watched and _is_up(before) and not _is_up(now):
                self._fire(EVENT_UPLINK_DOWN, {"port": name, "if_index": index})
            speed = now.high_speed if _is_up(now) else None
            previous = self._speeds.setdefault(index, _PortSpeed(None)).update(speed, read_at)
            if previous:
                self._fire(
                    EVENT_SPEED_DROPPED,
                    {"port": name, "if_index": index, "speed": speed, "previous": previous},
                )
        self._interfaces = dict(interfaces)
        super()._handle_coordinator_update()

    @callback
    def _fire(self, event_type: str, attributes: dict[str, object]) -> None:
        """Fire and write the state at once, so two events in one update are both seen."""
        self._trigger_event(event_type, attributes)
        self.async_write_ha_state()

    @callback
    def _slow_updated(self) -> None:
        """Fire when the switch booted again since the previous reading."""
        boot_time = self.entry.runtime_data.slow.data.boot_time
        if boot_time and self._boot_time and boot_time > self._boot_time:
            self._fire(EVENT_RESTARTED, {"boot_time": boot_time.isoformat()})
        if boot_time:
            self._boot_time = boot_time

    @callback
    def _new_device(self, location: MacLocation) -> None:
        """Fire for a device seen for the first time, on this switch."""
        if location.switch != self.entry.entry_id:
            return
        self._fire(
            EVENT_NEW_DEVICE,
            {
                "port": location.port_name,
                "if_index": location.if_index,
                "mac": location.address,
                "name": registry_name(self.hass, location.address),
                "ip_addresses": list(location.ip_addresses),
                # More than one device on the port: the device is behind a router, access point
                # or unmanaged switch there, maybe not plugged in at this switch at all.
                "devices_on_port": location.devices_on_port,
                "direct": location.devices_on_port == 1,
            },
        )
