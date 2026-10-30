# Contributing

Thanks for helping. Reports from switches that are not tested yet help most: other vendors,
models and firmware versions.

## Reporting a problem

Use the **Bug report** form and attach the integration's diagnostics (*Settings, Devices &
services, Managed Switch (SNMP), the three dots, Download diagnostics*). They contain no
addresses, names or secrets. Never paste raw SNMP output or unredacted logs.

How well a switch is supported depends on the library
[aiosnmpswitch](https://github.com/eizedev/aiosnmpswitch); its `aiosnmpswitch-diagnostics`
command describes what a switch answers, without any values.

## Development setup

```sh
uv sync
uv run pytest --cov
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

The tests run against anonymized recordings of three real switches (`tests/fixtures/`, made
with the library's diagnostics and anonymizer); they need no switch and no running Home
Assistant.

## Rules for changes

- **Read only.** The integration never changes a switch setting.
- **Texts in two languages.** Every user-facing text goes into `strings.json`,
  `translations/en.json` and `translations/de.json`.
- **No personal data** in code, docs or test data.
- `tests/test_privacy.py` fails on MAC and IP addresses that may be real, in the files and in
  every line your unpushed commits add. Run the tests before you push: removing an address in a
  later commit leaves it in the history, so fix the commit that added it instead.
- Update the docs and [CHANGELOG.md](CHANGELOG.md) in the same pull request.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

## Releases

Releases come from a tag `vX.Y.Z` on `main`:

1. In a pull request, rename `[Unreleased]` in CHANGELOG.md to `[X.Y.Z] - <date>`, add an empty
   `[Unreleased]` above it and the compare links below, and set `version` in `manifest.json` to
   `X.Y.Z` (a test checks that the manifest's version has a changelog section).
2. After the merge, wait for the *Docs* run (the release notes link the website), then tag the
   commit the merge created on `main` (not the pull request's own commits, which a squash merge
   leaves out) `vX.Y.Z` and push the tag.
3. `.github/workflows/release.yml` runs the checks again, refuses a tag that is not on `main` or
   does not match the manifest, and creates the GitHub release: the changelog section as notes,
   `managed_switch.zip` for manual installs with its SHA-256 and build provenance.

HACS offers each GitHub release (not the default branch).

If a run fails, fix the cause and re-run the failed job; the release step updates an existing
release. A wrong tag (not on `main`, or not matching the manifest) fails before anything is
published. Tags `v*` cannot be moved or deleted except by an administrator (ruleset "Release
tags"): delete it with the bypass, fix `main` in a pull request, and tag again.
