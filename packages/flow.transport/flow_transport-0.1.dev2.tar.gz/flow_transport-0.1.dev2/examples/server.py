from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from flow.transport import FlowProtocol, ServerLink

log = logging.getLogger(__name__)
logging.basicConfig(level="TRACE")


class MyServerProtocol(FlowProtocol):
    def on_connect(self, transport: asyncio.Transport) -> None:
        log.info("Protocol connected")

    def on_data(self, data: bytes) -> None:
        log.info("Protocol data received: %s", repr(data))
        self.send(data.upper())


async def stream_callback(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    log.info("Stream connected")
    while True:
        data = await reader.readline()
        if not data:
            break
        log.info("Stream data read: %s", data)
        writer.write(data.upper())
        await writer.drain()


async def main() -> None:
    cafile, certfile, keyfile = [
        (Path(__file__).parent / "../tests/_data" / filename).resolve()
        for filename in ["ca.crt", "server.crt", "server.key"]
    ]

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--uri", default="tcp://127.0.0.1:1337", help="server uri")
    parser.add_argument("--protocol", default=False, action="store_true", help="serve protocol")
    parser.add_argument("--stream", default=False, action="store_true", help="serve stream")
    parser.add_argument("--cafile", default=cafile, help="path to TLS CA file")
    parser.add_argument("--certfile", default=certfile, help="path to TLS certificate file")
    parser.add_argument("--keyfile", default=keyfile, help="path to TLS key file")
    args = parser.parse_args()

    if not args.protocol and not args.stream:
        parser.exit("At least one of --protocol or --stream must be specified")

    if args.protocol and args.stream:
        parser.exit("Only one of --protocol or --stream can be specified")

    # We first create a server link
    link = ServerLink.create(
        args.uri,
        cafile=args.cafile,
        certfile=args.certfile,
        keyfile=args.keyfile,
        verify=False,
    )
    if not link.is_server:
        parser.exit(f"URI is not a server URI: {args.uri}")

    tasks = []

    # You can serve a protocol, callback based method
    if args.protocol:
        server = await link.serve(MyServerProtocol)
        tasks.append(asyncio.create_task(server.serve_forever()))

    # ... or by registering a callback that receives (reader, writer) pairs for streaming communication
    if args.stream:
        server = await link.serve_stream(stream_callback)
        tasks.append(asyncio.create_task(server.serve_forever()))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
