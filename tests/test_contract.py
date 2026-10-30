"""The integration against the real library: what the fake transport in conftest stands in for."""

from __future__ import annotations

import inspect

from aiosnmpswitch import PysnmpTransport, SnmpSwitch, create_engine

from custom_components.managed_switch.coordinator import SLOW_READS

# Taken when the module is imported, before conftest replaces it for every test.
REAL_CREATE = PysnmpTransport.create
REAL_CREATE_ENGINE = create_engine


def test_every_read_exists_on_the_real_client() -> None:
    names = ["get_system", "get_interfaces", *(getter for _, getter in SLOW_READS)]
    for name in names:
        assert inspect.iscoroutinefunction(getattr(SnmpSwitch, name)), name


def test_the_transport_takes_what_the_integration_passes() -> None:
    # tests replace PysnmpTransport.create; the real one must accept the same arguments
    parameters = inspect.signature(REAL_CREATE).parameters
    for name in ("host", "auth", "port", "timeout", "retries", "engine"):
        assert name in parameters, name
    assert inspect.iscoroutinefunction(REAL_CREATE_ENGINE)
