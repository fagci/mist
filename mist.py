#!/usr/bin/env python3

from argparse import ArgumentParser
from ipaddress import IPv4Address
from random import randrange
from socket import setdefaulttimeout, socket
from subprocess import PIPE, Popen
from sys import stderr
from threading import BoundedSemaphore, Thread


class Handler:
    def __init__(self, cb=None, max_cb=8):
        if not cb:
            self.handler = lambda ip, *_: print(ip)
            return

        self.cb_sem = BoundedSemaphore(max_cb)

        if cb.endswith('.py'):
            self.set_py_handler(cb)
            return

        self.set_cmd_handler(cb)

    def set_cmd_handler(self, cmd):
        def sh(ip, port, _):
            p = Popen([cmd, ip, str(port)], stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            if out:
                print(out.decode())
            if err:
                print('[E] stderr:', file=stderr)
                print(err.decode(), file=stderr)
        self.handler = sh

    def set_py_handler(self, file):
        self.handler = self.import_file('cb', file).handle

    def handle(self, ip, port, s):
        with self.cb_sem:
            try:
                self.handler(ip, port, s)
            except Exception as e:
                print('[E]', e, file=stderr)

    @classmethod
    def import_file(cls, full_name, path):
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location(full_name, path)

        if spec is None or spec.loader is None:
            raise ModuleNotFoundError('Module not found')

        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


class Worker(Thread):
    @classmethod
    def random_wan_ip(cls):
        while True:
            ip_address = IPv4Address(randrange(0x01000000, 0xffffffff))
            if ip_address.is_global and not ip_address.is_multicast:
                return str(ip_address)

    def __init__(self, port, handler) -> None:
        super().__init__(daemon=True)
        self.port = port
        self.handler = handler

    def run(self):
        while True:
            ip = self.random_wan_ip()
            with socket() as s:
                if s.connect_ex((ip, self.port)) == 0:
                    self.handler.handle(ip, self.port, s)


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
