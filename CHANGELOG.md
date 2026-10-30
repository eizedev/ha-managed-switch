# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-10-30

### Changed

- A port with several devices is named after the device that describes it best: the internet
  gateway (a device of the UPnP integration), then a device the others are linked to in the device
  registry, then the rest by name. The port to the router no longer shows the first client in the
  alphabet.

### Fixed

- Ports, trunks and PoE ports that appear after setup get their entities without reloading.
- Example dashboard: names keep their brackets and other characters (escaped instead of removed).

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

[Unreleased]: https://github.com/eizedev/ha-managed-switch/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/eizedev/ha-managed-switch/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/eizedev/ha-managed-switch/releases/tag/v0.1.0
