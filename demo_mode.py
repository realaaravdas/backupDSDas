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
        
        # Create UDP socket - for demo mode, we can't use SO_REUSEPORT effectively
        # because all robots share localhost and messages get distributed randomly.
        # Instead, bind to any available port (0) and the driver station will respond
        # to the actual sender address.
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', 0))  # Bind to any available port
        self.udp_socket.settimeout(0.5)
        self.listen_port = self.udp_socket.getsockname()[1]
        
        print(f"Simulated robot '{robot_id}' created, listening on port {self.listen_port}")
    
    def send_discovery(self):
        """Send discovery broadcast"""
        message = f"DISCOVER:{self.robot_id}:{self.ip}"
        # Use the bound socket to send, just like ESP32 does
        # This ensures we send FROM the port we're listening on
        self.udp_socket.sendto(message.encode(), ('127.0.0.1', DISCOVERY_PORT))
        print(f"[{self.robot_id}] Sent discovery: {message}")
    
    def listen_for_commands(self):
        """Listen for port assignment and commands"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                
                # Check for port assignment (when not yet connected)
                if message.startswith("PORT:") and self.assigned_port is None:
                    parts = message.split(":")
                    if len(parts) >= 3:
                        target_robot = parts[1]
                        if target_robot == self.robot_id:
                            new_port = int(parts[2])
                            print(f"[{self.robot_id}] Received port assignment: {new_port}")
                        else:
                            # Message for another robot (due to SO_REUSEPORT distribution)
                            print(f"[{self.robot_id}] Ignoring PORT message for {target_robot}")
                            continue
                        
                        # Close old socket and bind to new assigned port
                        print(f"[{self.robot_id}] Closing old socket and switching to port {new_port}")
                        self.udp_socket.close()
                        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        self.udp_socket.bind(('', new_port))
                        self.udp_socket.settimeout(0.5)
                        self.assigned_port = new_port
                        print(f"[{self.robot_id}] Successfully switched to assigned port: {self.assigned_port}")
                
                # Check for game status
                elif message.startswith(self.robot_id) and ':' in message:
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
        self.udp_socket.close()

def main():
    print("Starting simulated robots for demo mode...")
    print("Start the driver_station.py in another terminal to connect")
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
