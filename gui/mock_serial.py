#!/usr/bin/env python3
"""
Mock Serial Port for Testing

Simulates the Raspberry Pi Pico tensile tester controller
for GUI testing without physical hardware.
"""

import threading
import time
import random
import math
from collections import deque
from typing import Optional


class MockSerial:
    """
    Mock serial port that simulates the Pico controller.
    
    Simulates:
    - Force readings (with noise)
    - Position tracking
    - State machine responses
    - Test data generation
    """
    
    def __init__(self, port: str = "MOCK", baudrate: int = 115200, timeout: float = 0.1, **kwargs):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._is_open = True
        
        # Simulated state
        self._state = "IDLE"
        self._force = 0.0
        self._position = 0.0
        self._is_running = False
        self._is_paused = False
        
        # Test parameters
        self._speed = 1.0  # mm/s
        self._max_force = 450.0  # N
        self._max_extension = 100.0  # mm
        
        # Simulation parameters
        self._test_start_time = 0
        self._specimen_stiffness = 50.0  # N/mm (simulated material)
        self._yield_force = 300.0  # N
        self._break_force = 400.0  # N
        
        # Response buffer
        self._read_buffer = deque()
        self._lock = threading.Lock()
        
        # Simulation thread
        self._sim_running = True
        self._sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._sim_thread.start()
        
        print(f"[MockSerial] Initialized on {port}")
    
    @property
    def is_open(self) -> bool:
        return self._is_open
    
    @property
    def in_waiting(self) -> int:
        with self._lock:
            # Calculate total bytes in buffer
            return sum(len(line) for line in self._read_buffer)
    
    def open(self):
        self._is_open = True
    
    def close(self):
        self._is_open = False
        self._sim_running = False
    
    def reset_input_buffer(self):
        with self._lock:
            self._read_buffer.clear()
    
    def reset_output_buffer(self):
        pass
    
    def write(self, data: bytes) -> int:
        """Process incoming commands."""
        if not self._is_open:
            raise Exception("Port not open")
        
        command = data.decode('utf-8').strip().upper()
        self._process_command(command)
        return len(data)
    
    def readline(self) -> bytes:
        """Read a line from the response buffer."""
        if not self._is_open:
            raise Exception("Port not open")
        
        with self._lock:
            if self._read_buffer:
                return self._read_buffer.popleft()
        return b''
    
    def read(self, size: int = 1) -> bytes:
        """Read bytes from buffer."""
        return self.readline()
    
    def _queue_response(self, response: str):
        """Add response to read buffer."""
        with self._lock:
            self._read_buffer.append((response + '\n').encode('utf-8'))
    
    def _process_command(self, command: str):
        """Process a command and queue response."""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        print(f"[MockSerial] Command: {command}")
        
        if cmd == "ID":
            self._queue_response("ID TensileTester v2.0 Pico-NAU7802-DM542T")
        
        elif cmd == "STATUS":
            running = "1" if self._is_running else "0"
            self._queue_response(
                f"STATUS {self._state} F:{self._force:.2f} P:{self._position:.3f} R:{running}"
            )
        
        elif cmd == "FORCE":
            self._queue_response(f"FORCE {self._force:.2f}")
        
        elif cmd == "POS":
            self._queue_response(f"POS {self._position:.3f}")
        
        elif cmd == "CONFIG":
            self._queue_response(
                f"CONFIG SPEED:{self._speed} MAXF:{self._max_force} MAXE:{self._max_extension}"
            )
        
        elif cmd == "START":
            if self._state in ["IDLE", "READY"]:
                self._state = "RUNNING"
                self._is_running = True
                self._is_paused = False
                self._test_start_time = time.time()
                self._position = 0.0
                self._force = 0.0
                self._queue_response("OK Test started")
            else:
                self._queue_response(f"ERROR Cannot start from state {self._state}")
        
        elif cmd == "STOP":
            self._state = "READY"
            self._is_running = False
            self._is_paused = False
            self._queue_response("OK Test stopped")
        
        elif cmd == "PAUSE":
            if self._is_running and not self._is_paused:
                self._state = "PAUSED"
                self._is_paused = True
                self._queue_response("OK Test paused")
            else:
                self._queue_response("ERROR Cannot pause")
        
        elif cmd == "RESUME":
            if self._is_paused:
                self._state = "RUNNING"
                self._is_paused = False
                self._queue_response("OK Test resumed")
            else:
                self._queue_response("ERROR Not paused")
        
        elif cmd == "ESTOP":
            self._state = "EMERGENCY"
            self._is_running = False
            self._is_paused = False
            self._queue_response("OK Emergency stop activated")
        
        elif cmd == "HOME":
            self._state = "HOMING"
            self._queue_response("OK Homing...")
            # Simulate homing
            threading.Timer(2.0, self._complete_homing).start()
        
        elif cmd == "TARE":
            self._force = 0.0
            self._queue_response("OK Tared")
        
        elif cmd == "UP":
            distance = float(args[0]) if args else 1.0
            self._position = max(0, self._position - distance)
            self._queue_response("OK Moving up")
        
        elif cmd == "DOWN":
            distance = float(args[0]) if args else 1.0
            self._position = min(self._max_extension, self._position + distance)
            self._queue_response("OK Moving down")
        
        elif cmd == "HALT":
            self._queue_response("OK Movement stopped")
        
        elif cmd == "SPEED":
            if args:
                self._speed = float(args[0])
                self._queue_response(f"OK Speed set to {self._speed}")
            else:
                self._queue_response("ERROR Missing speed value")
        
        elif cmd == "MAXFORCE":
            if args:
                self._max_force = float(args[0])
                self._queue_response(f"OK Max force set to {self._max_force}")
            else:
                self._queue_response("ERROR Missing force value")
        
        elif cmd == "MAXEXT":
            if args:
                self._max_extension = float(args[0])
                self._queue_response(f"OK Max extension set to {self._max_extension}")
            else:
                self._queue_response("ERROR Missing extension value")
        
        elif cmd == "RESET":
            self._state = "IDLE"
            self._is_running = False
            self._is_paused = False
            self._position = 0.0
            self._force = 0.0
            self._queue_response("OK System reset")
        
        else:
            self._queue_response(f"ERROR Unknown command: {cmd}")
    
    def _complete_homing(self):
        """Complete homing sequence."""
        self._state = "READY"
        self._position = 0.0
        self._queue_response("OK Homing complete")
    
    def _simulation_loop(self):
        """Background simulation loop."""
        last_data_time = 0
        
        while self._sim_running:
            time.sleep(0.05)  # 20 Hz simulation
            
            if self._is_running and not self._is_paused:
                # Update position based on speed
                dt = 0.05
                self._position += self._speed * dt
                
                # Simulate material response (stress-strain curve with noise)
                if self._position < 5:
                    # Initial slack/settling
                    self._force = random.uniform(0, 2)
                elif self._position < 30:
                    # Linear elastic region
                    base_force = (self._position - 5) * self._specimen_stiffness / 5
                    self._force = base_force + random.uniform(-2, 2)
                elif self._position < 50:
                    # Yield/plastic region
                    progress = (self._position - 30) / 20
                    base_force = self._yield_force + progress * (self._break_force - self._yield_force)
                    # Add some yielding behavior
                    self._force = base_force + random.uniform(-5, 5) + 10 * math.sin(self._position)
                else:
                    # Post-yield softening and break
                    if self._position > 60:
                        # Material breaking
                        self._force = max(0, self._force - 50)
                        if self._force < 10:
                            self._state = "READY"
                            self._is_running = False
                            self._queue_response("OK Test complete - specimen failed")
                    else:
                        progress = (self._position - 50) / 10
                        self._force = self._break_force - progress * 50 + random.uniform(-10, 10)
                
                self._force = max(0, self._force)
                
                # Check limits
                if self._force >= self._max_force:
                    self._state = "READY"
                    self._is_running = False
                    self._queue_response("OK Test stopped - max force reached")
                
                if self._position >= self._max_extension:
                    self._state = "READY"
                    self._is_running = False
                    self._queue_response("OK Test stopped - max extension reached")
                
                # Send data point every 100ms
                now = time.time()
                if now - last_data_time >= 0.1:
                    last_data_time = now
                    timestamp = (now - self._test_start_time) * 1000
                    # Calculate stress/strain (assuming 10mm^2 cross-section, 50mm gauge length)
                    stress = self._force / 10.0  # MPa
                    strain = self._position / 50.0  # ratio
                    
                    self._queue_response(
                        f"DATA {timestamp:.1f},{self._force:.2f},{self._position:.3f},{stress:.3f},{strain:.5f}"
                    )
            
            # Add some noise to force reading even when idle
            elif self._state in ["IDLE", "READY"]:
                self._force = random.uniform(-0.5, 0.5)


