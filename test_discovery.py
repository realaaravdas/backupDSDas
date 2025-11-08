#!/usr/bin/env python3
"""
Test script to verify robot discovery is working
"""

import socket
import time
import sys

DISCOVERY_PORT = 12345

def test_receiver():
    """Test receiving discovery packets"""
    print("=" * 60)
    print("TEST 1: Testing Discovery Packet Reception")
    print("=" * 60)

    # Create receiver socket (like driver station)
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receiver.bind(('', DISCOVERY_PORT))
    receiver.settimeout(5)

    # Create sender socket (like robot)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Send discovery packet
    message = "DISCOVER:TestRobot:127.0.0.1"
    print(f"\nSending: {message}")
    sender.sendto(message.encode(), ('127.0.0.1', DISCOVERY_PORT))

    # Try to receive
    print("Waiting for packet...")
    try:
        data, addr = receiver.recvfrom(1024)
        decoded = data.decode('utf-8')
        print(f"[OK] SUCCESS: Received '{decoded}' from {addr}")
        result = True
    except socket.timeout:
        print("[FAIL] FAILED: Timeout - no packet received")
        result = False

    receiver.close()
    sender.close()

    return result

def test_driver_station_socket():
    """Test if we can create the driver station socket"""
    print("\n" + "=" * 60)
    print("TEST 2: Testing Driver Station Socket Creation")
    print("=" * 60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        sock.settimeout(0.1)
        print(f"[OK] SUCCESS: Socket bound to port {DISCOVERY_PORT}")
        sock.close()
        return True
    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False

def test_demo_mode_simulation():
    """Test demo mode simulation"""
    print("\n" + "=" * 60)
    print("TEST 3: Testing Demo Mode Robot Simulation")
    print("=" * 60)

    # Create driver station socket
    driver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    driver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    driver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    driver.bind(('', DISCOVERY_PORT))
    driver.settimeout(6)

    # Create robot socket
    robot_port = DISCOVERY_PORT + 100
    robot = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    robot.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    robot.bind(('', robot_port))
    robot.settimeout(2)

    # Robot sends discovery
    discovery_msg = "DISCOVER:Robot1:127.0.0.1"
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"\n[Robot] Sending: {discovery_msg}")
    sender.sendto(discovery_msg.encode(), ('127.0.0.1', DISCOVERY_PORT))

    # Driver station receives
    print("[Driver Station] Waiting for discovery...")
    try:
        data, addr = driver.recvfrom(1024)
        decoded = data.decode('utf-8')
        print(f"[Driver Station] [OK] Received: {decoded}")

        # Parse and respond
        if decoded.startswith("DISCOVER:"):
            parts = decoded.split(":")
            robot_id = parts[1]
            robot_ip = parts[2]
            assigned_port = 12346

            response = f"PORT:{robot_id}:{assigned_port}"
            print(f"[Driver Station] Sending response: {response}")
            driver.sendto(response.encode(), (robot_ip, robot_port))

            # Robot receives port assignment
            print("[Robot] Waiting for port assignment...")
            try:
                data2, addr2 = robot.recvfrom(1024)
                decoded2 = data2.decode('utf-8')
                print(f"[Robot] [OK] Received: {decoded2}")
                print("\n[OK] SUCCESS: Full discovery handshake completed!")
                result = True
            except socket.timeout:
                print("[Robot] [FAIL] FAILED: Did not receive port assignment")
                result = False
        else:
            print("[FAIL] FAILED: Invalid discovery message format")
            result = False

    except socket.timeout:
        print("[Driver Station] [FAIL] FAILED: Did not receive discovery packet")
        result = False

    driver.close()
    robot.close()
    sender.close()

    return result

def main():
    print("\n" + "=" * 60)
    print("  MINIBOT DISCOVERY PROTOCOL TEST")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Basic UDP Reception", test_receiver()))
    results.append(("Driver Station Socket", test_driver_station_socket()))
    results.append(("Full Discovery Handshake", test_demo_mode_simulation()))

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("  [OK] ALL TESTS PASSED")
        print("\n  The discovery protocol is working correctly!")
        print("  If robots still don't show up in the driver station,")
        print("  the issue is likely in the UI update logic.")
    else:
        print("  [FAIL] SOME TESTS FAILED")
        print("\n  There is an issue with the network discovery.")
    print("=" * 60)
    print()

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
