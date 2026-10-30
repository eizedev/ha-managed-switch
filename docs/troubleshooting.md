# Troubleshooting

**"The switch did not answer."** Check the address, that SNMP is enabled on the switch, that no
firewall drops UDP port 161 between Home Assistant and the switch, and the community: with a
wrong community, switches do not answer at all.

**"The switch rejected the SNMPv3 user."** User name, passwords and both protocols must match
exactly what the switch has for the user. Some switches accept only certain password lengths or
characters.

**A port shows the wrong device, or many devices.** Set up all your switches and turn LLDP on on
each of them: a switch that is not set up, or that LLDP does not show, counts as a device, so
everything behind it appears on the port it hangs on. Devices
behind an access point or an unmanaged switch share that port.

**A device is missing.** Switches forget silent devices after a few minutes. It appears again
once it sends something.

**Entities are unavailable.** The switch did not answer the last reading (see the first entry),
or a port no longer exists on it. Entities of a port that is gone for good can be removed on the
entity's page.

**Received, sent and errors are missing.** They are off by default: Settings, Devices & services,
Managed Switch (SNMP), the switch, then the entities not shown, and enable the ones you want.

**Received and sent stay unknown.** They need the 64-bit counters (`ifXTable`), which SNMPv1
and some small switches do not offer.

**Diagnostics.** The entry's three dots, *Download diagnostics*: counts and structure of what
the switch answers, without addresses, names or credentials. Attach it to an
[issue](https://github.com/eizedev/ha-managed-switch/issues/new/choose).

**Debug logging.** The entry's three dots, *Enable debug logging*; the loggers are
`custom_components.managed_switch`, `aiosnmpswitch` and `pysnmp`. Read a debug log before you
share it: pysnmp may log the requests it sends, and with SNMPv1 or v2c those carry the community.
