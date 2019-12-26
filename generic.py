#  This is a proxy that can replace data going thought it.
#  Copyright (C) 2019 Mm2PL
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import asyncio
import inspect
import ssl
import typing

import regex


class Arguments:
    port: int
    config_file: str
    base_host: str
    base_port: int
    enable_ssl: bool
    enable_ssl_server: bool


p = argparse.ArgumentParser()
p.add_argument('-p', '--port', help='Pick a port.', dest='port', type=int, default=8642)
p.add_argument('-c', '--config', help='Config file.', dest='config_file', type=str, default='config.json')
p.add_argument('-b', '--base', dest='base_host', type=str, required=True)
p.add_argument('-P', '--base-port', dest='base_port', type=int, required=True)
p.add_argument('--ssl', dest='enable_ssl', action='store_true')
p.add_argument('--ssl-in', dest='enable_ssl_server', action='store_true')

args: Arguments = p.parse_args(namespace=Arguments)

PORT = args.port
VERSION = '1.0'
regexs: typing.Dict[str, typing.List['Replacement']] = {
    'in': [],
    'out': []
}


class Replacement:
    def __init__(self, expr, repl):
        self.regex = regex.compile(expr)
        self.repl = repl

    def sub(self, data, connection_id):
        print(data)
        return self.regex.sub(self.repl, data)


async def _replace(data: bytes, connection_id, incoming=False) -> bytes:
    for r in regexs['in' if incoming else 'out']:
        if inspect.iscoroutinefunction(r.sub):
            data = await r.sub(data, connection_id)
        else:
            data = r.sub(data, connection_id)
    return data


async def _read(remote_reader: asyncio.StreamReader, local_writer: asyncio.StreamWriter, close_lock, connection_id):
    while 1:
        d = await remote_reader.read(4096)
        print(f'> {d}')
        if close_lock.locked():
            await local_writer.drain()
            local_writer.close()
            return
        if d == b'':
            print('close read')
            await close_lock.acquire()
            await local_writer.drain()
            local_writer.close()
            return
        local_writer.write(await _replace(d, connection_id, incoming=True))
        try:
            await local_writer.drain()
        except ConnectionResetError:
            await close_lock.acquire()
            local_writer.close()
            return


async def _write(remote_writer: asyncio.StreamWriter, local_reader: asyncio.StreamReader, close_lock, connection_id):
    while 1:
        d = await local_reader.read(4096)
        print(f'< {d}')
        if close_lock.locked():
            await remote_writer.drain()
            remote_writer.close()
            return
        if d == b'':
            print('close write')
            await close_lock.acquire()
            await remote_writer.drain()
            remote_writer.close()
            return
        remote_writer.write(await _replace(d, connection_id))
        try:
            await remote_writer.drain()
        except ConnectionResetError:
            await close_lock.acquire()
            remote_writer.close()
            return


counter = 0


async def _connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global counter
    connection_id = counter
    counter += 1
    print('Got connection.')
    other = await asyncio.open_connection(args.base_host, args.base_port, ssl=args.enable_ssl)
    other_r: asyncio.StreamReader = other[0]
    other_w: asyncio.StreamWriter = other[1]
    close_lock = asyncio.Lock()
    print('Opened remote connection')

    await asyncio.gather(
        _read(other_r, writer, close_lock, connection_id),
        _write(other_w, reader, close_lock, connection_id)
    )
    print('Connection closed.')


async def main():
    ctx = None
    if args.enable_ssl_server:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    srv = await asyncio.start_server(_connected, 'localhost', PORT, ssl=ctx)
    await srv.serve_forever()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
