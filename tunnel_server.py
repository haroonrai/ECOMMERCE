"""
Persistent Auto-Reconnecting Public Tunnel Manager
"""
import subprocess
import time
import re
import sys

def start_tunnel():
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=5",
        "-R", "80:127.0.0.1:5000",
        "serveo.net"
    ]
    
    while True:
        print("[Tunnel] Connecting to public tunnel...")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in iter(proc.stdout.readline, ''):
                print(line, end='', flush=True)
                if "Forwarding HTTP traffic from" in line:
                    match = re.search(r'https://[^\s]+', line)
                    if match:
                        url = match.group(0)
                        print(f"\n==========================================")
                        print(f"ACTIVE PUBLIC MOBILE URL: {url}")
                        print(f"==========================================\n", flush=True)

            proc.wait()
            print("[Tunnel] Disconnected. Reconnecting in 3 seconds...", flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"[Tunnel Error] {e}", flush=True)
            time.sleep(5)

if __name__ == '__main__':
    start_tunnel()
