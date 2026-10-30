# Entities

## Per switch

| Entity | Meaning |
| --- | --- |
| Last restart | when the switch's SNMP agent started (diagnostic) |
| PoE budget | power the switch can deliver, watts (switches with PoE) |
| PoE consumption | power the powered devices draw, watts |
| Spanning tree changes | how often the topology changed since the restart (off by default) |
| Switch events | see [Events](events.md) |

## Per port

Ports are the switch's Ethernet ports and its trunks (link aggregations) with members. Each
entity is named after the port as the switch names it, for example *Port 7 link* or *Port TRK 1
link*.

| Entity | Meaning |
| --- | --- |
| Port … link | on while the port has a link |
| Port … speed | link speed in Mbit/s, 0 without link |
| Port … device | what is connected: see below |
| Port … PoE | PoE state of the port: searching, delivering power, fault, … (PoE ports only) |
| Port … received, sent | traffic in bit/s over the last polling interval (off by default) |
| Port … errors | received and sent errors since the restart (off by default) |

### Port … device

The state is the name of the device on the port; when there are several, the first name and how
many more (`Access point +8`). The attribute `devices` lists all of them with MAC address, name,
IP addresses (if a switch knows them) and whether the device announced itself by LLDP.

- An **LLDP neighbour** (another switch, an access point or phone that sends LLDP) comes first,
  by the name it announces.
- Other devices are named from Home Assistant's device registry: any device of another
  integration with that MAC address. Unknown devices show their MAC address.
- Several devices on one port mean something is between: an access point with its Wi-Fi
  clients, a router, or an unmanaged switch.
- The links between your switches show the other switch, not everything behind it, as long as
  all switches are set up.

The list of devices is not recorded in the history, only the state.
