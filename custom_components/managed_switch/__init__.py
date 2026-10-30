"""The Managed Switch (SNMP) integration: managed network switches, read only."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from aiosnmpswitch import (
    AuthProtocol,
    CommunityAuth,
    PrivProtocol,
    PysnmpTransport,
    SnmpError,
    SnmpSwitch,
    UsmAuth,
    create_engine,
)
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.singleton import singleton
from homeassistant.helpers.typing import ConfigType

from . import websocket
from .const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    CONF_USER,
    DEFAULT_PORT,
    DOMAIN,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
)
from .coordinator import (
    FastCoordinator,
    SlowCoordinator,
    SwitchConfigEntry,
    SwitchRuntimeData,
    get_hub,
    map_error,
)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the WebSocket command the switch card uses."""
    websocket.async_setup(hass)
    return True


def auth_from(data: Mapping[str, Any]) -> CommunityAuth | UsmAuth:
    """Credentials from an entry's data."""
    if data[CONF_SNMP_VERSION] in ("1", "2c"):
        return CommunityAuth(data[CONF_COMMUNITY], version=data[CONF_SNMP_VERSION])
    return UsmAuth(
        data[CONF_USER],
        data.get(CONF_AUTH_KEY) or None,
        data.get(CONF_PRIV_KEY) or None,
        auth_protocol=AuthProtocol(data.get(CONF_AUTH_PROTOCOL, AuthProtocol.SHA)),
        priv_protocol=PrivProtocol(data.get(CONF_PRIV_PROTOCOL, PrivProtocol.AES128)),
    )


@dataclass
class _Engines:
    """SNMP engines, one per set of credentials, closed when Home Assistant stops."""

    by_credentials: dict[tuple[Any, ...], Any] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@singleton(f"{DOMAIN}_engines")
async def _engines(hass: HomeAssistant) -> _Engines:
    engines = _Engines()

    @callback
    def _close(_: Event) -> None:
        for engine in engines.by_credentials.values():
            engine.close_dispatcher()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close)
    return engines


async def get_engine(hass: HomeAssistant, auth: CommunityAuth | UsmAuth) -> Any:
    """Return an SNMP engine for these credentials, prepared outside the event loop.

    Switches with the same credentials share one. pysnmp keeps an SNMPv3 user in its engine by
    name: two switches with the same user name but different passwords in one engine would
    replace each other's keys, so different SNMPv3 credentials get different engines.
    """
    key: tuple[Any, ...] = ("community",)
    if isinstance(auth, UsmAuth):
        key = (auth.user, auth.auth_protocol, auth.auth_key, auth.priv_protocol, auth.priv_key)
    engines = await _engines(hass)
    async with engines.lock:
        if key not in engines.by_credentials:
            engines.by_credentials[key] = await create_engine()
        return engines.by_credentials[key]


async def connect(hass: HomeAssistant, data: Mapping[str, Any], shared: bool = True) -> SnmpSwitch:
    """Create a client for the switch an entry's data describes.

    ``shared=False`` (the setup dialog's test) uses an engine of its own that closes with the
    client, so mistyped credentials leave nothing behind.
    """
    auth = auth_from(data)
    transport = await PysnmpTransport.create(
        data[CONF_HOST],
        auth,
        port=int(data.get(CONF_PORT, DEFAULT_PORT)),
        timeout=REQUEST_TIMEOUT,
        retries=REQUEST_RETRIES,
        engine=await get_engine(hass, auth) if shared else None,
    )
    return SnmpSwitch(transport)


async def async_setup_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> bool:
    """Connect to one switch and start polling it."""
    try:
        switch = await connect(hass, entry.data)
    except SnmpError as err:
        raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="resolve") from err
    fast = FastCoordinator(hass, entry, switch)
    slow = SlowCoordinator(hass, entry, switch)
    entry.runtime_data = SwitchRuntimeData(switch=switch, fast=fast, slow=slow)
    try:
        await slow.async_config_entry_first_refresh()
        await fast.async_config_entry_first_refresh()
        hub = get_hub(hass)
        await hub.async_load()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await switch.close()
        raise
    hub.async_add(entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> bool:
    """Stop polling and release the SNMP engine."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        get_hub(hass).async_remove(entry)
        await entry.runtime_data.switch.close()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> None:
    """Forget the located devices once no switch is left."""
    if not any(e.entry_id != entry.entry_id for e in hass.config_entries.async_entries(DOMAIN)):
        await get_hub(hass).async_forget()


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: SwitchConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Keep the switch's own device while the entry is set up."""
    return False


__all__ = ["auth_from", "connect", "map_error"]
