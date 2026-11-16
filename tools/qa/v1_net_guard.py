"""R0036 V1 browser verification: process-side network isolation for the Python helpers.

install() patches socket connect/create_connection/getaddrinfo before any connection is opened. Only loopback
(127.0.0.0/8, ::1, "localhost") is allowed; a non-loopback attempt is refused before any socket connects or any
name is resolved, and is logged in REFUSED. Proxy variables are removed so urllib consults no proxy.
"""
import ipaddress
import os
import socket

REFUSED = []
_STATE = {"installed": False}
PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "NO_PROXY", "no_proxy")


class IsolationError(OSError):
    pass


def is_loopback(host):
    if host is None or host == "":
        return True
    h = str(host).strip("[]").lower()
    if h == "localhost":
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def _refuse(kind, target):
    REFUSED.append({"kind": kind, "target": str(target)})
    return IsolationError("R0036 network isolation: refused non-loopback %s to %s" % (kind, target))


def install():
    if _STATE["installed"]:
        return
    for k in PROXY_VARS:
        os.environ.pop(k, None)
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    getaddrinfo = socket.getaddrinfo
    create_connection = socket.create_connection

    def host_of(address):
        return address[0] if isinstance(address, tuple) else None

    def guarded_connect(self, address):
        if not is_loopback(host_of(address)):
            raise _refuse("socket", address)
        return connect(self, address)

    def guarded_connect_ex(self, address):
        if not is_loopback(host_of(address)):
            raise _refuse("socket", address)
        return connect_ex(self, address)

    def guarded_getaddrinfo(host, *args, **kwargs):
        if not is_loopback(host if not isinstance(host, bytes) else host.decode()):
            raise _refuse("dns", host)
        return getaddrinfo(host, *args, **kwargs)

    def guarded_create_connection(address, *args, **kwargs):
        if not is_loopback(host_of(address)):
            raise _refuse("connection", address)
        return create_connection(address, *args, **kwargs)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    socket.getaddrinfo = guarded_getaddrinfo
    socket.create_connection = guarded_create_connection
    _STATE["installed"] = True


def installed():
    return _STATE["installed"]
