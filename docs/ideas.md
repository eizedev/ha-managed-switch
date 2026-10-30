# Ideas and automations

What you can do with the entities, with examples to copy. Each example is a
[package](https://www.home-assistant.io/docs/configuration/packages/): put the file into a
`packages` folder next to `configuration.yaml` and add

```yaml
homeassistant:
  packages: !include_dir_named packages
```

once, then restart. Or create the same automation in the editor (*Settings, Automations*, three
dots, *Edit in YAML*) from the part below `automation:`. Replace the entity IDs with yours (copy
them from the entity's settings; in another language than English they differ, see
[Entities](entities.md)), and `notify.mobile_app_phone` with your phone's notify action.

For uplinks, trunks, slower ports, restarts and new devices there is a ready
[blueprint](events.md#blueprint); the examples here are for single devices you care about.

## A wired device lost its link

```yaml
--8<-- "docs/assets/ideas/link_lost.yaml"
```

## A port runs slower than it should

A cable with a broken pair or a dirty plug often still works, at 100 Mbit/s instead of 1 Gbit/s.

```yaml
--8<-- "docs/assets/ideas/slow_port.yaml"
```

## A PoE device lost its power

```yaml
--8<-- "docs/assets/ideas/poe_lost.yaml"
```

## Something else is plugged into a port

```yaml
--8<-- "docs/assets/ideas/device_moved.yaml"
```

## A switch does not answer

```yaml
--8<-- "docs/assets/ideas/switch_unreachable.yaml"
```

## A port is busy for a long time

```yaml
--8<-- "docs/assets/ideas/busy_port.yaml"
```

Every example is loaded by the demo instance (`scripts/demo/run.py`) on each start, so a change
that breaks one shows there.
