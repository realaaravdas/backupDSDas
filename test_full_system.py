#!/usr/bin/env python3
"""
Quick test to verify robot discovery works
"""

import socket
import threading
import time

DISCOVERY_PORT = 12345
COMMAND_PORT_BASE = 12346

def robot_simulator():
    """Simulate a robot"""
    robot_id = "TestRobot"
    robot_ip = "127.0.0.1"
    discovery_port = DISCOVERY_PORT + 1

    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', discovery_port))
    sock.settimeout(2)

    print(f"[Robot] Starting on port {discovery_port}")

    # Send discovery
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    for i in range(3):
        message = f"DISCOVER:{robot_id}:{robot_ip}:{discovery_port}"
        print(f"[Robot] Sending: {message}")
        sender.sendto(message.encode(), ('127.0.0.1', DISCOVERY_PORT))
        sender.sendto(message.encode(), ('255.255.255.255', DISCOVERY_PORT))

        # Wait for response
        try:
            data, addr = sock.recvfrom(1024)
            response = data.decode('utf-8')
            print(f"[Robot] Received: {response}")
            if response.startswith("PORT:"):
                print("[Robot] SUCCESS - Got port assignment!")
                break
        except socket.timeout:
            print(f"[Robot] No response (attempt {i+1}/3)")

        time.sleep(1)

    sock.close()
    sender.close()

def driver_station_simulator():
    """Simulate driver station"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', DISCOVERY_PORT))
    sock.settimeout(0.5)

    print("[Driver Station] Listening for robots...")

    robots = {}

    for i in range(6):  # Listen for 3 seconds
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8')

            if message.startswith("DISCOVER:"):
                parts = message.split(":")
                if len(parts) >= 3:
                    robot_id = parts[1]
                    robot_ip = parts[2]
                    discovery_port = int(parts[3]) if len(parts) >= 4 else DISCOVERY_PORT

                    print(f"[Driver Station] Discovered: {robot_id} at {robot_ip}:{discovery_port}")

                    if robot_id not in robots:
                        robots[robot_id] = COMMAND_PORT_BASE + len(robots)

                    assigned_port = robots[robot_id]
                    response = f"PORT:{robot_id}:{assigned_port}"
                    print(f"[Driver Station] Sending: {response} to {robot_ip}:{discovery_port}")
                    sock.sendto(response.encode(), (robot_ip, discovery_port))

        except socket.timeout:
            pass

    sock.close()

    if robots:
        print(f"\n[Driver Station] SUCCESS - Discovered {len(robots)} robot(s)")
    else:
        print("\n[Driver Station] FAILED - No robots discovered")

def main():
    print("=" * 60)
    print("  FULL SYSTEM TEST - Robot Discovery")
    print("=" * 60)
    print()

    # Start driver station in thread
    ds_thread = threading.Thread(target=driver_station_simulator, daemon=True)
    ds_thread.start()

    time.sleep(0.5)

    # Start robot
    robot_simulator()

    time.sleep(0.5)

    print()
    print("=" * 60)
    print("  Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
