#!/usr/bin/env python3
"""
Mock Serial for Dear PyGui Testing

Simulates hardware for testing without physical device.
"""

import threading
import time
import math
import random
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class DataPoint:
    """Data point from tensile test."""
    timestamp: float
    force: float
    extension: float
    stress: float
    strain: float


@dataclass 
class Status:
    """Machine status."""
    state: str
    force: float
    position: float
    is_running: bool


class MockSerialHandler:
    """Mock serial handler that simulates tensile test hardware."""
    
    def __init__(self):
        self._running = False
        self._test_thread: Optional[threading.Thread] = None
        self._connected = False
        
        # State
        self._state = "IDLE"
        self._force = 0.0
        self._position = 0.0
        self._is_testing = False
        self._is_paused = False
        
        # Test parameters
        self._speed = 1.0
        self._max_force = 450.0
        self._max_extension = 100.0
        
        # Specimen parameters (for simulation)
        self._gauge_length = 50.0  # mm
        self._cross_section = 12.57  # mm² (4mm diameter)
        
        # Callbacks
        self.on_connected = None
        self.on_disconnected = None
        self.on_status = None
        self.on_data = None
        self.on_force = None
        self.on_position = None
        self.on_response = None
        self.on_error = None
    
    @staticmethod
    def list_ports() -> List[str]:
        return ["MOCK_PICO"]
    
    @staticmethod
    def find_pico() -> Optional[str]:
        return "MOCK_PICO"
    
    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Simulate connection."""
        print(f"[MockSerial] Connecting to {port}...")
        time.sleep(0.3)  # Simulate connection delay
        
        self._connected = True
        self._state = "IDLE"
        self._running = True
        
        if self.on_connected:
            self.on_connected()
        
        if self.on_response:
            self.on_response("Connected to Mock Pico")
        
        print(f"[MockSerial] Connected!")
        return True
    
    def disconnect(self):
        """Disconnect."""
        self._running = False
        self._is_testing = False
        
        if self._test_thread:
            self._test_thread.join(timeout=2.0)
            self._test_thread = None
        
        self._connected = False
        self._state = "DISCONNECTED"
        
        if self.on_disconnected:
            self.on_disconnected()
        
        print("[MockSerial] Disconnected")
    
    def is_connected(self) -> bool:
        return self._connected
    
    def send_command(self, command: str) -> bool:
        if not self._connected:
            return False
        print(f"[MockSerial] Command: {command}")
        return True
    
    def start_test(self) -> bool:
        """Start simulated test."""
        if not self._connected or self._is_testing:
            return False
        
        print("[MockSerial] Starting test simulation...")
        self._is_testing = True
        self._is_paused = False
        self._state = "RUNNING"
        self._position = 0.0
        self._force = 0.0
        
        # Start test thread
        self._test_thread = threading.Thread(target=self._run_test, daemon=True)
        self._test_thread.start()
        
        if self.on_response:
            self.on_response("Test started")
        
        return True
    
    def stop_test(self) -> bool:
        """Stop test."""
        self._is_testing = False
        self._state = "IDLE"
        
        if self.on_response:
            self.on_response("Test stopped")
        return True
    
    def pause_test(self) -> bool:
        """Pause test."""
        self._is_paused = True
        self._state = "PAUSED"
        
        if self.on_response:
            self.on_response("Test paused")
        return True
    
    def resume_test(self) -> bool:
        """Resume test."""
        self._is_paused = False
        self._state = "RUNNING"
        
        if self.on_response:
            self.on_response("Test resumed")
        return True
    
    def emergency_stop(self) -> bool:
        """Emergency stop."""
        self._is_testing = False
        self._is_paused = False
        self._state = "ESTOP"
        
        if self.on_response:
            self.on_response("EMERGENCY STOP!")
        return True
    
    def home(self) -> bool:
        """Home machine."""
        self._state = "HOMING"
        self._position = 0.0
        self._force = 0.0
        
        # Simulate homing
        def do_home():
            time.sleep(1.0)
            self._state = "IDLE"
            if self.on_response:
                self.on_response("Homing complete")
        
        threading.Thread(target=do_home, daemon=True).start()
        return True
    
    def tare(self) -> bool:
        """Tare load cell."""
        self._force = 0.0
        
        if self.on_response:
            self.on_response("Tare complete")
        return True
    
    def set_speed(self, speed: float) -> bool:
        self._speed = speed
        return True
    
    def set_max_force(self, force: float) -> bool:
        self._max_force = force
        return True
    
    def set_max_extension(self, extension: float) -> bool:
        self._max_extension = extension
        return True
    
    def get_status(self) -> bool:
        """Get current status."""
        if self.on_status:
            status = Status(
                state=self._state,
                force=self._force,
                position=self._position,
                is_running=self._is_testing and not self._is_paused
            )
            self.on_status(status)
        return True
    
    def get_force(self) -> bool:
        if self.on_force:
            self.on_force(self._force)
        return True
    
    def get_position(self) -> bool:
        if self.on_position:
            self.on_position(self._position)
        return True
    
    def identify(self) -> bool:
        if self.on_response:
            self.on_response("ID Mock Pico Tensile Tester v2.0")
        return True
    
    def jog_up(self, distance: float = 0) -> bool:
        return True
    
    def jog_down(self, distance: float = 0) -> bool:
        return True
    
    def stop_jog(self) -> bool:
        return True
    
    def reset(self) -> bool:
        self._state = "IDLE"
        return True
    
    def _run_test(self):
        """Run simulated tensile test with hybrid time + event-based sampling."""
        print("[MockSerial] Test thread started (Hybrid Sampling)")
        print(f"[MockSerial] Speed: {self._speed} mm/s, Max ext: {self._max_extension} mm")
        
        # Material simulation parameters - more realistic for longer test
        # Simulating a ductile polymer or soft metal
        yield_extension = 2.0    # mm - yield point
        ultimate_extension = 15.0  # mm - peak force
        break_extension = 25.0   # mm - failure
        
        # Scale to max extension if needed
        if self._max_extension < break_extension:
            scale = self._max_extension / break_extension
            yield_extension *= scale
            ultimate_extension *= scale
            break_extension = self._max_extension * 0.95
        
        # Force parameters
        yield_force = 50.0       # N at yield
        ultimate_force = 80.0    # N at peak (UTS)
        
        start_time = time.time()
        last_sample_time = start_time
        last_force = 0.0
        last_slope = 0.0
        
        # Hybrid sampling parameters
        BASE_INTERVAL = 0.1      # 100ms = 10 Hz base rate
        EVENT_INTERVAL = 0.02    # 20ms = 50 Hz during events
        FORCE_THRESHOLD = 2.0    # N - trigger event sampling (reduced for sensitivity)
        SLOPE_THRESHOLD = 0.2    # 20% slope change
        MIN_EVENT_INTERVAL = 0.02  # Minimum 20ms between event samples
        
        last_event_time = 0
        in_event_mode = False
        sample_count = 0
        
        while self._is_testing and self._running:
            if self._is_paused:
                time.sleep(0.05)
                continue
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Move crosshead (continuous)
            dt_move = 0.01  # 10ms physics update
            self._position += self._speed * dt_move
            extension = self._position
            
            # Calculate strain
            strain = extension / self._gauge_length
            
            # Calculate force using extension-based material model
            if extension < yield_extension:
                # Elastic region - linear
                force = (extension / yield_extension) * yield_force
            elif extension < ultimate_extension:
                # Plastic region - strain hardening
                progress = (extension - yield_extension) / (ultimate_extension - yield_extension)
                force = yield_force + progress * (ultimate_force - yield_force)
            elif extension < break_extension:
                # Necking - force decreases
                progress = (extension - ultimate_extension) / (break_extension - ultimate_extension)
                force = ultimate_force * (1.0 - 0.6 * progress)
            else:
                # Broken
                force = 0.0
                self._is_testing = False
                self._state = "COMPLETE"
                print(f"[MockSerial] Specimen failed at {extension:.1f}mm!")
            
            # Add noise
            force += random.gauss(0, 0.5)
            force = max(0, force)
            self._force = force
            
            # Calculate stress from force
            stress = force / self._cross_section
            
            # === Hybrid Sampling Decision ===
            time_since_last_sample = current_time - last_sample_time
            time_since_last_event = current_time - last_event_time
            
            # Event detection
            force_change = abs(force - last_force)
            current_slope = (force - last_force) / max(dt_move, 0.001)
            slope_change = abs(current_slope - last_slope) / max(abs(last_slope), 0.1)
            
            # Check for events
            event_detected = False
            if force_change > FORCE_THRESHOLD:
                event_detected = True
            if slope_change > SLOPE_THRESHOLD and abs(last_slope) > 1.0:
                event_detected = True
            if force > 0.95 * ultimate_force:
                event_detected = True  # Near peak
            if last_force > 10 and force < last_force * 0.9:
                event_detected = True  # Force drop (failure)
            
            # Determine if we should sample
            should_sample = False
            
            if event_detected and time_since_last_event >= MIN_EVENT_INTERVAL:
                should_sample = True
                in_event_mode = True
                last_event_time = current_time
            elif in_event_mode and time_since_last_sample >= EVENT_INTERVAL:
                should_sample = True
                if time_since_last_event > 0.5:
                    in_event_mode = False
            elif time_since_last_sample >= BASE_INTERVAL:
                should_sample = True
            
            # Send data point if sampling
            if should_sample:
                sample_count += 1
                last_sample_time = current_time
                last_slope = current_slope
                last_force = force
                
                if self.on_data:
                    data = DataPoint(
                        timestamp=elapsed * 1000,  # ms
                        force=force,
                        extension=extension,
                        stress=stress,
                        strain=strain
                    )
                    self.on_data(data)
            
            # Check limits
            if force > self._max_force:
                print(f"[MockSerial] Max force ({self._max_force}N) reached!")
                self._is_testing = False
                self._state = "COMPLETE"
            
            if extension > self._max_extension:
                print(f"[MockSerial] Max extension ({self._max_extension}mm) reached!")
                self._is_testing = False
                self._state = "COMPLETE"
            
            time.sleep(dt_move)
        
        print(f"[MockSerial] Test ended - {sample_count} data points collected")
        
        if self.on_response:
            self.on_response("Test complete")


# Create singleton instance
_mock_handler = None


def get_mock_handler():
    """Get or create mock handler instance."""
    global _mock_handler
    if _mock_handler is None:
        _mock_handler = MockSerialHandler()
    return _mock_handler
