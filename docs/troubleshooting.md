# Troubleshooting

**"The switch did not answer."** Check the address, that SNMP is enabled on the switch, that no
firewall drops UDP port 161 between Home Assistant and the switch, and the community: with a
wrong community, switches do not answer at all.

**"The switch rejected the SNMPv3 user."** User name, passwords and both protocols must match
exactly what the switch has for the user. Some switches accept only certain password lengths or
characters.

**A port shows the wrong device, or many devices.** Set up all your switches: a switch that is
not set up counts as a device, so everything behind it appears on the port it hangs on. Devices
behind an access point or an unmanaged switch share that port.

**A device is missing.** Switches forget silent devices after a few minutes. It appears again
once it sends something.

**Diagnostics.** The entry's three dots, *Download diagnostics*: counts and structure of what
the switch answers, without addresses, names or credentials. Attach it to an
[issue](https://github.com/eizedev/ha-managed-switch/issues/new/choose).

**Debug logging.** The entry's three dots, *Enable debug logging*; the loggers are
`custom_components.managed_switch`, `aiosnmpswitch` and `pysnmp`.
