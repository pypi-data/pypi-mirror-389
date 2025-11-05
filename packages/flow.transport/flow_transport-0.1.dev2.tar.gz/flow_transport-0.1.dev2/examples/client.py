from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from flow.transport import ClientLink, FlowProtocol, ReconnectMixin

log = logging.getLogger(__name__)
logging.basicConfig(level="TRACE")


# We define a simple protocol that only prints received data
# Adding a ReconnectMixin will make the protocol attempt to reconnect upon disconnection
class MyClientProtocol(ReconnectMixin, FlowProtocol):
    def on_connect(self, transport: asyncio.Transport) -> None:
        log.info("Protocol connected")

    def on_data(self, data: bytes) -> None:
        log.info("Protocol data received: %s", repr(data))


# An example loop task that periodically sends data using the protocol
async def loop_task_protocol(protocol: MyClientProtocol) -> None:
    while True:
        try:
            protocol.send(b"test from protocol\n")
            await asyncio.sleep(1)
        except asyncio.CancelledError:  # noqa: PERF203
            break


# An example loop task that periodically sends data using the stream
async def loop_task_stream(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    while True:
        try:
            writer.write(b"test from stream\n")
            await writer.drain()
            log.info("Stream data read: %s", await reader.readline())
            await asyncio.sleep(1)
        except asyncio.CancelledError:  # noqa: PERF203
            break


async def main() -> None:
    cafile, certfile, keyfile = [
        (Path(__file__).parent / "../tests/_data" / filename).resolve()
        for filename in ["ca.crt", "client.crt", "client.key"]
    ]

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--uri", default="tcp://127.0.0.1:1337", help="client uri")
    parser.add_argument("--protocol", default=False, action="store_true", help="connect using protocol")
    parser.add_argument("--stream", default=False, action="store_true", help="connect using stream")
    parser.add_argument("--cafile", default=cafile, help="path to TLS CA file")
    parser.add_argument("--certfile", default=certfile, help="path to TLS certificate file")
    parser.add_argument("--keyfile", default=keyfile, help="path to TLS key file")
    args = parser.parse_args()

    if not args.protocol and not args.stream:
        parser.exit("At least one of --protocol or --stream must be specified")

    # We first create a client link
    link = ClientLink.create(
        args.uri,
        cafile=args.cafile,
        certfile=args.certfile,
        keyfile=args.keyfile,
        verify=False,
    )
    if not link.is_client:
        parser.exit(f"URI is not a client URI: {args.uri}")

    tasks = []

    # You can connect to a server using a protocol, callback based method
    if args.protocol:
        # Upon connection, we get an instance of our protocol
        protocol = await link.connect(MyClientProtocol)
        # For demonstration, we start a loop task that periodically sends data
        tasks.append(asyncio.create_task(loop_task_protocol(protocol)))

        # After some time, we close the protocol
        await asyncio.sleep(5)
        protocol.close()

    # ... or by creating a (reader, writer) pair for streaming communication
    if args.stream:
        # Upon connection, we get a (reader, writer) pair
        reader, writer = await link.connect_stream()
        # For demonstration, we start a loop task that periodically sends data
        tasks.append(asyncio.create_task(loop_task_stream(reader, writer)))

        # After some time, we close the stream
        await asyncio.sleep(5)
        writer.close()

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
