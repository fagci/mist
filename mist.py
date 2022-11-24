#!/usr/bin/env python3

from argparse import ArgumentParser
from ipaddress import IPv4Address
from random import randrange
from socket import setdefaulttimeout, socket
from threading import Thread

def eprint(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)

def import_file(full_name, path):
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location(full_name, path)

    if spec is None or spec.loader is None:
        raise ModuleNotFoundError('Module not found')

    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def make_handler(cb):
    from pathlib import Path
    from shutil import which

    file = Path(cb)
    is_cmd = which(cb)

    if not file.exists() and not is_cmd:
        return lambda ip, port, s: eval(cb, locals(), locals())

    suf = file.suffix

    if suf == '.py':
        m = import_file(file.name, file.absolute())
        def py(ip, port, s):
            m.handle(ip, port, s)
        return py

    if file.is_file() or is_cmd:
        def sh(ip, port, _):
            from subprocess import PIPE, Popen
            cmd = [cb if is_cmd else file.absolute(), ip, str(port)]
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            if out:
                print(out.decode())
            if err:
                eprint('[E] stderr:', err.decode())
        return sh

    raise NotImplementedError(f'Extension {suf} not supported')

def random_wan_ip():
    while True:
        ip_address = IPv4Address(randrange(0x01000000, 0xffffffff))
        if ip_address.is_global and not ip_address.is_multicast:
            return str(ip_address)

def check(addr, handler):
    with socket() as s:
        if s.connect_ex(addr) == 0:
            try:
                handler(*addr, s)
            except Exception as e:
                eprint('[E]', e)

def worker(port, cb):
    try:
        handler = make_handler(cb)
    except Exception as e:
        eprint('[E] cannot create handle:', e)
        exit(255)
    while True:
        ip = random_wan_ip()
        check((ip, port), handler)

def main(args):
    setdefaulttimeout(args.t)

    threads = []
    for _ in range(args.w):
        t = Thread(target=worker, daemon=True, args=(args.p, args.cb))
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

    try:
        main(parser.parse_args())
    except KeyboardInterrupt:
        exit(130)
