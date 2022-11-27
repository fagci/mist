#!/usr/bin/env python3

from argparse import ArgumentParser
from importlib.util import module_from_spec, spec_from_file_location
from random import getrandbits
from socket import inet_ntoa, setdefaulttimeout, socket
from struct import pack
from subprocess import Popen
from sys import stderr, stdout
from threading import BoundedSemaphore, Thread


class Handler:
    def __init__(self, cb=None, max_cb=8):
        if cb:
            self.cb_sem = BoundedSemaphore(max_cb)
            self.set_handler(cb)
            return

        self.handler = lambda ip, *_: print(ip)

    def set_handler(self, cmd):
        if cmd.endswith('.py'):
            self.handler = self.import_file('cb', cmd).handle
            return

        def sh(ip, port, _):
            with Popen([cmd, ip, str(port)], stdout=stdout, stderr=stderr) as p:
                p.communicate()

        self.handler = sh

    def handle(self, addr:tuple[str,int], s=None):
        with self.cb_sem:
            try:
                self.handler(*addr, s)
            except Exception as e:
                print('[E]', e, file=stderr)

    @staticmethod
    def import_file(full_name, path):
        spec = spec_from_file_location(full_name, path)

        if spec and spec.loader:
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

        raise ModuleNotFoundError('Module not found')


class Worker(Thread):
    def __init__(self, port, handler) -> None:
        super().__init__(daemon=True)
        self.handle = handler.handle
        self.addr_generator = self.random_wan_addr(port)

    def run(self):
        for addr in self.addr_generator:
            with socket() as s:
                if s.connect_ex(addr) == 0:
                    self.handle(addr, s)

    # TODO: random inside specified network
    @staticmethod
    def random_wan_addr(port):
        while True:
            int_ip = 0x01000000 + getrandbits(32) % 0xdeffffff

            if (0xA000000 <= int_ip < 0xb000000
                or 0x7F000000 <= int_ip < 0x80000000
                or 0x64400000 <= int_ip < 0x64800000
                or 0xAC100000 <= int_ip < 0xac200000
                or 0xC6120000 <= int_ip < 0xc6140000
                or 0xA9FE0000 <= int_ip < 0xa9ff0000
                or 0xC0A80000 <= int_ip < 0xc0a90000
                or 0xC0000000 <= int_ip < 0xc0000100
                or 0xC0000200 <= int_ip < 0xc0000300
                or 0xc0586300 <= int_ip < 0xc0586400
                or 0xC6336400 <= int_ip < 0xc6336500
                or 0xCB007100 <= int_ip < 0xcb007200
                or 0xe9fc0000 <= int_ip < 0xe9fc0100):
                continue
            yield (inet_ntoa(pack('>I', int_ip)), port)


def main(args):
    setdefaulttimeout(args.t)

    handler = Handler(args.cb, args.cbc)

    threads = []
    for _ in range(args.w):
        t = Worker(args.p, handler)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

if __name__ == '__main__':
    parser = ArgumentParser(description='Minimalistic netstalker')
    parser.add_argument('-t', type=float, default=0.75, help='timeout (s)')
    parser.add_argument('-w', type=int, default=1024, help='workers count')
    parser.add_argument('-p', type=int, default=80, help='port')
    parser.add_argument('-cb', help='callback handler')
    parser.add_argument('-cbc', type=int, default=8, help='max parallel callbacs')

    try:
        main(parser.parse_args())
    except KeyboardInterrupt:
        exit(130)
