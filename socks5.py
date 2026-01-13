#!/usr/bin/env python3

import sys
import asyncio
import logging
import socket
import struct
import argparse
import daemon
from daemon import pidfile

import util

__NAME__ = 'ZZSocks5Proxy'
__VERSION__ = "1.0"

logger = logging.getLogger('zzapp')


class Socks5Proxy:
    def __init__(self, host, port, user=None, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    async def start(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        addr = server.sockets[0].getsockname()
        logger.info(f"Serving SOCKS5 on {addr[0]}:{addr[1]}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        addr = ':'.join([str(x) for x in writer.get_extra_info('peername')])
        logger.debug(f"Accepted connection from {addr}")

        try:
            # SOCKS5 Handshake
            version, nmethods = await reader.readexactly(2)
            if version != 5:
                logger.warning(f"Unsupported SOCKS version {version} from {addr}")
                return
            methods = await reader.readexactly(nmethods)

            auth_method = 0xFF  # No acceptable methods
            if self.user and self.password:
                auth_method = 2  # Username/Password Authentication
            elif 0 in methods:
                auth_method = 0  # No Authentication Required

            writer.write(struct.pack('!BB', 5, auth_method))
            await writer.drain()

            if auth_method == 0xFF:
                logger.warning(f"No acceptable authentication methods for {addr}.")
                return

            if auth_method == 2:
                if not await self.authenticate(reader, writer, addr):
                    return

            # SOCKS5 Request
            version, cmd, rsv, atyp = await reader.readexactly(4)
            if version != 5 or rsv != 0:
                logger.warning(f"Malformed SOCKS request from {addr}")
                return

            if atyp == 1:  # IPv4
                dest_addr_raw = await reader.readexactly(4)
                dest_addr = socket.inet_ntoa(dest_addr_raw)
            elif atyp == 3:  # Domain name
                domain_len = await reader.readexactly(1)
                dest_addr_raw = await reader.readexactly(domain_len[0])
                dest_addr = dest_addr_raw.decode('utf-8')
            elif atyp == 4:  # IPv6
                dest_addr_raw = await reader.readexactly(16)
                dest_addr = socket.inet_ntop(socket.AF_INET6, dest_addr_raw)
            else:
                logger.warning(f"Unsupported address type {atyp} from {addr}")
                return

            dest_port_raw = await reader.readexactly(2)
            dest_port = struct.unpack('!H', dest_port_raw)[0]

            if cmd == 1:  # CONNECT
                await self.handle_connect(reader, writer, addr, dest_addr, dest_port)
            else:
                logger.warning(f"Unsupported command {cmd} from {addr}")
                # Send failure response
                writer.write(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00')  # Command not supported
                await writer.drain()
                return

        except asyncio.IncompleteReadError:
            logger.warning(f"Client {addr} disconnected unexpectedly.")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}", exc_info=True)
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            logger.debug(f"Connection to {addr} is fully closed.")

    async def authenticate(self, reader, writer, addr):
        try:
            ver = await reader.readexactly(1)
            if ver[0] != 1:
                logger.warning(f"Invalid auth version from {addr}")
                return False

            ulen = await reader.readexactly(1)
            user = (await reader.readexactly(ulen[0])).decode('utf-8')

            plen = await reader.readexactly(1)
            password = (await reader.readexactly(plen[0])).decode('utf-8')

            if user == self.user and password == self.password:
                writer.write(b'\x01\x00')  # Success
                await writer.drain()
                logger.info(f"Successful auth from {addr} for user '{user}'")
                return True
            else:
                writer.write(b'\x01\x01')  # Failure
                await writer.drain()
                logger.warning(f"Failed auth from {addr} for user '{user}'")
                return False
        except asyncio.IncompleteReadError:
            logger.warning(f"Client {addr} disconnected during authentication.")
            return False

    async def handle_connect(self, client_reader, client_writer, client_addr, dest_addr, dest_port):
        logger.info(f"[{client_addr}] CONNECT request to {dest_addr}:{dest_port}")
        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(dest_addr, dest_port)
        except Exception as e:
            logger.error(f"[{client_addr}] Failed to connect to {dest_addr}:{dest_port}: {e}")
            # Send failure response
            client_writer.write(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')  # Host unreachable
            await client_writer.drain()
            return

        # Send success response
        # REP: 0x00 (succeeded), RSV: 0x00, ATYP: 0x01 (IPv4), BND.ADDR/BND.PORT: 0s
        client_writer.write(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        await client_writer.drain()

        await self.pipe_bi(client_reader, client_writer, upstream_reader, upstream_writer)

    @staticmethod
    async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, source_peer: str, dest_peer: str):
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except asyncio.CancelledError:
            raise
        except (ConnectionResetError, BrokenPipeError):
            logger.debug(f"Connection reset/broken from {source_peer} to {dest_peer}.")
        except Exception as e:
            logger.error(f"Pipe error from {source_peer} to {dest_peer}: {e}", exc_info=True)
        finally:
            if not writer.is_closing():
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    @staticmethod
    async def pipe_bi(reader1, writer1, reader2, writer2):
        peer1 = ':'.join([str(x) for x in writer1.get_extra_info('peername')])
        peer2 = ':'.join([str(x) for x in writer2.get_extra_info('peername')])
        logger.debug(f"Piping data between {peer1} and {peer2}")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(Socks5Proxy.pipe(reader1, writer2, peer1, peer2), name=f"pipe_{peer1}_to_{peer2}")
            tg.create_task(Socks5Proxy.pipe(reader2, writer1, peer2, peer1), name=f"pipe_{peer2}_to_{peer1}")

        logger.debug(f"Pipe between {peer1} and {peer2} finished.")


def usage():
    parser = argparse.ArgumentParser(description=f'{__NAME__}')
    parser.add_argument('-H', '--host', type=str, dest="host", default='127.0.0.1',
                        help="Host to bind to [default: 127.0.0.1]")
    parser.add_argument('-P', '--port', type=int, dest="port", default='1080',
                        help="Port to bind to [default: 1080]")
    parser.add_argument('-u', '--user', type=str, dest="user", default=None,
                        help="Username for authentication")
    parser.add_argument('-p', '--password', type=str, dest="password", default=None,
                        help="Password for authentication")
    parser.add_argument('-l', '--logfile', type=str, dest="logfile", default='STDOUT',
                        help="Path to the logfile [default: STDOUT]")
    parser.add_argument('--pidfile', type=str, dest="pidfile", default=None,
                        help=f"Path to the pidfile [default: /tmp/{__NAME__.lower()}.pid]")
    parser.add_argument('-d', '--daemon', action='store_true', dest="daemon", default=False,
                        help="Daemonize (run in the background). Daemon mode must specify logfile")
    parser.add_argument('-v', '--verbose', action='store_true', dest="verbose", default=False,
                        help="Log debug info")
    args = parser.parse_args()

    if (args.user and not args.password) or (not args.user and args.password):
        parser.error("Both --user and --password are required for authentication.")

    if args.daemon and args.logfile in ('-', 'STDOUT'):
        parser.error("Daemon mode requires a logfile path.")

    if not args.pidfile:
        args.pidfile = f"/tmp/{__NAME__.lower()}.pid"

    return args


def main():
    args = usage()
    if not (0 < args.port < 65536):
        print(f'Port[{args.port}] invalid', file=sys.stderr)
        sys.exit(1)

    logger = util.setup_logging(args.logfile, 20, args.verbose)

    if args.daemon:
        context = daemon.DaemonContext(
            working_directory='/tmp',
            umask=0o022,
            pidfile=pidfile.TimeoutPIDLockFile(args.pidfile),
            files_preserve=[handler.stream.fileno() for handler in logger.handlers],
            stdout=logger.handlers[0].stream,
            stderr=logger.handlers[0].stream,
        )
        try:
            with context:
                logger.info("Daemon process started.")
                proxy = Socks5Proxy(args.host, args.port, args.user, args.password)
                asyncio.run(proxy.start())
        except Exception as e:
            logger.critical(f"Daemon failed to start: {e}")
            sys.exit(1)
    else:
        try:
            logger.info("Starting proxy in foreground.")
            proxy = Socks5Proxy(args.host, args.port, args.user, args.password)
            asyncio.run(proxy.start())
        except KeyboardInterrupt:
            logger.info("Proxy stopped by user.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == '__main__':
    main()
