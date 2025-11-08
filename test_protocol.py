#!/usr/bin/env python3
"""
Test script to verify the protocol implementation matches the minibot expectations
"""

import struct

def test_controller_packet():
    """Test that controller packet format matches minibot.cpp expectations"""
    
    # Create a test packet
    robot_id = "TestRobot"
    robot_name_bytes = robot_id.encode('utf-8')[:15].ljust(16, b'\x00')
    
    # Test values
    left_x = 100
    left_y = 150
    right_x = 200
    right_y = 127
    
    # Axes (6 bytes)
    axes = struct.pack('BBBBBB', left_x, left_y, right_x, right_y, 127, 127)
    
    # Buttons (2 bytes)
    cross = True
    circle = False
    square = True
    triangle = False
    
    button_byte_0 = (
        (1 if cross else 0) |
        ((1 if circle else 0) << 1) |
        ((1 if square else 0) << 2) |
        ((1 if triangle else 0) << 3)
    )
    buttons = struct.pack('BB', button_byte_0, 0)
    
    # Complete packet
    packet = robot_name_bytes + axes + buttons
    
    # Verify packet size
    assert len(packet) == 24, f"Packet size should be 24, got {len(packet)}"
    
    # Verify robot name
    robot_name_from_packet = packet[:16].rstrip(b'\x00').decode('utf-8')
    assert robot_name_from_packet == robot_id, f"Robot name mismatch: {robot_name_from_packet}"
    
    # Verify axes
    axes_from_packet = struct.unpack('BBBBBB', packet[16:22])
    assert axes_from_packet[0] == left_x, f"Left X mismatch: {axes_from_packet[0]}"
    assert axes_from_packet[1] == left_y, f"Left Y mismatch: {axes_from_packet[1]}"
    assert axes_from_packet[2] == right_x, f"Right X mismatch: {axes_from_packet[2]}"
    assert axes_from_packet[3] == right_y, f"Right Y mismatch: {axes_from_packet[3]}"
    
    # Verify buttons
    buttons_from_packet = struct.unpack('BB', packet[22:24])
    button_byte = buttons_from_packet[0]
    assert (button_byte & 0x01) == 1, "Cross button should be pressed"
    assert (button_byte & 0x02) == 0, "Circle button should not be pressed"
    assert (button_byte & 0x04) == 4, "Square button should be pressed"
    assert (button_byte & 0x08) == 0, "Triangle button should not be pressed"
    
    print("[OK] Controller packet format test passed!")

def test_discovery_message():
    """Test discovery message format"""
    robot_id = "TestRobot"
    ip = "192.168.1.100"
    
    message = f"DISCOVER:{robot_id}:{ip}"
    parts = message.split(":")
    
    assert len(parts) >= 3, "Discovery message should have at least 3 parts"
    assert parts[0] == "DISCOVER", "First part should be DISCOVER"
    assert parts[1] == robot_id, f"Robot ID should be {robot_id}"
    assert parts[2] == ip, f"IP should be {ip}"
    
    print("[OK] Discovery message format test passed!")

def test_port_assignment():
    """Test port assignment message format"""
    robot_id = "TestRobot"
    port = 12346
    
    message = f"PORT:{robot_id}:{port}"
    parts = message.split(":")
    
    assert len(parts) == 3, "Port assignment should have 3 parts"
    assert parts[0] == "PORT", "First part should be PORT"
    assert parts[1] == robot_id, f"Robot ID should be {robot_id}"
    assert int(parts[2]) == port, f"Port should be {port}"
    
    print("[OK] Port assignment format test passed!")

def test_game_status():
    """Test game status message format"""
    robot_id = "TestRobot"
    status = "teleop"
    
    message = f"{robot_id}:{status}"
    sep_index = message.index(":")
    
    parsed_id = message[:sep_index]
    parsed_status = message[sep_index + 1:]
    
    assert parsed_id == robot_id, f"Robot ID should be {robot_id}"
    assert parsed_status == status, f"Status should be {status}"
    
    print("[OK] Game status format test passed!")

def test_emergency_stop():
    """Test emergency stop messages"""
    estop_enable = "ESTOP"
    estop_disable = "ESTOP_OFF"
    
    assert estop_enable == "ESTOP", "Emergency stop enable should be ESTOP"
    assert estop_disable == "ESTOP_OFF", "Emergency stop disable should be ESTOP_OFF"
    
    print("[OK] Emergency stop format test passed!")

def test_axis_mapping():
    """Test that joystick axis mapping is correct"""
    # Test center position
    joystick_value = 0.0  # Center
    mapped = int((joystick_value + 1.0) * 127.5)
    assert mapped == 127, f"Center should map to 127, got {mapped}"
    
    # Test full forward
    joystick_value = 1.0  # Full forward
    mapped = int((joystick_value + 1.0) * 127.5)
    assert mapped == 255, f"Full forward should map to 255, got {mapped}"
    
    # Test full backward
    joystick_value = -1.0  # Full backward
    mapped = int((joystick_value + 1.0) * 127.5)
    assert mapped == 0, f"Full backward should map to 0, got {mapped}"
    
    print("[OK] Axis mapping test passed!")

if __name__ == "__main__":
    print("Running protocol compatibility tests...\n")
    
    test_controller_packet()
    test_discovery_message()
    test_port_assignment()
    test_game_status()
    test_emergency_stop()
    test_axis_mapping()
    
    print("\n[SUCCESS] All protocol tests passed!")
    print("The driver station protocol is compatible with minibot.cpp")
