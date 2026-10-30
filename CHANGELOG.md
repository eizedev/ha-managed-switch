# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-10-30

### Fixed

- `new_device` tells whether the device is alone on its port (`direct`, `devices_on_port`). The
  blueprint reports only devices plugged in directly unless *Only devices plugged in directly*
  is off; a phone joining the router's Wi-Fi was reported as new on the port towards the router
  ([#19](https://github.com/eizedev/ha-managed-switch/issues/19)).

## [0.2.0] - 2026-10-30

### Added

- WebSocket command `managed_switch/ports`: a switch's ports with their kind (port or trunk), trunk
  members, uplinks, PoE and the entity of each role, for the
  [switch card](https://github.com/eizedev/managed-switch-card).
- Docs: the switch card and the command's reply; the demo photographs the card
  (`screenshots.py --card`). The card is installed separately; nothing changes for existing
  switches.
- Screenshots in the README and on the website, from a demo instance (`scripts/demo/`) with three
  stand-in switches answering SNMP from the test data.
- Docs: "Ideas and automations" with six example packages, loaded by the demo on every start.
- Docs: what the SNMP read access must include, what is lost without each MIB, updating,
  entity IDs in other languages, minimum polling intervals, more troubleshooting.

### Fixed

- Port speed without decimal places.

## [0.1.1] - 2026-10-30

### Changed

- A port with several devices is named after the device that describes it best: the internet
  gateway (a device of the UPnP integration), then a device the others are linked to in the device
  registry, then the rest by name. The port to the router no longer shows the first client in the
  alphabet.

### Fixed

- Ports, trunks and PoE ports that appear after setup get their entities without reloading.
- Example dashboard: names keep their brackets and other characters (escaped instead of removed).
- Switches with SNMPv3 users of the same name but different passwords no longer share an SNMP
  engine, where they could replace each other's keys; the setup dialog's test uses an engine of
  its own.
- A device seen again counts as recent for the remembered devices, so a device that is always
  there is not announced as new after 5000 others; a second sysUpTime wrap is no restart either.
- Deprecated `DeviceEntry.config_entries` no longer used.

## [0.1.0] - 2026-10-30

First release.

### Added

- Config flow for SNMPv3 and SNMPv1/v2c, with reauthentication, reconfiguration and options
  for the two polling intervals.
- Per switch: last restart, PoE budget and consumption, spanning tree changes.
- Per port and trunk: link, speed, connected device (LLDP neighbours and the devices located on
  the port across all switches, named from the device registry), PoE status, received and sent
  traffic and errors (off by default).
- Switch events (uplink or trunk down, slower port, restart, new device) and a notification
  blueprint; diagnostics without addresses; an example dashboard.

[Unreleased]: https://github.com/eizedev/ha-managed-switch/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/eizedev/ha-managed-switch/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/eizedev/ha-managed-switch/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/eizedev/ha-managed-switch/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/eizedev/ha-managed-switch/releases/tag/v0.1.0
