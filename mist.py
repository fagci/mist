#!/usr/bin/env python3

from argparse import ArgumentParser
from ipaddress import IPv4Address
from random import randrange
from socket import setdefaulttimeout, socket
from threading import Thread

def random_wan_ip():
    while True:
        ip_address = IPv4Address(randrange(0x01000000, 0xffffffff))
        if ip_address.is_global and not ip_address.is_multicast:
            return str(ip_address)

def check(addr):
    with socket() as s:
        return s.connect_ex(addr) == 0

def worker(port):
    while True:
        ip = random_wan_ip()
        if check((ip, port)):
            print(ip)

def main(args):
    setdefaulttimeout(args.t)

    threads = []
    for _ in range(args.w):
        t = Thread(target=worker, daemon=True, args=(args.p,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

if __name__ == '__main__':
    parser = ArgumentParser(description='Minimalistic netstalker')
    parser.add_argument('-t', type=float, default=0.75, help='timeout (s)')
    parser.add_argument('-w', type=int, default=1024, help='workers count')
    parser.add_argument('-p', type=int, default=80, help='port')

    try:
        main(parser.parse_args())
    except KeyboardInterrupt:
        exit(130)
