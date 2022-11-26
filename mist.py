#!/usr/bin/env python3

from argparse import ArgumentParser
from ipaddress import IPv4Address
from random import randrange
from socket import setdefaulttimeout, socket
from threading import Thread, BoundedSemaphore
from sys import stderr


class Handler:
    def __init__(self, cb=None, max_cb=8):
        if cb is None:
            self.handler = lambda ip, *_: print(ip)
            return
        self.cb_sem = BoundedSemaphore(max_cb)

        from pathlib import Path
        from shutil import which

        file = Path(cb)
        is_cmd = which(cb)

        if not file.exists() and not is_cmd:
            self.handler = lambda ip, port, s: eval(cb, locals(), locals())
            return

        suf = file.suffix
        path = str(file.absolute())

        if suf == '.py':
            m = self.import_file(file.name, path)
            def py(ip, port, s):
                m.handle(ip, port, s)
            self.handler = py
            return

        if file.is_file() or is_cmd:
            def sh(ip, port, _):
                from subprocess import PIPE, Popen
                cmd = [cb if is_cmd else path, ip, str(port)]
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                if out:
                    print(out.decode())
                if err:
                    print('[E] stderr:', err.decode(), file=stderr)
                p.terminate()
            self.handler = sh
            return

        raise NotImplementedError(f'not supported')

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
