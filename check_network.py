#!/usr/bin/env python3
"""
Network diagnostic tool to help debug robot discovery
"""

import socket
import sys

def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a socket and connect to a remote address (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unable to determine"

def check_firewall():
    """Check if we can bind to port 12345"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 12345))
        sock.close()
        return True, "Can bind to port 12345"
    except Exception as e:
        return False, f"Cannot bind to port 12345: {e}"

def listen_for_broadcasts():
    """Listen for any UDP broadcasts on port 12345"""
    print("\nListening for UDP packets on port 12345...")
    print("Press Ctrl+C to stop")
    print("-" * 60)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', 12345))
    sock.settimeout(1.0)

    count = 0
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                count += 1
                print(f"\n[Packet {count}]")
                print(f"  From: {addr[0]}:{addr[1]}")
                print(f"  Message: {message}")

                if message.startswith("DISCOVER:"):
                    parts = message.split(":")
                    if len(parts) >= 3:
                        print(f"  >>> ROBOT FOUND: {parts[1]} at {parts[2]}")

            except socket.timeout:
                print(".", end="", flush=True)
    except KeyboardInterrupt:
        print("\n\nStopped listening.")
        print(f"Total packets received: {count}")

    sock.close()

def main():
    print("=" * 60)
    print("  NETWORK DIAGNOSTIC TOOL")
    print("=" * 60)
    print()

    # Check local IP
    local_ip = get_local_ip()
    print(f"Your PC's IP address: {local_ip}")
    print()

    # Check if we can bind to the port
    can_bind, msg = check_firewall()
    if can_bind:
        print(f"[OK] {msg}")
    else:
        print(f"[ERROR] {msg}")
        print("\nThis might be a firewall issue!")
        print("Try:")
        print("  1. Disable Windows Firewall temporarily")
        print("  2. Add Python to firewall exceptions")
        return 1

    print()
    print("What your ESP32 IP should start with:")
    ip_parts = local_ip.split(".")
    if len(ip_parts) >= 3:
        print(f"  {ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.XXX")
        print()
        print("If your ESP32 has a different IP prefix, they're on")
        print("different networks and can't communicate!")

    print()
    print("=" * 60)

    # Listen for broadcasts
    listen_for_broadcasts()

if __name__ == "__main__":
    sys.exit(main())
