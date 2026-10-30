# Security Policy

## Scope

This integration only reads from managed switches over SNMP, through the library
[aiosnmpswitch](https://github.com/eizedev/aiosnmpswitch). In scope: anything in this repository
that could leak a community or SNMPv3 passwords, change a switch setting, or let a malicious
switch answer harm Home Assistant. Problems in the library itself are best
reported there.

Vulnerabilities in a switch's firmware belong to its vendor.

## Reporting a vulnerability

Please report privately via GitHub's
[Report a vulnerability](https://github.com/eizedev/ha-managed-switch/security/advisories/new)
(`Security` tab, `Advisories`, `Report a vulnerability`), not in a public issue. This opens a
private discussion until a fix is released. If you cannot use GitHub, email `oss@eize.dev`
instead.

Please include the integration and Home Assistant versions, your switch model and firmware, and how to reproduce it.
Do not include communities, passwords or unredacted SNMP output.

## Supported versions

Only the [latest release](https://github.com/eizedev/ha-managed-switch/releases/latest) receives
fixes.

## What to expect

This is a community-maintained project without a service level. Reports are read and taken
seriously; confirmed vulnerabilities are fixed and released as soon as practical.
