"""
High-Speed Cloudflare Public Tunnel for AURA Healthcare E-Commerce Store
"""
import os
import sys
import subprocess
import re
import time

def start_tunnel():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cloudflared_bin = os.path.join(base_dir, 'cloudflared.exe')
    
    if not os.path.exists(cloudflared_bin):
        cloudflared_bin = 'cloudflared'

    port = 5000
    cmd = [cloudflared_bin, 'tunnel', '--url', f'http://127.0.0.1:{port}']
    
    print("\n" + "=" * 65)
    print("  🚀 INITIALIZING CLOUDFLARE SECURE PUBLIC TUNNEL...")
    print(f"  Forwarding local port {port} to the world...")
    print("=" * 65 + "\n")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        tunnel_url = None
        for line in iter(proc.stdout.readline, ''):
            if not tunnel_url:
                # Search for trycloudflare URL
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    tunnel_url = match.group(0)
                    print("\n" + "🌟" * 32)
                    print("🎉 YOUR STORE IS NOW LIVE ON THE GLOBAL INTERNET!")
                    print(f"🔗 Public Link:     {tunnel_url}")
                    print(f"🔐 Admin Portal:    {tunnel_url}/auth")
                    print("📱 Share this link with anyone on mobile or PC!")
                    print("🌟" * 32 + "\n", flush=True)

            # Print cloudflared heartbeat status
            if "Registered tunnel connection" in line or "Connection" in line:
                print(f"[Cloudflare] {line.strip()}", flush=True)

        proc.wait()
    except KeyboardInterrupt:
        print("\n[Tunnel] Closed by user.")
    except Exception as e:
        print(f"\n[Tunnel Error] {e}")

if __name__ == '__main__':
    start_tunnel()