# Patch serial module for testing
class MockSerialModule:
    """Mock serial module that returns MockSerial instances."""
    
    Serial = MockSerial
    
    class tools:
        class list_ports:
            @staticmethod
            def comports():
                """Return mock port list."""
                class MockPort:
                    def __init__(self, device, description, hwid):
                        self.device = device
                        self.description = description
                        self.hwid = hwid
                
                return [
                    MockPort("MOCK_PICO", "Raspberry Pi Pico (Mock)", "USB VID:PID=2E8A:000A"),
                    MockPort("COM1", "Communications Port", ""),
                ]


def patch_serial():
    """Patch the serial module with mock implementation."""
    import sys
    sys.modules['serial'] = MockSerialModule()
    sys.modules['serial.tools'] = MockSerialModule.tools
    sys.modules['serial.tools.list_ports'] = MockSerialModule.tools.list_ports
    print("[MockSerial] Serial module patched for testing")


if __name__ == "__main__":
    # Test the mock serial directly
    mock = MockSerial("TEST")
    
    mock.write(b"ID\n")
    print(mock.readline())
    
    mock.write(b"STATUS\n")
    print(mock.readline())
    
    mock.write(b"START\n")
    print(mock.readline())
    
    time.sleep(1)
    
    mock.write(b"STATUS\n")
    time.sleep(0.1)
    while mock.in_waiting:
        print(mock.readline())
    
    mock.write(b"STOP\n")
    print(mock.readline())
    
    mock.close()
