# Events

Each switch has an entity *Switch events*. Its state is the time of the last event; the
attribute `event_type` says which:

| Event type | When | Attributes |
| --- | --- | --- |
| `uplink_down` | a link to another of your switches, a trunk or a trunk member lost its link | `port`, `if_index` |
| `speed_dropped` | a port is up at a lower speed than it had before (a bad cable, a port that negotiated 100 Mbit/s) | `port`, `if_index`, `speed`, `previous` |
| `restarted` | the switch booted since the last reading | `boot_time` |
| `new_device` | a device is seen for the first time on any of your switches | `port`, `if_index`, `mac`, `name`, `ip_addresses` |

Nothing fires for the state at startup. New devices are remembered across restarts (the 5000
seen most recently); on the very first run, and for a switch that is added or whose address table is read for
the first time, all devices are taken as known. Phones and laptops that use a new random MAC
address for a network now and then appear as new each time. The event's attributes, including
MAC and IP addresses, are kept in Home Assistant's history like any other state.

## Blueprint

[![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Feizedev%2Fha-managed-switch%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmanaged_switch%2Fnotify_switch_events.yaml)

*Managed switch events* sends a notification for the events you choose. Pick the events entity
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
