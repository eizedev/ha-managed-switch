# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/eizedev/ha-managed-switch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/eizedev/ha-managed-switch/releases/tag/v0.1.0
