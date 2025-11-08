#!/usr/bin/env python3
"""
GUI Driver Station for Minibot Control System
Supports 2 robots with PS5 controller pairing via pygame
"""

import pygame
import socket
import struct
import threading
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Constants from minibot.h
DISCOVERY_PORT = 12345
COMMAND_PORT_BASE = 12346
WIFI_BROADCAST = "255.255.255.255"

# Display settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (220, 50, 50)
GREEN = (50, 220, 50)
BLUE = (50, 150, 220)
YELLOW = (220, 220, 50)
ORANGE = (255, 165, 0)

@dataclass
class RobotInfo:
    """Information about a discovered robot"""
    robot_id: str
    ip: str
    port: int
    last_seen: float
    connected: bool = False

@dataclass
class ControllerState:
    """State of a PS5 controller"""
    index: int
    name: str
    joystick: Optional[pygame.joystick.Joystick]
    left_x: int = 127
    left_y: int = 127
    right_x: int = 127
    right_y: int = 127
    cross: bool = False
    circle: bool = False
    square: bool = False
    triangle: bool = False
    connected: bool = False

class DriverStation:
    """Main driver station application"""
    
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Minibot Driver Station")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # Network setup
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', DISCOVERY_PORT))
        self.udp_socket.settimeout(0.1)
        
        # State
        self.robots: Dict[str, RobotInfo] = {}
        self.controllers: Dict[int, ControllerState] = {}
        self.robot_controller_pairs: Dict[str, int] = {}  # robot_id -> controller_index
        self.game_status = "standby"  # standby, teleop, autonomous
        self.emergency_stop = False
        self.running = True
        
        # Start network thread
        self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
        self.network_thread.start()
        
        # Discover controllers
        self._discover_controllers()
        
        # UI State
        self.selected_robot = None
        self.selected_controller = None
    
    def _discover_controllers(self):
        """Discover connected PS5 controllers"""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        num_joysticks = pygame.joystick.get_count()
        for i in range(num_joysticks):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.controllers[i] = ControllerState(
                index=i,
                name=joystick.get_name(),
                joystick=joystick,
                connected=True
            )
            print(f"Controller {i} connected: {joystick.get_name()}")
    
    def _network_loop(self):
        """Background thread for handling network communications"""
        while self.running:
            try:
                # Listen for discovery packets
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                
                # Parse discovery message: "DISCOVER:<robotId>:<IP>" or "DISCOVER:<robotId>:<IP>:<port>"
                if message.startswith("DISCOVER:"):
                    parts = message.split(":")
                    if len(parts) >= 3:
                        robot_id = parts[1]
                        robot_ip = parts[2]
                        # Check if discovery includes a port (for demo mode)
                        discovery_port = int(parts[3]) if len(parts) >= 4 else DISCOVERY_PORT

                        if robot_id not in self.robots:
                            # Assign a port for this robot
                            port = COMMAND_PORT_BASE + len(self.robots)
                            self.robots[robot_id] = RobotInfo(
                                robot_id=robot_id,
                                ip=robot_ip,
                                port=port,
                                last_seen=time.time(),
                                connected=False
                            )
                            print(f"Discovered robot: {robot_id} at {robot_ip}:{discovery_port}")
                        else:
                            # Update last seen time
                            self.robots[robot_id].last_seen = time.time()

                        # Send port assignment to the discovery port
                        robot_info = self.robots[robot_id]
                        response = f"PORT:{robot_id}:{robot_info.port}"
                        self.udp_socket.sendto(response.encode(), (robot_ip, discovery_port))
                        robot_info.connected = True
                        
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Network error: {e}")
            
            # Clean up stale robots (not seen in 10 seconds)
            current_time = time.time()
            stale_robots = [
                robot_id for robot_id, info in self.robots.items()
                if current_time - info.last_seen > 10
            ]
            for robot_id in stale_robots:
                print(f"Robot {robot_id} timed out")
                del self.robots[robot_id]
                if robot_id in self.robot_controller_pairs:
                    del self.robot_controller_pairs[robot_id]
            
            time.sleep(0.05)
    
    def _send_controller_data(self, robot_id: str, controller: ControllerState):
        """Send controller data to robot in binary format"""
        if robot_id not in self.robots:
            return
        
        robot_info = self.robots[robot_id]
        if not robot_info.connected:
            return
        
        # Only send controller data in teleop mode
        if self.game_status == "teleop" and not self.emergency_stop:
            # Create binary packet (24 bytes)
            # Bytes 0-15: Robot name (16 bytes, null-terminated)
            robot_name_bytes = robot_id.encode('utf-8')[:15].ljust(16, b'\x00')
            
            # Bytes 16-21: Axes data (6 bytes)
            axes = struct.pack('BBBBBB',
                controller.left_x,
                controller.left_y,
                controller.right_x,
                controller.right_y,
                127,  # Extra axis (unused)
                127   # Extra axis (unused)
            )
            
            # Bytes 22-23: Button data (2 bytes)
            button_byte_0 = (
                (1 if controller.cross else 0) |
                ((1 if controller.circle else 0) << 1) |
                ((1 if controller.square else 0) << 2) |
                ((1 if controller.triangle else 0) << 3)
            )
            buttons = struct.pack('BB', button_byte_0, 0)
            
            packet = robot_name_bytes + axes + buttons
            
            try:
                self.udp_socket.sendto(packet, (robot_info.ip, robot_info.port))
            except Exception as e:
                print(f"Error sending controller data: {e}")
    
    def _send_game_status(self, robot_id: str):
        """Send game status to robot"""
        if robot_id not in self.robots:
            return
        
        robot_info = self.robots[robot_id]
        message = f"{robot_id}:{self.game_status}"
        
        try:
            self.udp_socket.sendto(message.encode(), (robot_info.ip, robot_info.port))
        except Exception as e:
            print(f"Error sending game status: {e}")
    
    def _send_emergency_stop(self, enable: bool):
        """Send emergency stop to all robots"""
        message = "ESTOP" if enable else "ESTOP_OFF"
        
        for robot_info in self.robots.values():
            try:
                # Send to both discovery and command ports
                self.udp_socket.sendto(message.encode(), (robot_info.ip, DISCOVERY_PORT))
                self.udp_socket.sendto(message.encode(), (robot_info.ip, robot_info.port))
            except Exception as e:
                print(f"Error sending emergency stop: {e}")
    
    def _update_controllers(self):
        """Update controller states from pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                controller_index = event.joy
                if controller_index in self.controllers:
                    controller = self.controllers[controller_index]
                    pressed = (event.type == pygame.JOYBUTTONDOWN)
                    
                    # PS5 controller button mappings
                    if event.button == 0:  # Cross
                        controller.cross = pressed
                    elif event.button == 1:  # Circle
                        controller.circle = pressed
                    elif event.button == 2:  # Square
                        controller.square = pressed
                    elif event.button == 3:  # Triangle
                        controller.triangle = pressed
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Toggle emergency stop
                    self.emergency_stop = not self.emergency_stop
                    self._send_emergency_stop(self.emergency_stop)
                    print(f"Emergency stop: {self.emergency_stop}")
                elif event.key == pygame.K_1:
                    self.game_status = "standby"
                    for robot_id in self.robots:
                        self._send_game_status(robot_id)
                    print("Game status: standby")
                elif event.key == pygame.K_2:
                    self.game_status = "teleop"
                    for robot_id in self.robots:
                        self._send_game_status(robot_id)
                    print("Game status: teleop")
                elif event.key == pygame.K_3:
                    self.game_status = "autonomous"
                    for robot_id in self.robots:
                        self._send_game_status(robot_id)
                    print("Game status: autonomous")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event.pos)
        
        # Update joystick axes
        for controller in self.controllers.values():
            if controller.joystick and controller.connected:
                # Map joystick axes from -1..1 to 0..255
                left_x = int((controller.joystick.get_axis(0) + 1.0) * 127.5)
                left_y = int((controller.joystick.get_axis(1) + 1.0) * 127.5)
                right_x = int((controller.joystick.get_axis(2) + 1.0) * 127.5)
                right_y = int((controller.joystick.get_axis(3) + 1.0) * 127.5)
                
                controller.left_x = max(0, min(255, left_x))
                controller.left_y = max(0, min(255, left_y))
                controller.right_x = max(0, min(255, right_x))
                controller.right_y = max(0, min(255, right_y))
    
    def _refresh_robots(self):
        """Clear robot list and force rediscovery"""
        print("Refreshing robot list...")
        self.robots.clear()
        self.robot_controller_pairs.clear()
        self.selected_robot = None
        print("Robot list cleared - waiting for discovery...")

    def _handle_mouse_click(self, pos):
        """Handle mouse clicks for UI interactions"""
        x, y = pos

        # Check if clicking refresh button
        if 450 <= x <= 550 and 120 <= y <= 145:
            self._refresh_robots()
            return

        # Check if clicking on robot boxes (left side)
        robot_y_start = 150
        robot_height = 120
        for i, robot_id in enumerate(sorted(self.robots.keys())):
            robot_y = robot_y_start + i * (robot_height + 10)
            if 50 <= x <= 550 and robot_y <= y <= robot_y + robot_height:
                self.selected_robot = robot_id
                print(f"Selected robot: {robot_id}")
                return

        # Check if clicking on controller boxes (right side)
        controller_y_start = 150
        controller_height = 120
        for i in range(2):
            controller_y = controller_y_start + i * (controller_height + 10)
            if 650 <= x <= 1150 and controller_y <= y <= controller_y + controller_height:
                self.selected_controller = i if i in self.controllers else None
                print(f"Selected controller: {i}")
                return

        # Check if clicking pair button
        if 500 <= x <= 700 and 500 <= y <= 550:
            if self.selected_robot and self.selected_controller is not None:
                self.robot_controller_pairs[self.selected_robot] = self.selected_controller
                print(f"Paired {self.selected_robot} with controller {self.selected_controller}")
                self.selected_robot = None
                self.selected_controller = None
    
    def _draw_ui(self):
        """Draw the user interface"""
        self.screen.fill(BLACK)
        
        # Title
        title = self.title_font.render("Minibot Driver Station", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Game status indicator
        status_color = GREEN if self.game_status == "teleop" else YELLOW if self.game_status == "autonomous" else GRAY
        status_text = self.font.render(f"Status: {self.game_status.upper()}", True, status_color)
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 60))
        
        # Emergency stop indicator
        if self.emergency_stop:
            estop_text = self.title_font.render("EMERGENCY STOP", True, RED)
            pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH // 2 - 150, 90, 300, 40), 3)
            self.screen.blit(estop_text, (SCREEN_WIDTH // 2 - estop_text.get_width() // 2, 95))
        
        # Draw robots (left side)
        robot_label = self.font.render("Robots:", True, WHITE)
        self.screen.blit(robot_label, (50, 120))

        # Draw refresh button
        refresh_color = ORANGE
        pygame.draw.rect(self.screen, refresh_color, (450, 120, 100, 25))
        refresh_text = self.font.render("Refresh", True, BLACK)
        self.screen.blit(refresh_text, (465, 122))
        
        robot_y = 150
        for robot_id in sorted(self.robots.keys()):
            robot_info = self.robots[robot_id]
            
            # Draw robot box
            color = BLUE if self.selected_robot == robot_id else DARK_GRAY
            pygame.draw.rect(self.screen, color, (50, robot_y, 500, 120), 2)
            
            # Robot info
            name_text = self.font.render(f"Robot: {robot_id}", True, WHITE)
            ip_text = self.font.render(f"IP: {robot_info.ip}", True, GRAY)
            port_text = self.font.render(f"Port: {robot_info.port}", True, GRAY)
            status_text = self.font.render(
                f"Status: {'Connected' if robot_info.connected else 'Disconnected'}",
                True, GREEN if robot_info.connected else RED
            )
            
            # Check if paired with controller
            paired_controller = self.robot_controller_pairs.get(robot_id)
            if paired_controller is not None:
                pair_text = self.font.render(f"Paired with Controller {paired_controller}", True, YELLOW)
                self.screen.blit(pair_text, (60, robot_y + 90))
            
            self.screen.blit(name_text, (60, robot_y + 10))
            self.screen.blit(ip_text, (60, robot_y + 35))
            self.screen.blit(port_text, (60, robot_y + 55))
            self.screen.blit(status_text, (300, robot_y + 10))
            
            robot_y += 130
        
        # Draw controllers (right side)
        controller_label = self.font.render("Controllers:", True, WHITE)
        self.screen.blit(controller_label, (650, 120))
        
        controller_y = 150
        for i in range(2):
            # Draw controller box
            color = BLUE if self.selected_controller == i else DARK_GRAY
            pygame.draw.rect(self.screen, color, (650, controller_y, 500, 120), 2)
            
            if i in self.controllers:
                controller = self.controllers[i]
                name_text = self.font.render(f"Controller {i}: {controller.name[:30]}", True, WHITE)
                
                # Joystick values
                left_text = self.font.render(
                    f"Left: ({controller.left_x}, {controller.left_y})",
                    True, GRAY
                )
                right_text = self.font.render(
                    f"Right: ({controller.right_x}, {controller.right_y})",
                    True, GRAY
                )
                
                # Button states
                buttons_text = self.font.render(
                    f"X:{controller.cross} O:{controller.circle} □:{controller.square} △:{controller.triangle}",
                    True, GRAY
                )
                
                self.screen.blit(name_text, (660, controller_y + 10))
                self.screen.blit(left_text, (660, controller_y + 40))
                self.screen.blit(right_text, (660, controller_y + 65))
                self.screen.blit(buttons_text, (660, controller_y + 90))
            else:
                no_controller = self.font.render(f"Controller {i}: Not Connected", True, GRAY)
                self.screen.blit(no_controller, (660, controller_y + 50))
            
            controller_y += 130
        
        # Draw pairing button
        pair_button_color = GREEN if self.selected_robot and self.selected_controller is not None else DARK_GRAY
        pygame.draw.rect(self.screen, pair_button_color, (500, 500, 200, 50))
        pair_text = self.font.render("PAIR", True, WHITE)
        self.screen.blit(pair_text, (580, 512))
        
        # Draw instructions
        instructions = [
            "Controls:",
            "1: Standby | 2: Teleop | 3: Autonomous",
            "SPACE: Emergency Stop",
            "Click robot and controller, then PAIR button",
            "ESC: Quit"
        ]
        
        y_offset = 580
        for instruction in instructions:
            text = self.font.render(instruction, True, GRAY)
            self.screen.blit(text, (50, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
    def run(self):
        """Main application loop"""
        print("Driver Station started")
        print("Controls:")
        print("  1 - Set to Standby mode")
        print("  2 - Set to Teleop mode")
        print("  3 - Set to Autonomous mode")
        print("  SPACE - Toggle Emergency Stop")
        print("  ESC - Quit")
        
        while self.running:
            self._update_controllers()
            
            # Send controller data to paired robots
            for robot_id, controller_index in self.robot_controller_pairs.items():
                if controller_index in self.controllers and robot_id in self.robots:
                    controller = self.controllers[controller_index]
                    self._send_controller_data(robot_id, controller)
            
            self._draw_ui()
            self.clock.tick(FPS)
        
        # Cleanup
        print("Shutting down driver station...")
        self.emergency_stop = True
        self._send_emergency_stop(True)
        time.sleep(0.5)
        self.udp_socket.close()
        pygame.quit()

def main():
    try:
        station = DriverStation()
        station.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
