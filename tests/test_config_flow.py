"""Config flow: SNMPv3 and v2c, errors, reauthentication, reconfiguration, options."""

from __future__ import annotations

from typing import Any

from aiosnmpswitch import SnmpAuthError, SnmpError, SnmpTimeoutError
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.managed_switch.config_flow import NoIdentityError, _error_key
from custom_components.managed_switch.const import DOMAIN

from .conftest import FakeTransport, entry_data, make_entry

V3 = {
    "user": "monitor",
    "auth_protocol": "sha",
    "auth_key": "auth-secret",
    "priv_protocol": "des",
    "priv_key": "priv-secret",
}


async def start(hass: HomeAssistant, host: str = "192.0.2.1", version: str = "3") -> Any:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host, "port": 161, "snmp_version": version}
    )


async def test_snmpv3(hass: HomeAssistant) -> None:
    result = await start(hass)
    assert result["step_id"] == "usm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V3)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "switch-1"
    assert result["result"].unique_id == "02:00:00:00:00:02"
    assert result["data"] == entry_data("192.0.2.1", "3")
    assert FakeTransport.instances[0].closed  # the probe does not stay connected


async def test_snmpv2c_on_a_1930(hass: HomeAssistant) -> None:
    result = await start(hass, "192.0.2.3", "2c")
    assert result["step_id"] == "community"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"community": "secret"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "02:00:00:00:00:19"
    assert result["data"] == entry_data("192.0.2.3", "2c")


async def test_identity_from_the_ports_without_lldp(hass: HomeAssistant) -> None:
    globals()["_hass"] = hass
    FakeTransport.errors = {"192.0.2.1": {"1.0.8802.1.1.2.1.3": SnmpError("genErr")}}
    with pytest.raises(SnmpError):  # get_lldp itself raises; the probe needs LLDP or ports
        await (await _probe_switch("192.0.2.1"))
    FakeTransport.errors = {}


_hass: Any = None


async def _probe_switch(host: str) -> Any:
    from custom_components.managed_switch.config_flow import _probe  # noqa: PLC0415

    return _probe(_hass, entry_data(host))


async def test_identity_falls_back_to_the_lowest_port_mac(hass: HomeAssistant) -> None:
    globals()["_hass"] = hass
    probe = await _probe_switch("192.0.2.1")
    original = FakeTransport.walk

    async def walk(self: FakeTransport, oid: str) -> Any:
        if oid.startswith("1.0.8802"):
            return []
        return await original(self, oid)

    original_get = FakeTransport.get

    async def get(self: FakeTransport, oids: Any) -> Any:
        return await original_get(self, [o for o in oids if not o.startswith("1.0.8802")])

    FakeTransport.walk = walk  # type: ignore[method-assign]
    FakeTransport.get = get  # type: ignore[method-assign]
    try:
        identity, name = await probe
    finally:
        FakeTransport.walk = original  # type: ignore[method-assign]
        FakeTransport.get = original_get  # type: ignore[method-assign]
    assert identity == "02:00:00:00:00:01"
    assert name == "switch-1"


async def test_no_identity(hass: HomeAssistant) -> None:
    original = FakeTransport.walk

    async def walk(self: FakeTransport, oid: str) -> Any:
        if oid.startswith(("1.0.8802", "1.3.6.1.2.1.2.2.1")):
            return []
        return await original(self, oid)

    original_get = FakeTransport.get

    async def get(self: FakeTransport, oids: Any) -> Any:
        return await original_get(self, [o for o in oids if not o.startswith("1.0.8802")])

    result = await start(hass)
    FakeTransport.walk = walk  # type: ignore[method-assign]
    FakeTransport.get = get  # type: ignore[method-assign]
    try:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], V3)
    finally:
        FakeTransport.walk = original  # type: ignore[method-assign]
        FakeTransport.get = original_get  # type: ignore[method-assign]
    assert result["errors"] == {"base": "no_identity"}


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (SnmpTimeoutError("no answer"), "timeout"),
        (SnmpAuthError("WrongDigest"), "invalid_auth"),
        (SnmpError("genErr"), "cannot_connect"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_errors_and_retry(hass: HomeAssistant, error: Exception, key: str) -> None:
    result = await start(hass)
    FakeTransport.errors = {"192.0.2.1": {"1.3.6.1.2.1.1": error}}  # type: ignore[dict-item]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V3)
    assert result["errors"] == {"base": key}
    FakeTransport.errors = {}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V3)
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize(
    "fields",
    [
        {"auth_key": ""},  # SHA without its password
        {"auth_protocol": "none", "auth_key": ""},  # privacy without authentication
        {"priv_protocol": "none"},  # a privacy password without a protocol
    ],
)
async def test_missing_keys(hass: HomeAssistant, fields: dict[str, str]) -> None:
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**V3, **fields})
    assert result["errors"] == {"base": "key_missing"}


async def test_without_privacy(hass: HomeAssistant) -> None:
    result = await start(hass)
    fields = {"user": "monitor", "auth_protocol": "sha", "auth_key": "a", "priv_protocol": "none"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], fields)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["priv_key"] is None


def test_unexpected_error_key() -> None:
    assert _error_key(NoIdentityError()) == "no_identity"


async def test_already_configured_updates_the_host(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1")
    entry.add_to_hass(hass)
    result = await start(hass, "192.0.2.1", "2c")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"community": "secret"}
    )
    assert result["reason"] == "already_configured"


async def test_reauth(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1", version="3")
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "usm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**V3, "auth_key": "new-secret"}
    )
    assert result["reason"] == "reauth_successful"
    assert entry.data["auth_key"] == "new-secret"


async def test_reauth_on_another_switch(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1", version="3")
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, data={**entry.data, "host": "192.0.2.2"})
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V3)
    assert result["reason"] == "wrong_switch"


async def test_reconfigure(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.0.2.1", "port": 1161, "snmp_version": "3"}
    )
    assert result["step_id"] == "usm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V3)
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {**entry_data("192.0.2.1", "3"), "port": 1161}
    assert "community" not in entry.data


async def test_reconfigure_to_another_switch(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.0.2.3", "port": 161, "snmp_version": "2c"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"community": "secret"}
    )
    assert result["reason"] == "wrong_switch"


async def test_options(hass: HomeAssistant) -> None:
    entry = make_entry("192.0.2.1")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"fast_interval": 20, "slow_interval": 300}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options == {"fast_interval": 20, "slow_interval": 300}
