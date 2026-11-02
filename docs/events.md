# Events

Each switch has an entity *Switch events*. Its state is the time of the last event; the
attribute `event_type` says which:

| Event type | When | Attributes |
| --- | --- | --- |
| `uplink_down` | a link to another of your switches, a trunk or a trunk member lost its link | `port`, `if_index` |
| `speed_dropped` | a port is up at a lower speed than it held before (a bad cable, a port that negotiated 100 Mbit/s); see [Slower ports](#slower-ports) | `port`, `if_index`, `speed`, `previous` |
| `restarted` | the switch booted since the last reading | `boot_time` |
| `new_device` | a device is seen for the first time on any of your switches | `port`, `if_index`, `mac`, `name`, `ip_addresses`, `devices_on_port`, `direct` |

Nothing fires for the state at startup. New devices are remembered across restarts (the 5000
seen most recently); on the very first run, and for a switch that is added or whose address table is read for
the first time, all devices are taken as known. Phones and laptops that use a new random MAC
address for a network now and then appear as new each time.

`direct` is true when the device is alone on its port. On a port that carries several devices
(`devices_on_port`), it sits behind a router, an access point or an unmanaged switch there: a
phone joining the router's Wi-Fi shows up on the port that leads to the router, although nothing
was plugged in. The blueprint reports only direct devices unless you turn that off. The event's attributes, including
MAC and IP addresses, are kept in Home Assistant's history like any other state.

## Slower ports

`speed_dropped` compares a port's speed with the speed it *held*: the speed it had when Home
Assistant started, or one it kept for at least an hour. It fires once the lower speed is read on
two polls in a row, so a real drop is reported one poll after it happens (30 s by default), with
the held speed as `previous`. Afterwards the lower speed is the held one, so a port that falls
back reports it once.

Nothing fires for speeds a port shows only briefly: link negotiation can show 1 Gbit/s for a
few seconds before a 100 Mbit/s device settles, and some devices run faster for a few minutes,
for example a game console installing updates in rest mode. A port that went down keeps its held
speed, so a device plugged in again at a lower speed is reported.

## Blueprint

[![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Feizedev%2Fha-managed-switch%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmanaged_switch%2Fnotify_switch_events.yaml)

*Managed switch events* sends a notification for the events you choose; new devices only when
plugged in directly, unless you turn *Only devices plugged in directly* off. Pick the events entity
of a switch and an action, for example a notification to your phone; by default it creates a
persistent notification.

## In your own automations

```yaml
triggers:
  - trigger: state
    entity_id: event.switch_1_switch_events
conditions:
  - condition: state
    entity_id: event.switch_1_switch_events
    attribute: event_type
    state: uplink_down
actions:
  - action: notify.mobile_app_phone
    data:
      message: "Port {{ trigger.to_state.attributes.port }} lost its link"
```

The entity ID follows the language Home Assistant used when the entity was created: in a German
installation it is `event.switch_1_switch_ereignisse`. Copy it from the entity's settings, or use
the blueprint, which needs no ID.
