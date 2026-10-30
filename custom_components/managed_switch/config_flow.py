"""Config flow: where the switch is, SNMPv3 user or community, intervals."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aiosnmpswitch import AuthProtocol, PrivProtocol, SnmpAuthError, SnmpError, SnmpTimeoutError
from aiosnmpswitch.helpers import is_ethernet_port
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import probatio

from . import connect
from .const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_FAST_INTERVAL,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SLOW_INTERVAL,
    CONF_SNMP_VERSION,
    CONF_USER,
    DEFAULT_FAST_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SLOW_INTERVAL,
    DOCS_URL,
    DOMAIN,
    LOGGER,
    MIN_FAST_INTERVAL,
    MIN_SLOW_INTERVAL,
)
from .coordinator import SwitchConfigEntry

DOCS_SETUP = f"{DOCS_URL}configuration/"
DOCS_SNMP = f"{DOCS_URL}configuration/#snmp-access"
SNMP_VERSIONS = ["3", "2c", "1"]
_MAC_TEXT_LENGTH = 17
_SECRET = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _select(options: list[str], key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN, translation_key=key)
    )


def _connection_schema() -> probatio.Schema:
    return probatio.Schema(
        {
            probatio.Required(CONF_HOST): TextSelector(),
            probatio.Optional(CONF_PORT, default=DEFAULT_PORT): NumberSelector(
                NumberSelectorConfig(min=1, max=65535, step=1, mode=NumberSelectorMode.BOX)
            ),
            probatio.Required(CONF_SNMP_VERSION, default="3"): _select(
                SNMP_VERSIONS, CONF_SNMP_VERSION
            ),
        }
    )


COMMUNITY_SCHEMA = probatio.Schema({probatio.Required(CONF_COMMUNITY): _SECRET})
USM_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_USER): TextSelector(),
        probatio.Required(CONF_AUTH_PROTOCOL, default=AuthProtocol.SHA.value): _select(
            [p.value for p in AuthProtocol], CONF_AUTH_PROTOCOL
        ),
        probatio.Optional(CONF_AUTH_KEY): _SECRET,
        probatio.Required(CONF_PRIV_PROTOCOL, default=PrivProtocol.AES128.value): _select(
            [p.value for p in PrivProtocol], CONF_PRIV_PROTOCOL
        ),
        probatio.Optional(CONF_PRIV_KEY): _SECRET,
    }
)


class NoIdentityError(SnmpError):
    """The switch reports no MAC address to tell it apart from others."""


class KeyMissingError(SnmpError):
    """A protocol was chosen without its key, or a privacy key without authentication."""


def _error_key(err: Exception) -> str:
    """Return the form error for a failed attempt; log unexpected ones."""
    if isinstance(err, NoIdentityError):
        return "no_identity"
    if isinstance(err, KeyMissingError):
        return "key_missing"
    if isinstance(err, SnmpAuthError):
        return "invalid_auth"
    if isinstance(err, SnmpTimeoutError):
        return "timeout"
    if isinstance(err, SnmpError):
        return "cannot_connect"
    LOGGER.exception("Unexpected error while connecting", exc_info=err)
    return "unknown"


def _credentials(data: Mapping[str, Any]) -> dict[str, Any]:
    """Only the credential fields of the chosen SNMP version, checked for missing keys."""
    if data[CONF_SNMP_VERSION] != "3":
        return {CONF_COMMUNITY: data[CONF_COMMUNITY]}
    auth_key, priv_key = data.get(CONF_AUTH_KEY), data.get(CONF_PRIV_KEY)
    auth = data[CONF_AUTH_PROTOCOL] != AuthProtocol.NONE
    priv = data[CONF_PRIV_PROTOCOL] != PrivProtocol.NONE
    if auth != bool(auth_key) or priv != bool(priv_key) or (priv and not auth):
        raise KeyMissingError
    return {
        CONF_USER: data[CONF_USER],
        CONF_AUTH_PROTOCOL: data[CONF_AUTH_PROTOCOL],
        CONF_AUTH_KEY: auth_key,
        CONF_PRIV_PROTOCOL: data[CONF_PRIV_PROTOCOL],
        CONF_PRIV_KEY: priv_key,
    }


async def _probe(hass: HomeAssistant, data: Mapping[str, Any]) -> tuple[str, set[str], str | None]:
    """Read the switch once: its MAC address (the unique ID), all its own addresses, its name.

    The unique ID is the LLDP chassis MAC, or without LLDP the lowest port MAC; on many switches
    these differ (the chassis MAC belongs to the management interface). Both are among the
    switch's own addresses, which is how a switch is recognised when LLDP was turned on or off.
    """
    switch = await connect(hass, data, shared=False)
    try:
        system = await switch.get_system()
        lldp = await switch.get_lldp()
        interfaces = await switch.get_interfaces()
    finally:
        await switch.close()
    identity = lldp.chassis_id if lldp.chassis_id_subtype == 4 else None  # noqa: PLR2004
    if not identity or len(identity) != _MAC_TEXT_LENGTH:
        macs = [
            i.phys_address for i in interfaces.values() if is_ethernet_port(i) and i.phys_address
        ]
        identity = min(macs) if macs else None
    if identity is None:
        raise NoIdentityError
    addresses = {i.phys_address for i in interfaces.values() if i.phys_address} | {identity}
    return identity, addresses, system.name


class SwitchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up one managed switch."""

    VERSION = 1

    def __init__(self) -> None:
        """Start with nothing known."""
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: SwitchConfigEntry) -> SwitchOptionsFlow:
        """Return the options flow: polling intervals."""
        return SwitchOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask where the switch is and which SNMP version it speaks."""
        if user_input is not None:
            self._data = {**user_input, CONF_PORT: int(user_input.get(CONF_PORT, DEFAULT_PORT))}
            return await self._credentials_step(None)
        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(),
            description_placeholders={"docs": DOCS_SETUP},
        )

    async def async_step_community(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the SNMPv1 or v2c community."""
        return await self._credentials_step(user_input)

    async def async_step_usm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the SNMPv3 user and its keys."""
        return await self._credentials_step(user_input)

    async def _credentials_step(self, user_input: dict[str, Any] | None) -> ConfigFlowResult:
        """Check the credentials against the switch, then create or update the entry."""
        step = "usm" if self._data[CONF_SNMP_VERSION] == "3" else "community"
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = {**self._data, **_credentials({**self._data, **user_input})}
                identity, addresses, name = await _probe(self.hass, data)
            except Exception as err:  # the form shows the error; unexpected ones are logged
                errors["base"] = _error_key(err)
            else:
                return await self._finish(data, identity, addresses, name)
        schema = USM_SCHEMA if step == "usm" else COMMUNITY_SCHEMA
        return self.async_show_form(
            step_id=step,
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {}),
            errors=errors,
            description_placeholders={"docs": DOCS_SNMP, "host": self._data[CONF_HOST]},
        )

    async def _finish(
        self, data: dict[str, Any], identity: str, addresses: set[str], name: str | None
    ) -> ConfigFlowResult:
        # An entry whose ID is one of the switch's own addresses is this switch, under the other
        # identity (LLDP turned on or off since it was set up): keep that entry's ID.
        entry: ConfigEntry | None
        if self.source == "reauth":
            entry = self._get_reauth_entry()
        elif self.source == "reconfigure":
            entry = self._get_reconfigure_entry()
        else:
            entry = next(
                (e for e in self._async_current_entries() if e.unique_id in addresses), None
            )
        known = entry.unique_id if entry is not None and entry.unique_id in addresses else None
        await self.async_set_unique_id(known or identity)
        if self.source == "reauth":
            self._abort_if_unique_id_mismatch(reason="wrong_switch")
            return self.async_update_reload_and_abort(self._get_reauth_entry(), data=data)
        if self.source == "reconfigure":
            self._abort_if_unique_id_mismatch(reason="wrong_switch")
            return self.async_update_reload_and_abort(self._get_reconfigure_entry(), data=data)
        self._abort_if_unique_id_configured(updates={CONF_HOST: data[CONF_HOST]})
        return self.async_create_entry(title=name or data[CONF_HOST], data=data)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Ask for new credentials when the switch rejects the stored ones."""
        self._data = {
            CONF_HOST: entry_data[CONF_HOST],
            CONF_PORT: entry_data[CONF_PORT],
            CONF_SNMP_VERSION: entry_data[CONF_SNMP_VERSION],
        }
        return await self._credentials_step(None)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change address, port, SNMP version and credentials of a switch that is set up."""
        if user_input is not None:
            self._data = {**user_input, CONF_PORT: int(user_input.get(CONF_PORT, DEFAULT_PORT))}
            return await self._credentials_step(None)
        entry = self._get_reconfigure_entry()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(_connection_schema(), entry.data),
            description_placeholders={"docs": DOCS_SETUP},
        )


class SwitchOptionsFlow(OptionsFlowWithReload):
    """How often the switch is read."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the two intervals."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        schema = probatio.Schema(
            {
                probatio.Required(
                    CONF_FAST_INTERVAL,
                    default=options.get(CONF_FAST_INTERVAL, DEFAULT_FAST_INTERVAL.total_seconds()),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_FAST_INTERVAL,
                        max=3600,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                probatio.Required(
                    CONF_SLOW_INTERVAL,
                    default=options.get(CONF_SLOW_INTERVAL, DEFAULT_SLOW_INTERVAL.total_seconds()),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SLOW_INTERVAL,
                        max=86400,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, description_placeholders={"docs": DOCS_SETUP}
        )
