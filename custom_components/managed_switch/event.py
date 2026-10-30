"""Events of a switch: uplink or trunk down, a slower port, a restart, a new device."""

from __future__ import annotations

from datetime import datetime

from aiosnmpswitch import Interface, OperStatus
from aiosnmpswitch.helpers import MacLocation, lag_members, port_name, uplink_ports
from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

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
        self._last_speed = {
            index: i.high_speed
            for index, i in self._interfaces.items()
            if _is_up(i) and i.high_speed
        }
        self._boot_time: datetime | None = entry.runtime_data.slow.data.boot_time

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
        watched = self._watched()
        for index, now in interfaces.items():
            before = self._interfaces.get(index)
            name = port_name(now)
            if index in watched and _is_up(before) and not _is_up(now):
                self._trigger_event(EVENT_UPLINK_DOWN, {"port": name, "if_index": index})
            if _is_up(now) and now.high_speed:
                last = self._last_speed.get(index)
                if last and now.high_speed < last:
                    self._trigger_event(
                        EVENT_SPEED_DROPPED,
                        {
                            "port": name,
                            "if_index": index,
                            "speed": now.high_speed,
                            "previous": last,
                        },
                    )
                self._last_speed[index] = now.high_speed
        self._interfaces = dict(interfaces)
        super()._handle_coordinator_update()

    @callback
    def _slow_updated(self) -> None:
        """Fire when the switch booted again since the previous reading."""
        boot_time = self.entry.runtime_data.slow.data.boot_time
        if boot_time and self._boot_time and boot_time > self._boot_time:
            self._trigger_event(EVENT_RESTARTED, {"boot_time": boot_time.isoformat()})
            self.async_write_ha_state()
        if boot_time:
            self._boot_time = boot_time

    @callback
    def _new_device(self, location: MacLocation) -> None:
        """Fire for a device seen for the first time, on this switch."""
        if location.switch != self.entry.entry_id:
            return
        self._trigger_event(
            EVENT_NEW_DEVICE,
            {
                "port": location.port_name,
                "if_index": location.if_index,
                "mac": location.address,
                "name": registry_name(self.hass, location.address),
                "ip_addresses": list(location.ip_addresses),
            },
        )
        self.async_write_ha_state()
