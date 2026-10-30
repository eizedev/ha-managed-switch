# Switch card

[managed-switch-card](https://github.com/eizedev/managed-switch-card) draws a switch like its own
web interface: every port coloured by link and speed, uplinks to other switches, trunk members,
PoE delivering power, and the device on each port.

![Three switches as cards: green ports at 1 Gbit/s, orange at 100 Mbit/s, white without link, arrows on the links between the switches, the device name under each port](assets/screenshots/card.png)

## Install

The card needs this integration in version 0.2.0 or newer.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eizedev&repository=managed-switch-card&category=plugin)

Or in HACS: the three dots, *Custom repositories*, add this URL with the type *Dashboard*:

```text
https://github.com/eizedev/managed-switch-card
```

Install **Managed Switch Card** and reload the browser. Then edit a dashboard, *Add card*,
**Managed Switch**, and choose the switch. One card per switch.

## What it shows

| On a port | Meaning |
| --- | --- |
| green | link at 1 Gbit/s or more |
| orange | link at 100 Mbit/s |
| red | link at 10 Mbit/s |
| blue | link, speed unknown (the port's speed sensor is off or has no value) |
| empty | no link |
| grey | unknown: the switch did not answer, or the port's link sensor is off |
| arrow | link to another of your switches |
| flash | PoE delivering power |
| T | member of a trunk; the trunks are listed below the ports |

Under each port is the device connected to it, as the port's device sensor names it
([Entities](entities.md)). Hovering over a port shows all devices on it (screen readers read the
same); a click opens the device sensor. The header shows the switch's PoE consumption and budget.

While Home Assistant starts or a switch is set up again, the card keeps its last picture and tries
again after 15 seconds. With an integration older than 0.2.0 it says so.

## Options

```yaml
type: custom:managed-switch-card
device_id: 0123456789abcdef0123456789abcdef  # the switch, chosen in the card's dialog
title: Hallway                               # optional, else the switch's name
show_names: true                             # device names under the ports (default)
show_rates: false                            # data rates (↓ in, ↑ out, Mbit/s); turn on the
                                             # ports' "received" and "sent" sensors first
layout:                                      # optional: your own front panel, by port name
  rows:
    - ["1", "3", "5", "7"]
    - ["2", "4", "6", "8"]
  sfp: ["9", "10"]
```

The card knows the front panel of the tested models (HPE OfficeConnect 1920S 8G, HPE Instant On
1930 8G 2SFP). Other switches get their ports in one row, or odd numbers above even ones beyond
twelve; `layout` draws them as your switch looks. A layout for your model is welcome in the
[card's repository](https://github.com/eizedev/managed-switch-card/blob/main/CONTRIBUTING.md).

## For developers: what the card reads

The card asks the integration with the WebSocket command `managed_switch/ports` and a switch's
`device_id`. Every logged-in user may ask, as for entity states; the reply holds the switch's
model, firmware and port descriptions, no address or credentials. A device that is not a loaded
managed switch gives the error `not_found`.

```json
{
  "switch": {"entry_id": "…", "name": "Hallway", "vendor": "HPE", "model": "…",
             "firmware": "…", "object_id": "1.3.6.1.4.1.…",
             "entities": {"boot_time": "sensor.…", "poe_consumption": "sensor.…",
                          "poe_budget": "sensor.…", "port_event": "event.…"}},
  "ports": [
    {"if_index": 1, "name": "1", "alias": "…", "kind": "ethernet", "trunk": null,
     "members": [], "uplink": false, "poe": true,
     "entities": {"link": "binary_sensor.…", "speed": "sensor.…", "device": "sensor.…",
                  "poe": "sensor.…", "received": "sensor.…", "sent": "sensor.…",
                  "errors": "sensor.…"}}
  ]
}
```

`kind` is `ethernet` or `trunk`; a trunk lists its members' `if_index` in `members`, and a member
names its trunk in `trunk`. An entity the integration does not create for a port (PoE on a trunk or on
a port without PoE) is `null`; disabled entities are
listed. Renaming or removing a field is a breaking change of the integration.
