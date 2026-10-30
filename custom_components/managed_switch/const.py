"""Constants for the Managed Switch (SNMP) integration."""

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "managed_switch"
LOGGER = logging.getLogger(__package__)

CONF_SNMP_VERSION: Final = "snmp_version"
CONF_COMMUNITY: Final = "community"
CONF_USER: Final = "user"
CONF_AUTH_PROTOCOL: Final = "auth_protocol"
CONF_AUTH_KEY: Final = "auth_key"
CONF_PRIV_PROTOCOL: Final = "priv_protocol"
CONF_PRIV_KEY: Final = "priv_key"
CONF_FAST_INTERVAL: Final = "fast_interval"
CONF_SLOW_INTERVAL: Final = "slow_interval"

DEFAULT_PORT: Final = 161
# Ports, link and traffic change quickly; the address table, LLDP, PoE and spanning tree slowly.
DEFAULT_FAST_INTERVAL: Final = timedelta(seconds=30)
DEFAULT_SLOW_INTERVAL: Final = timedelta(minutes=2)
MIN_FAST_INTERVAL: Final = 10
MIN_SLOW_INTERVAL: Final = 60
# One SNMP request may take this long per try; a walk is many requests.
REQUEST_TIMEOUT: Final = 5.0
REQUEST_RETRIES: Final = 1

DOCS_URL: Final = "https://ha-managed-switch.eize.dev/"

# Vendor names by IANA enterprise number, the 7th part of sysObjectID (1.3.6.1.4.1.<n>).
VENDORS: Final = {
    9: "Cisco",
    11: "HPE",
    171: "D-Link",
    674: "Dell",
    890: "Zyxel",
    2636: "Juniper",
    4526: "Netgear",
    11863: "TP-Link",
    14988: "MikroTik",
    41112: "Ubiquiti",
}
