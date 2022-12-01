#!/usr/bin/env python3

from argparse import ArgumentParser
from importlib.util import module_from_spec, spec_from_file_location
from random import getrandbits
from socket import SOL_SOCKET, SO_BINDTODEVICE, inet_ntoa, setdefaulttimeout, socket
from struct import pack
from subprocess import run
from sys import stderr, stdout
from threading import BoundedSemaphore, Lock, Thread
from time import sleep, time
from typing import DefaultDict


class Handler:
    def __init__(self, cb=None, max_cb=8):
        if cb:
            self.cb_sem = BoundedSemaphore(max_cb)
            self.set_handler(cb)
            return

        self.handler = lambda ip, *_: print(ip)

    def set_handler(self, cb):
        if cb.endswith('null'):
            self.handler = lambda *_: None
            return

        if cb.endswith(('.tst', '.log', '.csv', '.tsv')):
            file = open(cb, 'a')
            lock = Lock()
            sep = ':'
            if cb.endswith('.tsv'):
                sep = "\t"
            if cb.endswith('.csv'):
                sep = ','
            def write(ip, port, _):
                with lock:
                    file.write(f"{ip}{sep}{port}\n")
                    file.flush()
            self.handler = write
            return

        if cb.endswith('.py'):
            self.handler = self.import_file('cb', cb).handle
            return

        io = {'stdout': stdout, 'stderr': stderr}
        self.handler = lambda ip, port, _: run([cb, ip, str(port)], **io)

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
    def __init__(self, port, handler, iface=None, dbg_fn=None) -> None:
        super().__init__(daemon=True)
        self.handle = handler.handle
        self.addr_generator = self.random_wan_addr(port)
        self.iface = iface
        self.dbg_fn = dbg_fn if dbg_fn else lambda *_: None

    def run(self):
        iface = self.iface
        dbg_fn = self.dbg_fn
        for addr in self.addr_generator:
            with socket() as s:
                if iface:
                    s.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, iface.encode())

                err = None
                t = time()
                try:
                    s.connect(addr)
                except Exception as e:
                    err = e
                    pass
                finally:
                    dt = time() - t
                    dbg_fn(dt, err)

                if not err:
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

class Stats(Thread):
    __slots__ = ('errors', 'last_scan', 'last_pos', 'dt_min', 'dt_max')

    def __init__(self, interval):
        super().__init__(daemon=True)
        self.errors = DefaultDict(int)
        self.times = DefaultDict(int)
        self.inc_lock = Lock()
        self.interval = interval
        self.reset_counters()

    def reset_counters(self):
        self.last_scan = 0
        self.last_pos = 0
        self.dt_min = 3600
        self.dt_max = 0
        self.errors.clear()
        self.times.clear()

    def on_scanned(self, dt, err):
        with self.inc_lock:
            self.last_scan += 1
            if err:
                self.errors[str(err)] += 1
            else:
                self.times[round(dt, 1)] += 1
                self.last_pos += 1
                self.dt_min = min(self.dt_min, dt)
                self.dt_max = max(self.dt_max, dt)

    def update_counter(self):
        print()
        total = self.last_scan
        print(f'Total: {total}')

        if self.last_pos:
            print(f'Found: {self.last_pos} ({round(self.last_pos*100.0/total, 1)}%)')
            for t, c in sorted(self.times.items()):
                print(f'  {round(t*1000)} ms: {c} ({round(c*100.0/self.last_pos, 1)}%)')

        if self.errors:
            err_cnt = total - self.last_pos
            print(f'Errors: {err_cnt} ({round(err_cnt*100.0/total, 1)}%)')
            for n, c in sorted(self.errors.items()):
                print(f'  {n}: {c} ({round(c*100.0/total, 1)}%)')

        with self.inc_lock:
            self.reset_counters()

    def run(self):
        while True:
            sleep(self.interval)
            self.update_counter()

def main(args):
    setdefaulttimeout(args.t)

    handler = Handler(args.cb, args.cbc)

    dbg_fn = lambda *_: None
    if args.si:
        dbg = Stats(args.si)
        dbg_fn = dbg.on_scanned
        dbg.start()

    threads = []
    for _ in range(args.w):
        t = Worker(args.p, handler, args.i, dbg_fn)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

if __name__ == '__main__':
    parser = ArgumentParser(description='Minimalistic netstalker')
    parser.add_argument('-t', type=float, default=0.55, help='timeout (s)')
    parser.add_argument('-w', type=int, default=1200, help='workers count')
    parser.add_argument('-p', type=int, default=80, help='port')
    parser.add_argument('-cb', help='callback handler')
    parser.add_argument('-i', help='interface to use')
    parser.add_argument('-cbc', type=int, default=8, help='max parallel callbacs')
    parser.add_argument('-si', type=float, default=0, help='stats interval')

    try:
        main(parser.parse_args())
    except KeyboardInterrupt:
        exit(130)
