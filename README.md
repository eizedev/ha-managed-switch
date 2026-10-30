# Managed Switch (SNMP) for Home Assistant

| HACS | Release | CI | License |
| ---- | ------- | -- | ------- |
| [![HACS custom](https://img.shields.io/badge/HACS-custom-41BDF5?cacheSeconds=3600)](https://hacs.xyz/docs/faq/custom_repositories/) | [![Release](https://img.shields.io/github/v/release/eizedev/ha-managed-switch?cacheSeconds=3600)](https://github.com/eizedev/ha-managed-switch/releases) | [![CI](https://github.com/eizedev/ha-managed-switch/actions/workflows/ci.yml/badge.svg)](https://github.com/eizedev/ha-managed-switch/actions/workflows/ci.yml) | [![License](https://img.shields.io/github/license/eizedev/ha-managed-switch?cacheSeconds=3600)](https://github.com/eizedev/ha-managed-switch/blob/main/LICENSE) |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/eizedev/ha-managed-switch/main/assets/header-dark.svg">
  <img alt="Managed Switch for Home Assistant" src="https://raw.githubusercontent.com/eizedev/ha-managed-switch/main/assets/header-light.svg" height="72">
</picture>

Shows your **managed network switches** in Home Assistant over SNMP: every port with link,
speed, traffic and PoE, and **which device is connected to which port**, across all your
switches, named after the devices Home Assistant already knows. Events tell you when an uplink
or trunk goes down, a port comes back slower, a switch restarts or a new device appears. Read
only: it never changes a setting.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eizedev&repository=ha-managed-switch&category=integration)
[![Open your Home Assistant instance and start setting up the integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=managed_switch)
[![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Feizedev%2Fha-managed-switch%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmanaged_switch%2Fnotify_switch_events.yaml)

**Documentation: [ha-managed-switch.eize.dev](https://ha-managed-switch.eize.dev/)**

<p>
  <img src="https://raw.githubusercontent.com/eizedev/ha-managed-switch/main/docs/assets/screenshots/dashboard.png" alt="The example dashboard: every port of three switches with link, speed and the device connected to it" width="49%">
  <img src="https://raw.githubusercontent.com/eizedev/ha-managed-switch/main/docs/assets/screenshots/device-switch.png" alt="A switch's device page with PoE, port devices, links and speeds" width="49%">
</p>

## What you get

- One device per switch: last restart, PoE budget and consumption, spanning tree changes.
- Per port (and per trunk): link, speed, the connected device (an LLDP neighbour such as
  another switch, or the devices learned on the port, named from Home Assistant's device
  registry), PoE status, and on request received and sent traffic and errors.
- One events entity per switch with a ready blueprint for notifications.
- SNMPv3 (recommended) or v2c, standard MIBs only: vendor-neutral. Tested on HPE OfficeConnect
  1920S and HPE Instant On 1930; other managed switches with SNMP are expected to work.

## Install

In HACS, add this repository as a custom repository of the type *Integration* (or use the button
above), install **Managed Switch (SNMP)** and restart Home Assistant:

```text
https://github.com/eizedev/ha-managed-switch
```

Then add the integration once per switch. Requires Home Assistant 2026.10.3 or newer. Details:
[Installation](https://ha-managed-switch.eize.dev/installation/).

## Documentation

- [Installation](https://ha-managed-switch.eize.dev/installation/) and [Configuration](https://ha-managed-switch.eize.dev/configuration/): SNMP access on the switch, setup, options
- [Entities](https://ha-managed-switch.eize.dev/entities/) and [Events](https://ha-managed-switch.eize.dev/events/): what each one means, the blueprint
- [Dashboard](https://ha-managed-switch.eize.dev/dashboard/): a port overview to paste
- [Ideas and automations](https://ha-managed-switch.eize.dev/ideas/): link lost, slow port, PoE, busy port
- [Troubleshooting](https://ha-managed-switch.eize.dev/troubleshooting/)

The SNMP part is the library [aiosnmpswitch](https://aiosnmpswitch.eize.dev/).

## Roadmap

Planned work is in the [roadmap issues](https://github.com/eizedev/ha-managed-switch/issues?q=is%3Aissue+is%3Aopen+label%3Aroadmap):
a card that shows a switch like its own web interface, PoE power per port, temperatures.

## Contributing

Reports with your switch model help most. See [CONTRIBUTING.md](https://github.com/eizedev/ha-managed-switch/blob/main/CONTRIBUTING.md);
for security issues [SECURITY.md](https://github.com/eizedev/ha-managed-switch/blob/main/SECURITY.md).

## License

[MIT](https://github.com/eizedev/ha-managed-switch/blob/main/LICENSE). Provided "as is", without warranty of any kind. The icon and header images are
CC BY 4.0; their source is in [eizedev/brand](https://github.com/eizedev/brand).
