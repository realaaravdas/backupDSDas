#!/usr/bin/env python3
"""
GUI Driver Station for Minibot Control System
Supports unlimited robots and controllers with scrollable lists
Resizable window with dynamic layout
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

        # Block joystick events to avoid pygame/Python 3.13 compatibility issue
        # We'll poll joystick state directly instead
        pygame.event.set_blocked(pygame.JOYAXISMOTION)
        pygame.event.set_blocked(pygame.JOYBALLMOTION)
        pygame.event.set_blocked(pygame.JOYHATMOTION)
        pygame.event.set_blocked(pygame.JOYBUTTONDOWN)
        pygame.event.set_blocked(pygame.JOYBUTTONUP)
        pygame.event.set_blocked(pygame.JOYDEVICEADDED)
        pygame.event.set_blocked(pygame.JOYDEVICEREMOVED)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Minibot Driver Station")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

        # Window dimensions (updated on resize)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        
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
        self.robot_scroll = 0
        self.controller_scroll = 0
    
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

                # Debug: Print ALL received packets
                print(f"[DEBUG] Received packet from {addr}: {message[:50]}")

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
        try:
            # Pump events first to avoid internal pygame errors
            pygame.event.pump()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

                elif event.type == pygame.MOUSEWHEEL:
                    # Scroll robot list if mouse over left side
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if mouse_x < self.width // 2:
                        self.robot_scroll -= event.y * 20
                        self.robot_scroll = max(0, self.robot_scroll)
                    else:
                        self.controller_scroll -= event.y * 20
                        self.controller_scroll = max(0, self.controller_scroll)

                # Note: Joystick button events disabled due to pygame/Python 3.13 compatibility issue
                # Button states are polled directly below instead
                # elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                #     controller_index = event.joy
                #     if controller_index in self.controllers:
                #         controller = self.controllers[controller_index]
                #         pressed = (event.type == pygame.JOYBUTTONDOWN)
                #
                #         # PS5 controller button mappings
                #         if event.button == 0:  # Cross
                #             controller.cross = pressed
                #         elif event.button == 1:  # Circle
                #             controller.circle = pressed
                #         elif event.button == 2:  # Square
                #             controller.square = pressed
                #         elif event.button == 3:  # Triangle
                #             controller.triangle = pressed

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
        except Exception as e:
            print(f"Error processing events: {e}")
            import traceback
            traceback.print_exc()

        # Update joystick axes and buttons (polled directly to avoid pygame/Python 3.13 event bug)
        for controller in self.controllers.values():
            if controller.joystick and controller.connected:
                try:
                    # Check number of axes available
                    num_axes = controller.joystick.get_numaxes()

                    # Map joystick axes from -1..1 to 0..255
                    # Use default value of 0.0 if axis doesn't exist
                    left_x_val = controller.joystick.get_axis(0) if num_axes > 0 else 0.0
                    left_y_val = controller.joystick.get_axis(1) if num_axes > 1 else 0.0
                    right_x_val = controller.joystick.get_axis(2) if num_axes > 2 else 0.0
                    right_y_val = controller.joystick.get_axis(3) if num_axes > 3 else 0.0

                    left_x = int((left_x_val + 1.0) * 127.5)
                    left_y = int((left_y_val + 1.0) * 127.5)
                    right_x = int((right_x_val + 1.0) * 127.5)
                    right_y = int((right_y_val + 1.0) * 127.5)

                    controller.left_x = max(0, min(255, left_x))
                    controller.left_y = max(0, min(255, left_y))
                    controller.right_x = max(0, min(255, right_x))
                    controller.right_y = max(0, min(255, right_y))

                    # Poll button states directly (avoids pygame event bug)
                    num_buttons = controller.joystick.get_numbuttons()
                    if num_buttons > 0:
                        controller.cross = controller.joystick.get_button(0)
                    if num_buttons > 1:
                        controller.circle = controller.joystick.get_button(1)
                    if num_buttons > 2:
                        controller.square = controller.joystick.get_button(2)
                    if num_buttons > 3:
                        controller.triangle = controller.joystick.get_button(3)

                except Exception as e:
                    print(f"Error reading controller {controller.index} state: {e}")
    
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

        # Dynamic layout calculations
        left_panel_width = (self.width - 40) // 2
        right_panel_x = self.width // 2 + 20

        # Check if clicking refresh button
        refresh_x = 150
        if refresh_x <= x <= refresh_x + 100 and 120 <= y <= 145:
            self._refresh_robots()
            return

        # Check if clicking on robot boxes (left side)
        robot_y_start = 150
        robot_height = 120
        for i, robot_id in enumerate(sorted(self.robots.keys())):
            robot_y = robot_y_start + i * (robot_height + 10) - self.robot_scroll
            if 20 <= x <= 20 + left_panel_width and robot_y <= y <= robot_y + robot_height:
                # Check if visible
                if robot_y >= 150 and robot_y < self.height - 150:
                    self.selected_robot = robot_id
                    print(f"Selected robot: {robot_id}")
                    return

        # Check if clicking on controller boxes (right side)
        controller_y_start = 150
        controller_height = 120
        for i, controller_id in enumerate(sorted(self.controllers.keys())):
            controller_y = controller_y_start + i * (controller_height + 10) - self.controller_scroll
            if right_panel_x <= x <= right_panel_x + left_panel_width and controller_y <= y <= controller_y + controller_height:
                # Check if visible
                if controller_y >= 150 and controller_y < self.height - 150:
                    self.selected_controller = controller_id
                    print(f"Selected controller: {controller_id}")
                    return

        # Check if clicking pair button (bottom center)
        pair_btn_x = self.width // 2 - 100
        pair_btn_y = self.height - 100
        if pair_btn_x <= x <= pair_btn_x + 200 and pair_btn_y <= y <= pair_btn_y + 50:
            if self.selected_robot and self.selected_controller is not None:
                self.robot_controller_pairs[self.selected_robot] = self.selected_controller
                print(f"Paired {self.selected_robot} with controller {self.selected_controller}")
                self.selected_robot = None
                self.selected_controller = None
    
    def _draw_ui(self):
        """Draw the user interface"""
        self.screen.fill(BLACK)

        # Dynamic layout calculations
        left_panel_width = (self.width - 40) // 2
        right_panel_x = self.width // 2 + 20

        # Title
        title = self.title_font.render("Minibot Driver Station", True, WHITE)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))

        # Game status indicator
        status_color = GREEN if self.game_status == "teleop" else YELLOW if self.game_status == "autonomous" else GRAY
        status_text = self.font.render(f"Status: {self.game_status.upper()}", True, status_color)
        self.screen.blit(status_text, (self.width // 2 - status_text.get_width() // 2, 60))

        # Emergency stop indicator
        if self.emergency_stop:
            estop_text = self.title_font.render("EMERGENCY STOP", True, RED)
            pygame.draw.rect(self.screen, RED, (self.width // 2 - 150, 90, 300, 40), 3)
            self.screen.blit(estop_text, (self.width // 2 - estop_text.get_width() // 2, 95))

        # Draw robots (left side with scrolling)
        robot_label = self.font.render("Robots:", True, WHITE)
        self.screen.blit(robot_label, (20, 120))

        # Draw refresh button
        refresh_x = 150
        pygame.draw.rect(self.screen, ORANGE, (refresh_x, 120, 100, 25))
        refresh_text = self.font.render("Refresh", True, BLACK)
        self.screen.blit(refresh_text, (refresh_x + 15, 122))

        # Create a clipping region for scrollable robot list
        robot_list_rect = pygame.Rect(20, 150, left_panel_width, self.height - 300)

        robot_y = 150
        for robot_id in sorted(self.robots.keys()):
            robot_info = self.robots[robot_id]
            actual_y = robot_y - self.robot_scroll

            # Only draw if visible
            if actual_y + 120 >= 150 and actual_y < self.height - 150:
                # Draw robot box
                color = BLUE if self.selected_robot == robot_id else DARK_GRAY
                pygame.draw.rect(self.screen, color, (20, actual_y, left_panel_width, 120), 2)

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
                    pair_text = self.font.render(f"Paired with Ctrl {paired_controller}", True, YELLOW)
                    self.screen.blit(pair_text, (30, actual_y + 90))

                self.screen.blit(name_text, (30, actual_y + 10))
                self.screen.blit(ip_text, (30, actual_y + 35))
                self.screen.blit(port_text, (30, actual_y + 55))
                self.screen.blit(status_text, (30 + left_panel_width - 200, actual_y + 10))

            robot_y += 130

        # Draw controllers (right side with scrolling)
        controller_label = self.font.render("Controllers:", True, WHITE)
        self.screen.blit(controller_label, (right_panel_x, 120))

        controller_y = 150
        for controller_id in sorted(self.controllers.keys()):
            actual_y = controller_y - self.controller_scroll

            # Only draw if visible
            if actual_y + 120 >= 150 and actual_y < self.height - 150:
                controller = self.controllers[controller_id]

                # Draw controller box
                color = BLUE if self.selected_controller == controller_id else DARK_GRAY
                pygame.draw.rect(self.screen, color, (right_panel_x, actual_y, left_panel_width, 120), 2)

                name_text = self.font.render(f"Controller {controller_id}: {controller.name[:20]}", True, WHITE)

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

                self.screen.blit(name_text, (right_panel_x + 10, actual_y + 10))
                self.screen.blit(left_text, (right_panel_x + 10, actual_y + 40))
                self.screen.blit(right_text, (right_panel_x + 10, actual_y + 65))
                self.screen.blit(buttons_text, (right_panel_x + 10, actual_y + 90))

            controller_y += 130

        # Draw pairing button at bottom
        pair_btn_x = self.width // 2 - 100
        pair_btn_y = self.height - 100
        pair_button_color = GREEN if self.selected_robot and self.selected_controller is not None else DARK_GRAY
        pygame.draw.rect(self.screen, pair_button_color, (pair_btn_x, pair_btn_y, 200, 50))
        pair_text = self.font.render("PAIR", True, WHITE)
        self.screen.blit(pair_text, (pair_btn_x + 80, pair_btn_y + 12))

        # Draw instructions at bottom
        instructions = [
            "Controls: 1=Standby | 2=Teleop | 3=Auto | SPACE=E-Stop | ESC=Quit | Scroll to see more"
        ]

        y_offset = self.height - 40
        for instruction in instructions:
            text = self.font.render(instruction, True, GRAY)
            self.screen.blit(text, (20, y_offset))
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
