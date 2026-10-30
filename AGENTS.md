# AGENTS.md

Instructions for AI coding agents working on this repository. People should read
[CONTRIBUTING.md](CONTRIBUTING.md) first; this file adds what an agent tends to get wrong.

## What this is

A Home Assistant custom integration (domain `managed_switch`) for managed network switches over
SNMP. It reads only, through the library [aiosnmpswitch](https://github.com/eizedev/aiosnmpswitch);
every request to a switch goes through that library.

## Commands

```sh
uv sync                       # environment from uv.lock (Home Assistant and its test harness)
uv run pytest --cov           # coverage must stay at 100 %
uv run ruff check . && uv run ruff format --check .
uv run mypy                   # strict
```

hassfest and the HACS check run in CI only.

## Rules that matter here

- **One config entry per switch**, identified by its MAC address (LLDP chassis ID, else the
  lowest port MAC). Device locations are combined across all entries in `coordinator.NetworkHub`
  with `aiosnmpswitch.helpers.locate_macs()`; never read another entry's switch from an entry.
- **Coordinators poll, entities never do.** Fast coordinator: interfaces (link, speed, counters,
  rates). Slow coordinator: system, then the optional reads in `SLOW_READS`; a failing optional
  read keeps its last value, only the system read failing fails the update.
- **Stable identities for the planned card**: entity unique IDs are
  `<switch MAC>_<ifIndex>_<key>` and `<switch MAC>_<key>`, each entity has a fixed
  `translation_key`. Do not rename keys.
- **Names of devices** come from the device registry (`devices.registry_name`), never from this
  integration's own devices. The device list is an unrecorded attribute.
- **Errors**: `SnmpAuthError` raises `ConfigEntryAuthFailed` (reauth); everything else is
  `UpdateFailed` or `ConfigEntryNotReady`. Messages come from `strings.json` (`exceptions`).
- **Texts**: every user-facing text is in `strings.json` and in both `translations/en.json` and
  `translations/de.json`.
- **Schemas use `probatio`**, not voluptuous.
- **No personal data** in code, docs or tests. Test data are the library's anonymized recordings
  in `tests/fixtures/`.
- **Docs describe the current state**: update `README.md`, `docs/` and `CHANGELOG.md` (Keep a
  Changelog, under `[Unreleased]`) in the same change. Commit messages follow Conventional
  Commits.
- **`.claude/settings.json`** keeps claude.ai session links out of commits and pull requests
  (`attribution.sessionUrl: false`) and denies reads of secret files. Cloud sessions read only
  this settings file, so keep these keys.
- **Website**: `docs/` and `zensical.toml` are https://ha-managed-switch.eize.dev/, built by
  `.github/workflows/docs.yml` with the shared design from eizedev/brand (`docs-site/`);
  `docs/assets/site.css` is copied in at build time and not committed. Help links in the config
  flow point to sections of `docs/configuration.md` (`DOCS_*` in `config_flow.py`). The example
  dashboard lives once, in `docs/assets/example-dashboard.yaml`; the blueprint in `blueprints/`.

- **Screenshots** come from the demo instance in `scripts/demo/` (CONTRIBUTING.md, "Demo instance
  and screenshots"); regenerate them when dialogs or pages change, never take them from a real
  network.

## Don'ts

- Don't contact real switches from tests; use `tests/conftest.py`'s `FakeTransport`.
- Don't add write actions (services, switches, buttons that change a switch).
- Don't edit `uv.lock` by hand.
