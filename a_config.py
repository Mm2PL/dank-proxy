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

import asyncio
import sys
sys.argv += [
    '-b', 'localhost', '-P', '42070', '-p', '42071'
]
import generic

generic.regexs['in'].append(generic.Replacement(
    b'dupa.8', b'test'
))
generic.regexs['out'].append(generic.Replacement(
    b'test2', b'dupa.8'
))


class R(generic.Replacement):
    def __init__(self):
        self.regex = None
        super().__init__('', None)

    def sub(self, data: bytes, conn_id: int):
        return str(len(data)).encode('utf-8')


generic.regexs['in'].append(R())

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(generic.main())
