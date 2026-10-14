import socket
import concurrent.futures
import subprocess
import re
import sys

PORT = 4747
TIMEOUT = 2.5

def get_arp_ips():
    out = subprocess.check_output(["arp", "-a"], text=True, errors="ignore")
    ips = re.findall(r"10\.0\.38\.\d+", out)
    ips = [ip for ip in ips if not ip.endswith(".255")]
    return sorted(set(ips), key=lambda x: int(x.split(".")[-1]))

def probe(ip):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((ip, PORT))
        try:
            s.sendall(b"GET / HTTP/1.0\r\nHost: " + ip.encode() + b"\r\n\r\n")
            banner = s.recv(256)
        except Exception:
            banner = b""
        s.close()
        return (ip, banner)
    except Exception:
        return None

def main():
    targets = get_arp_ips()
    full_scan = [f"10.0.38.{i}" for i in range(1, 255)]
    for ip in full_scan:
        if ip not in targets:
            targets.append(ip)
    print(f"Scanning {len(targets)} hosts on port {PORT}...")
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as pool:
        for r in pool.map(probe, targets):
            if r:
                ip, banner = r
                print(f"OPEN: {ip} banner={banner[:80]!r}")
                found.append((ip, banner))
    if not found:
        print("NO_HOST_FOUND")
        sys.exit(1)
    # Prefer one with DroidCam banner
    chosen = None
    for ip, banner in found:
        if b"DroidCam" in banner or b"droidcam" in banner.lower():
            chosen = ip
            break
    if not chosen:
        chosen = found[0][0]
    print(f"RESULT={chosen}")

if __name__ == "__main__":
    main()
