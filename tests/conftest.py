"""Switches answering from anonymized recordings of a real network.

switch-1 and switch-2 are HPE OfficeConnect 1920S, switch-3 an HPE Instant On 1930; they are
linked by LLDP (switch-1 port 7 to switch-2, port 5 to switch-3), switch-2 port 4 has an access
point with its Wi-Fi clients, switch-1 port 1 the router.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any, ClassVar

from aiosnmpswitch import PysnmpTransport, RecordedTransport, SnmpError, Value
from aiosnmpswitch.diagnostics import load_recording
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.managed_switch.const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    CONF_USER,
    DOMAIN,
)

FIXTURES = Path(__file__).parent / "fixtures"
HOSTS = {
    "192.0.2.1": FIXTURES / "hpe-1920s-pd.02.22" / "switch-1.json",
    "192.0.2.2": FIXTURES / "hpe-1920s-pd.02.22" / "switch-2.json",
    "192.0.2.3": FIXTURES / "hpe-1930-3.4.0.0" / "switch-3.json",
}
# The switches' MAC addresses (LLDP chassis IDs in the recordings): the config entries' unique IDs.
UNIQUE_IDS = {
    "192.0.2.1": "02:00:00:00:00:02",
    "192.0.2.2": "02:00:00:00:00:0a",
    "192.0.2.3": "02:00:00:00:00:19",
}
TITLES = {"192.0.2.1": "switch-1", "192.0.2.2": "switch-2", "192.0.2.3": "switch-3"}


class FakeTransport(RecordedTransport):
    """A recording; tests can make reads below an OID fail, or change values."""

    instances: ClassVar[list[FakeTransport]] = []
    errors: ClassVar[dict[str, dict[str, SnmpError]]] = {}
    """By host, then by OID prefix: the error a read below that OID raises."""

    def __init__(self, host: str, values: dict[str, Value], options: dict[str, Any]) -> None:
        super().__init__(values)
        self.host = host
        self.options = options
        self.closed = False
        FakeTransport.instances.append(self)

    def _raise(self, oid: str) -> None:
        for prefix, error in FakeTransport.errors.get(self.host, {}).items():
            if oid == prefix or oid.startswith(prefix + "."):
                raise error

    def set(self, oid: str, value: Value) -> None:
        self._values[oid] = value

    async def get(self, oids: Any) -> dict[str, Value]:
        for oid in oids:
            self._raise(oid)
        return await super().get(oids)

    async def walk(self, oid: str) -> list[tuple[str, Value]]:
        self._raise(oid)
        return await super().walk(oid)

    async def close(self) -> None:
        self.closed = True


def transport(host: str) -> FakeTransport:
    """The newest fake transport created for ``host``."""
    return next(t for t in reversed(FakeTransport.instances) if t.host == host)


@pytest.fixture(autouse=True)
def fake_snmp(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Every switch answers from its recording; an unknown host cannot be resolved."""

    async def create(host: str, auth: Any, **options: Any) -> FakeTransport:
        if host not in HOSTS:
            raise SnmpError("cannot resolve the switch address: gaierror")
        return FakeTransport(host, load_recording(HOSTS[host]), {"auth": auth, **options})

    FakeTransport.instances = []
    FakeTransport.errors = {}
    monkeypatch.setattr(PysnmpTransport, "create", create)
    yield
    FakeTransport.errors = {}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load the integration from custom_components."""


def entry_data(host: str, version: str = "2c") -> dict[str, Any]:
    if version == "3":
        return {
            "host": host,
            "port": 161,
            CONF_SNMP_VERSION: "3",
            CONF_USER: "monitor",
            CONF_AUTH_PROTOCOL: "sha",
            CONF_AUTH_KEY: "auth-secret",
            CONF_PRIV_PROTOCOL: "des",
            CONF_PRIV_KEY: "priv-secret",
        }
    return {"host": host, "port": 161, CONF_SNMP_VERSION: version, CONF_COMMUNITY: "secret"}


def make_entry(host: str, version: str = "2c", **options: Any) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=TITLES[host],
        unique_id=UNIQUE_IDS[host],
        data=entry_data(host, version),
        options=options,
    )


def state(hass: Any, entity_id: str) -> Any:
    """The state of ``entity_id``, which must exist."""
    current = hass.states.get(entity_id)
    assert current is not None, entity_id
    return current
