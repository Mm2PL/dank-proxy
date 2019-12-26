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

    def sub(self, data: bytes):
        return str(len(data)).encode('utf-8')


generic.regexs['in'].append(R())

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(generic.main())
