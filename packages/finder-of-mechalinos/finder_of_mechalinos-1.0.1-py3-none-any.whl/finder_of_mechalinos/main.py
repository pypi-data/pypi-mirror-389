#!/usr/bin/env python3
"""
Find devices on subnet (via ARP), probe http://<ip>/cmd?cmd=S&param1=0
If response contains OK, save IP to /opt/mechalinos/ip_list.txt (one per line).
On start, the file is removed so the run is fresh.

Requires:
  sudo apt install python3-scapy python3-netifaces
Run:
  sudo python3 find_mechalinos.py
"""

import os
import sys
import ipaddress
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    from scapy.all import ARP, Ether, srp, get_if_list, get_if_addr
except Exception as e:
    print("Error: Scapy not available. Install with: sudo apt install python3-scapy")
    print("Exception:", e)
    sys.exit(1)

try:
    import netifaces
except Exception as e:
    print("Error: netifaces not available. Install with: sudo apt install python3-netifaces")
    print("Exception:", e)
    sys.exit(1)


OUT_DIR = "/opt/mechalinos"
OUT_FILE = os.path.join(OUT_DIR, "ip_list.txt")
PROBE_PATH = "/cmd?cmd=S&param1=0"
HTTP_TIMEOUT = 3  # seconds
ARP_TIMEOUT = 4   # seconds


def iface_to_subnet(iface):
    """Return CIDR subnet for iface (e.g. '10.42.0.0/24') or None"""
    try:
        addrs = netifaces.ifaddresses(iface)
        v4 = addrs.get(netifaces.AF_INET)
        if not v4:
            return None
        info = v4[0]
        ip = info.get("addr")
        netmask = info.get("netmask")
        if not ip or not netmask:
            return None
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network)
    except Exception:
        return None


def select_interface():
    ifaces = [i for i in get_if_list() if i != "lo"]
    if not ifaces:
        print("No network interfaces found (except loopback).")
        sys.exit(1)

    # If only one, pick it
    if len(ifaces) == 1:
        print(f"Using interface: {ifaces[0]}")
        return ifaces[0]

    # list and choose
    print("Available interfaces:")
    for idx, name in enumerate(ifaces):
        print(f"  {idx}: {name}")
    try:
        choice = input("Select interface number (Enter for default 0): ").strip()
        if choice == "":
            choice = "0"
        choice = int(choice)
        iface = ifaces[choice]
        print(f"Using interface: {iface}")
        return iface
    except (ValueError, IndexError):
        print("Invalid selection.")
        sys.exit(1)


def scan_arp(subnet, iface):
    """ARP-scan the subnet on iface. Return list of IP strings."""
    print(f"Scanning subnet {subnet} on interface {iface} (this may take a few seconds)...")
    arp = ARP(pdst=subnet)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    try:
        ans = srp(packet, iface=iface, timeout=ARP_TIMEOUT, verbose=0)[0]
    except PermissionError as e:
        print("Permission error: raw sockets need root privileges. Try running with sudo.")
        sys.exit(1)
    found = []
    for sent, received in ans:
        found.append(received.psrc)
    return sorted(set(found), key=lambda ip: ipaddress.IPv4Address(ip))


def probe_device(ip):
    url = f"http://{ip}{PROBE_PATH}"
    req = Request(url, headers={"User-Agent": "mechalino-scanner/1.0"})
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            body = resp.read().decode(errors="ignore").strip()
            # Accept either exact "OK!" or any text that starts with "OK" (case-insensitive)
            if resp.status == 200 and body.upper().startswith("OK"):
                return True, body
            # some devices might return 200 with custom body, check for OK anywhere
            if resp.status == 200 and "OK" in body.upper():
                return True, body
            return False, body
    except HTTPError as e:
        return False, f"HTTPError: {e.code}"
    except URLError as e:
        return False, f"URLError: {e.reason}"
    except Exception as e:
        return False, f"Error: {e}"


def ensure_outdir():
    if not os.path.exists(OUT_DIR):
        try:
            os.makedirs(OUT_DIR, exist_ok=True)
            # set reasonable perms
            os.chmod(OUT_DIR, 0o755)
        except PermissionError:
            print(f"Permission denied creating {OUT_DIR}. Run with sudo or create the directory yourself.")
            sys.exit(1)
    # remove old file if exists
    if os.path.exists(OUT_FILE):
        try:
            os.remove(OUT_FILE)
        except PermissionError:
            print(f"Permission denied removing {OUT_FILE}. Run with sudo or remove it manually.")
            sys.exit(1)


def save_ip(ip):
    try:
        with open(OUT_FILE, "a") as f:
            f.write(ip + "\n")
    except PermissionError:
        print(f"Permission denied writing to {OUT_FILE}. Run with sudo or adjust permissions.")
        sys.exit(1)


def main():
    iface = select_interface()
    subnet = iface_to_subnet(iface)
    if not subnet:
        subnet = input("Could not detect subnet automatically. Enter target subnet (e.g. 10.42.0.0/24): ").strip()
        if not subnet:
            print("No subnet provided. Exiting.")
            sys.exit(1)

    ensure_outdir()
    ips = scan_arp(subnet, iface)
    if not ips:
        print("No hosts found via ARP.")
        sys.exit(0)

    print(f"Found {len(ips)} hosts. Probing HTTP endpoint on each...")
    hits = []
    for ip in ips:
        print(f"  Probing http://{ip}{PROBE_PATH} ... ", end="", flush=True)
        ok, info = probe_device(ip)
        if ok:
            print("OK -> saving")
            save_ip(ip)
            hits.append((ip, info))
        else:
            print(f"no ({info})")
        # slight delay to avoid hammering
        time.sleep(0.05)

    print("\nScan complete.")
    if hits:
        print(f"Saved {len(hits)} IP(s) to {OUT_FILE}:")
        for ip, body in hits:
            print(f"  {ip} (response: {body})")
    else:
        print("No devices responded with OK.")

def cli():
    main()

if __name__ == "__main__":
    main()