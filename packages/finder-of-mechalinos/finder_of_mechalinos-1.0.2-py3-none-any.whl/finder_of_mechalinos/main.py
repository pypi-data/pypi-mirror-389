#!/usr/bin/env python3
"""
Find Mechalino robots on local subnet by probing /id.
Saves results as ip,ID in /opt/mechalinos/ip_list.txt.

Requires: sudo apt install python3-scapy python3-netifaces
"""

import os, sys, ipaddress, time
from urllib.request import urlopen
from urllib.error import URLError
from scapy.all import ARP, Ether, srp, get_if_list
import netifaces

OUT_DIR = "/opt/mechalinos"
OUT_FILE = os.path.join(OUT_DIR, "ip_list.txt")
HTTP_TIMEOUT = 3
ARP_TIMEOUT = 4
ID_PATH = "/id"

def iface_to_subnet(iface):
    try:
        v4 = netifaces.ifaddresses(iface).get(netifaces.AF_INET)[0]
        return str(ipaddress.IPv4Network(f"{v4['addr']}/{v4['netmask']}", strict=False))
    except Exception:
        return None

def select_iface():
    ifaces = [i for i in get_if_list() if i != "lo"]
    if not ifaces: sys.exit("No usable network interfaces found.")
    if len(ifaces) == 1: return ifaces[0]
    for i, n in enumerate(ifaces): print(f"[{i}] {n}")
    return ifaces[int(input("Select interface number: ") or "0")]

def scan_arp(subnet, iface):
    ans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=subnet),
              iface=iface, timeout=ARP_TIMEOUT, verbose=0)[0]
    return sorted({r.psrc for _, r in ans}, key=lambda x: ipaddress.IPv4Address(x))

def get_id(ip):
    try:
        with urlopen(f"http://{ip}{ID_PATH}", timeout=HTTP_TIMEOUT) as r:
            if r.status == 200:
                return r.read().decode().strip()
    except URLError:
        pass
    return None

def main():
    iface = select_iface()
    subnet = iface_to_subnet(iface) or input("Subnet (e.g. 10.42.0.0/24): ")
    os.makedirs(OUT_DIR, exist_ok=True)
    try: os.remove(OUT_FILE)
    except FileNotFoundError: pass

    print(f"Scanning {subnet} on {iface} ...")
    for ip in scan_arp(subnet, iface):
        ident = get_id(ip)
        if ident:
            print(f"{ip}: {ident}")
            with open(OUT_FILE, "a") as f: f.write(f"{ip},{ident}\n")
        else:
            print(f"{ip}: no response")
        time.sleep(0.05)
    print(f"\nDone. Results saved to {OUT_FILE}")

def cli(): main()
if __name__ == "__main__": main()