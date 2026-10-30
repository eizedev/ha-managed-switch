# Installation

Requires Home Assistant 2026.10.3 or newer.

## In HACS

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eizedev&repository=ha-managed-switch&category=integration)

Or in HACS: the three dots, *Custom repositories*, add this URL with the type *Integration*:

```text
https://github.com/eizedev/ha-managed-switch
```

Install **Managed Switch (SNMP)**, then restart Home Assistant.

## Without HACS

1. Download `managed_switch.zip` from the
   [latest release](https://github.com/eizedev/ha-managed-switch/releases/latest).
2. Optional: check it against the SHA-256 in the release notes, or with the
   [GitHub CLI](https://cli.github.com/):
   `gh attestation verify managed_switch.zip --repo eizedev/ha-managed-switch`.
3. Unpack it into `custom_components/managed_switch/` in your Home Assistant configuration
   folder, so that `manifest.json` ends up directly in it.
4. Restart Home Assistant.

## Updating

HACS shows a new release as an update (also under Settings, Updates). Install it and restart
Home Assistant. Without HACS, replace the folder's content with the new release's zip and
restart. The switches, their entities and settings stay.

## Adding your switches

[![Open your Home Assistant instance and start setting up the integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=managed_switch)

Add the integration once per switch (Settings, Devices & services, Add integration, *Managed
Switch*). Before that, give Home Assistant read access on each switch:
[SNMP access](configuration.md#snmp-access). Add all your switches: only with all of them can
the integration tell the links between switches from the ports your devices are on.
