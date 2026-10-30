---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

<p class="hero-kicker">Home Assistant · SNMP · read only</p>

# Managed Switch

<p class="hero-lead">Every port of your <strong>managed switches</strong> in Home Assistant: link, speed, PoE, traffic, and which device is connected where, across all your switches.</p>

[Install](installation.md){ .md-button .md-button--primary }
[Source on GitHub](https://github.com/eizedev/ha-managed-switch){ .md-button }

</div>

<div class="cards" markdown>

- [**Installation**](installation.md)<br>HACS, then one entry per switch.
- [**Configuration**](configuration.md)<br>SNMP access on the switch, setup, options.
- [**Entities**](entities.md)<br>Switch and port sensors, what each means.
- [**Events**](events.md)<br>Uplink down, slower port, restart, new device, with a blueprint.
- [**Dashboard**](dashboard.md)<br>A port overview of all switches to paste.
- [**Ideas and automations**](ideas.md)<br>Link lost, slow port, PoE, busy port: examples to copy.
- [**Troubleshooting**](troubleshooting.md)<br>Timeouts, rejected users, missing ports.

</div>

![The example dashboard: every port of three switches with link, speed and the device connected to it](assets/screenshots/dashboard.png)

## Before you start

- Home Assistant 2026.10.3 or newer.
- Read-only SNMP access on every switch (SNMPv3 recommended, v2c works): [SNMP access](configuration.md#snmp-access).
- LLDP on on every switch, and all switches added, so the links between them are recognised.
- Tested on HPE OfficeConnect 1920S and HPE Instant On 1930; other managed switches with the
  standard MIBs are expected to work. Reports are welcome in the
  [issues](https://github.com/eizedev/ha-managed-switch/issues) and
  [discussions](https://github.com/eizedev/ha-managed-switch/discussions).

## How it finds where a device is

Every switch learns the MAC addresses on its ports. The integration reads the address tables of
all your switches, recognises the links between them through LLDP, and places each device on the
one port that is not such a link. The name comes from Home Assistant's device registry: a device
that another integration (your router, a smart TV, a speaker) knows by its MAC address gets that
name. Details: [Locating devices](https://aiosnmpswitch.eize.dev/locating/) in the library's
documentation.

> Not affiliated with any switch vendor. Product names are trademarks of their owners.
