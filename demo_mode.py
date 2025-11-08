#!/usr/bin/env python3
"""
Demo/Simulation mode for the driver station
Simulates robots and controller input for testing without hardware
"""

import socket
import time
import threading
import random

DISCOVERY_PORT = 12345

class SimulatedRobot:
    """Simulates a robot for testing"""

    def __init__(self, robot_id, ip="127.0.0.1"):
        self.robot_id = robot_id
        self.ip = ip
        self.running = True
        self.assigned_port = None

        # Create discovery socket (listens on DISCOVERY_PORT like real ESP32)
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Bind to unique port for this robot so multiple can run
        self.discovery_port = DISCOVERY_PORT + 1 + hash(robot_id) % 10
        self.discovery_socket.bind(('', self.discovery_port))
        self.discovery_socket.settimeout(0.5)

        # Command socket (created after port assignment)
        self.command_socket = None

        print(f"Simulated robot '{robot_id}' created on port {self.discovery_port}")
    
    def send_discovery(self):
        """Send discovery broadcast"""
        message = f"DISCOVER:{self.robot_id}:{self.ip}:{self.discovery_port}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Send to broadcast and localhost
        sock.sendto(message.encode(), ('255.255.255.255', DISCOVERY_PORT))
        sock.sendto(message.encode(), ('127.0.0.1', DISCOVERY_PORT))
        sock.close()
        print(f"[{self.robot_id}] Sent discovery: {message}")
    
    def listen_for_commands(self):
        """Listen for port assignment and commands"""
        while self.running:
            try:
                # Listen on discovery socket if not assigned yet
                if self.assigned_port is None:
                    data, addr = self.discovery_socket.recvfrom(1024)
                else:
                    data, addr = self.command_socket.recvfrom(1024)

                message = data.decode('utf-8', errors='ignore')

                # Check for port assignment
                if message.startswith("PORT:"):
                    parts = message.split(":")
                    if len(parts) >= 3 and parts[1] == self.robot_id:
                        self.assigned_port = int(parts[2])
                        print(f"[{self.robot_id}] Assigned port: {self.assigned_port}")

                        # Create command socket
                        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        self.command_socket.bind(('', self.assigned_port))
                        self.command_socket.settimeout(0.5)
                
                # Check for game status
                elif message.startswith(self.robot_id):
                    sep_index = message.index(":")
                    status = message[sep_index + 1:]
                    print(f"[{self.robot_id}] Game status: {status}")
                
                # Check for emergency stop
                elif message == "ESTOP":
                    print(f"[{self.robot_id}] EMERGENCY STOP!")
                
                elif message == "ESTOP_OFF":
                    print(f"[{self.robot_id}] Emergency stop released")
                
                # Controller data (binary)
                elif len(data) == 24:
                    robot_name = data[:16].rstrip(b'\x00').decode('utf-8', errors='ignore')
                    if robot_name == self.robot_id:
                        axes = data[16:22]
                        buttons = data[22:24]
                        print(f"[{self.robot_id}] Controller data: axes={list(axes)}, buttons={list(buttons)}")
            
            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    print(f"[{self.robot_id}] Error: {e}")
    
    def run(self):
        """Main robot loop"""
        listen_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        listen_thread.start()
        
        while self.running:
            if self.assigned_port is None:
                self.send_discovery()
            time.sleep(2)
    
    def stop(self):
        """Stop the simulated robot"""
        self.running = False
        self.discovery_socket.close()
        if self.command_socket:
            self.command_socket.close()

def main():
    print("=" * 60)
    print("  DEMO MODE - Simulated Robots")
    print("=" * 60)
    print()
    print("IMPORTANT: Demo mode has a known limitation on Windows!")
    print("Windows blocks UDP localhost communication on the same port.")
    print()
    print("What this means:")
    print("  - Simulated robots WILL send discovery packets")
    print("  - Driver station WILL receive them")
    print("  - But robots WON'T receive PORT responses on Windows")
    print()
    print("THIS IS NORMAL! Real ESP32 robots work perfectly because")
    print("they're on different machines (different IPs).")
    print()
    print("To test the GUI: Just run 'python driver_station.py'")
    print("To test fully: Use real ESP32 hardware or Linux/Mac")
    print()
    print("See ROBOT_DISCOVERY_FIX.md for full details.")
    print("=" * 60)
    print()
    print("Starting simulated robots...")
    print("Press Ctrl+C to stop\n")
    
    # Create two simulated robots
    robot1 = SimulatedRobot("Robot1")
    robot2 = SimulatedRobot("Robot2")
    
    # Start robots in threads
    thread1 = threading.Thread(target=robot1.run, daemon=True)
    thread2 = threading.Thread(target=robot2.run, daemon=True)
    
    thread1.start()
    thread2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping simulated robots...")
        robot1.stop()
        robot2.stop()
        time.sleep(1)

if __name__ == "__main__":
    main()
