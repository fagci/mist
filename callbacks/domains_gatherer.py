#!/usr/bin/env python3

def handle(ip, port, _):
    domains = get_domains_from_cert(ip, port, 2)
    if domains:
        res = ', '.join(domains)
        print(f'{ip}: {res}')

def get_domains_from_cert(hostname, port: int = 443, timeout: float = 10) -> list:
    import ssl
    import socket

    context = ssl.create_default_context()
    context.check_hostname = False

    try:
        with context.wrap_socket(socket.socket(), server_hostname=hostname) as c:
            c.settimeout(timeout)
            c.connect((hostname, port))

            ssl_info = c.getpeercert()

            return [v for _, v in ssl_info.get('subjectAltName', [])]
    except:
        pass

    return []
