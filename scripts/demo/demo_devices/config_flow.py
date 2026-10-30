"""The demo devices' config entry, created on startup."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult


class DemoDevicesFlow(ConfigFlow, domain="demo_devices"):
    """One entry, created by the import at startup."""

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Create the entry."""
        return self.async_create_entry(title="Demo devices", data={})
