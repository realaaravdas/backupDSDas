#!/usr/bin/env python3
"""
Connection test utility for troubleshooting network issues
Tests UDP broadcast and listens for robot discovery packets
"""

import socket
import time
import sys

DISCOVERY_PORT = 12345

def test_udp_broadcast():
    """Test if UDP broadcast is working"""
    print("Testing UDP broadcast capability...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        test_message = "TEST_BROADCAST"
        sock.sendto(test_message.encode(), ('255.255.255.255', DISCOVERY_PORT))
        sock.close()
        
        print("✓ UDP broadcast is working")
        return True
    except Exception as e:
        print(f"✗ UDP broadcast failed: {e}")
        return False

def listen_for_robots(duration=10):
    """Listen for robot discovery packets"""
    print(f"\nListening for robot discovery packets for {duration} seconds...")
    print("Waiting for DISCOVER messages from robots...\n")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        sock.settimeout(1.0)
        
        robots_found = set()
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                
                if message.startswith("DISCOVER:"):
                    parts = message.split(":")
                    if len(parts) >= 3:
                        robot_id = parts[1]
                        robot_ip = parts[2]
                        
                        if robot_id not in robots_found:
                            print(f"✓ Found robot: {robot_id} at {robot_ip} (from {addr[0]})")
                            robots_found.add(robot_id)
                        else:
                            # Show subsequent pings with dots
                            print(".", end="", flush=True)
                else:
                    print(f"Received other message: {message[:50]}")
            
            except socket.timeout:
                continue
        
        sock.close()
        
        print(f"\n\nDiscovery complete!")
        if robots_found:
            print(f"✓ Found {len(robots_found)} robot(s): {', '.join(robots_found)}")
            return True
        else:
            print("✗ No robots found")
            return False
            
    except Exception as e:
        print(f"✗ Error listening for robots: {e}")
        return False

def check_port_availability():
    """Check if the discovery port is available"""
    print(f"Checking if port {DISCOVERY_PORT} is available...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        sock.close()
        print(f"✓ Port {DISCOVERY_PORT} is available")
        return True
    except Exception as e:
        print(f"✗ Port {DISCOVERY_PORT} is not available: {e}")
        return False

def show_network_info():
    """Show local network information"""
    print("\nNetwork Information:")
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  Hostname: {hostname}")
        print(f"  Local IP: {local_ip}")
    except Exception as e:
        print(f"  Could not determine network info: {e}")
    
    print(f"  Discovery Port: {DISCOVERY_PORT}")
    print(f"  Broadcast Address: 255.255.255.255")

def main():
    print("=" * 60)
    print("Minibot Driver Station - Connection Test Utility")
    print("=" * 60)
    print()
    
    show_network_info()
    print()
    
    # Test 1: Check port availability
    if not check_port_availability():
        print("\n⚠ Warning: Port may be in use by another application")
        print("   Try closing other driver station instances")
    
    print()
    
    # Test 2: Test UDP broadcast
    if not test_udp_broadcast():
        print("\n⚠ Warning: UDP broadcast may be blocked by firewall")
        sys.exit(1)
    
    # Test 3: Listen for robots
    if not listen_for_robots(duration=10):
        print("\n⚠ Troubleshooting tips:")
        print("   1. Make sure robots are powered on and running")
        print("   2. Verify robots are connected to the same WiFi network")
        print("   3. Check firewall settings (UDP port 12345)")
        print("   4. Ensure WiFi SSID is 'WATCHTOWER'")
        print("\n   To test without real robots, run: python3 demo_mode.py")
        sys.exit(1)
    
    print("\n✅ Connection test passed!")
    print("Your network is properly configured for the driver station.")
    print("\nYou can now run: python3 driver_station.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
