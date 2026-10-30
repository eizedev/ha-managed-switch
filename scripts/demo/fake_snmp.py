r"""Stand-in switches: an SNMPv2c agent per recording in tests/fixtures, on 127.0.0.1.

    python scripts/demo/fake_snmp.py [--first-port 16101]

Each recording answers on its own UDP port (16101, 16102, 16103 by default) to any community,
with GET, GETNEXT and GETBULK; nothing is written. The recordings are the anonymized test data,
so no real network is involved. The value types the recordings do not keep (counter, gauge,
time ticks) come from the MIB columns below.
"""

from __future__ import annotations

import argparse
import asyncio
import bisect
from pathlib import Path
import sys
import time
from typing import Any

from aiosnmpswitch.diagnostics import load_recording
from aiosnmpswitch.transport import ObjectId, Value, oid_key
from pyasn1.codec.ber import decoder, encoder
from pysnmp.proto import api, rfc1902

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
RECORDINGS = [
    FIXTURES / "hpe-1920s-pd.02.22" / "switch-1.json",
    FIXTURES / "hpe-1920s-pd.02.22" / "switch-2.json",
    FIXTURES / "hpe-1930-3.4.0.0" / "switch-3.json",
]
COUNTER32 = (
    "1.3.6.1.2.1.2.2.1.1",
    "1.3.6.1.2.1.31.1.1.1.2",
    "1.3.6.1.2.1.31.1.1.1.3",
    "1.3.6.1.2.1.31.1.1.1.4",
    "1.3.6.1.2.1.31.1.1.1.5",
    "1.3.6.1.2.1.17.2.4",
    "1.3.6.1.2.1.105.1.1.1.11",
)
COUNTER64 = (
    "1.3.6.1.2.1.31.1.1.1.6",
    "1.3.6.1.2.1.31.1.1.1.7",
    "1.3.6.1.2.1.31.1.1.1.8",
    "1.3.6.1.2.1.31.1.1.1.9",
    "1.3.6.1.2.1.31.1.1.1.10",
    "1.3.6.1.2.1.31.1.1.1.11",
    "1.3.6.1.2.1.31.1.1.1.12",
    "1.3.6.1.2.1.31.1.1.1.13",
)
GAUGE32 = (
    "1.3.6.1.2.1.2.2.1.5",
    "1.3.6.1.2.1.31.1.1.1.15",
    "1.3.6.1.2.1.105.1.3.1.1.2",
    "1.3.6.1.2.1.105.1.3.1.1.4",
)
TIMETICKS = (
    "1.3.6.1.2.1.1.3",
    "1.3.6.1.2.1.2.2.1.9",
    "1.3.6.1.2.1.17.2.3",
    "1.0.8802.1.1.2.1.4.1.1.1",
    "1.3.6.1.2.1.4.35.1.5",
)
# ifTable counters (ifInOctets ... ifOutErrors): columns 10 to 20
IF_TABLE_COUNTERS = tuple(f"1.3.6.1.2.1.2.2.1.{n}" for n in range(10, 21))


def _under(oid: str, prefixes: tuple[str, ...]) -> bool:
    return any(oid == p or oid.startswith(p + ".") for p in prefixes)


def typed(oid: str, value: Value) -> Any:
    """Return the recorded value as the SNMP type its MIB column has."""
    if isinstance(value, ObjectId):
        return rfc1902.ObjectIdentifier(str(value))
    if isinstance(value, bytes):
        return rfc1902.OctetString(value)
    for prefixes, kind in (
        (COUNTER64, rfc1902.Counter64),
        (COUNTER32 + IF_TABLE_COUNTERS, lambda v: rfc1902.Counter32(v % 2**32)),
        (GAUGE32, rfc1902.Gauge32),
        (TIMETICKS, rfc1902.TimeTicks),
    ):
        if _under(oid, prefixes):
            return kind(value)
    return rfc1902.Integer32(value)


SYS_UP_TIME = "1.3.6.1.2.1.1.3.0"


class Agent(asyncio.DatagramProtocol):
    """Answers GET, GETNEXT and GETBULK from one recording; sysUpTime keeps counting."""

    def __init__(self, values: dict[str, Value]) -> None:
        """Serve ``values``, a recording."""
        self.started = time.monotonic()
        self.oids = sorted(values, key=oid_key)
        self.keys = [oid_key(o) for o in self.oids]
        self.values = values
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: Any) -> None:
        """Keep the socket to answer on."""
        self.transport = transport

    def value(self, oid: str) -> Value | None:
        """Return the recorded value; sysUpTime counts on from the start of the agent."""
        value = self.values.get(oid)
        if oid == SYS_UP_TIME and isinstance(value, int):
            return value + int((time.monotonic() - self.started) * 100)
        return value

    def _next(self, oid: str) -> str | None:
        index = bisect.bisect_right(self.keys, oid_key(oid))
        return self.oids[index] if index < len(self.oids) else None

    def datagram_received(self, data: bytes, addr: Any) -> None:
        """Answer one request."""
        version = int(api.decodeMessageVersion(data))
        module = api.PROTOCOL_MODULES[version]
        message, _ = decoder.decode(data, asn1Spec=module.Message())
        request = module.apiMessage.get_pdu(message)
        response = module.apiPDU.get_response(request)
        binds: list[tuple[Any, Any]] = []
        names = [str(name) for name, _ in module.apiPDU.get_varbinds(request)]
        if request.isSameTypeWith(module.GetRequestPDU()):
            for name in names:
                value = self.value(name)
                missing = module.NoSuchInstance()
                binds.append((name, typed(name, value) if value is not None else missing))
        else:
            repetitions = 1
            bulk = request.isSameTypeWith(module.GetBulkRequestPDU())
            if version == api.SNMP_VERSION_2C and bulk:
                repetitions = max(1, int(module.apiBulkPDU.get_max_repetitions(request)))
            for name in names:
                current = name
                for _ in range(repetitions):
                    nxt = self._next(current)
                    if nxt is None:
                        binds.append((current, module.EndOfMibView()))
                        break
                    binds.append((nxt, typed(nxt, self.value(nxt))))
                    current = nxt
        module.apiPDU.set_varbinds(response, binds)
        module.apiMessage.set_pdu(message, response)
        if self.transport is not None:
            self.transport.sendto(encoder.encode(message), addr)


async def main(first_port: int) -> None:
    """Start one agent per recording and run until stopped."""
    loop = asyncio.get_running_loop()
    for number, path in enumerate(RECORDINGS):
        port = first_port + number
        await loop.create_datagram_endpoint(
            lambda path=path: Agent(load_recording(path)), local_addr=("127.0.0.1", port)
        )
        print(f"{path.stem}: udp://127.0.0.1:{port}", flush=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else None)
    parser.add_argument("--first-port", type=int, default=16101)
    try:
        asyncio.run(main(parser.parse_args().first_port))
    except KeyboardInterrupt:
        sys.exit(0)
