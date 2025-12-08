#!/usr/bin/env python3
"""
Serial Communication Handler

Manages serial communication with the Raspberry Pi Pico.
Optimized for Raspberry Pi performance.
"""

import serial
import serial.tools.list_ports
import threading
import queue
import time
from dataclasses import dataclass
from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, pyqtSignal

# Import Pi configuration
try:
    from pi_config import IS_RASPBERRY_PI, SERIAL_TIMEOUT, SERIAL_BUFFER_SIZE
except ImportError:
    IS_RASPBERRY_PI = False
    SERIAL_TIMEOUT = 0.1
    SERIAL_BUFFER_SIZE = 4096


@dataclass
class DataPoint:
    """Data point from tensile test."""
    timestamp: float  # ms
    force: float      # N
    extension: float  # mm
    stress: float     # MPa
    strain: float     # ratio


@dataclass
class Status:
    """Machine status."""
    state: str
    force: float
    position: float
    is_running: bool


class SerialHandler(QObject):
    """
    Handles serial communication with the Pico controller.
    
    Signals:
        connected: Emitted when connection established
        disconnected: Emitted when connection lost
        status_received: Emitted when status update received
        data_received: Emitted when test data point received
        force_received: Emitted when force reading received
        position_received: Emitted when position reading received
        response_received: Emitted when command response received
        error_occurred: Emitted when error occurs
    """
    
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    status_received = pyqtSignal(object)  # Status
    data_received = pyqtSignal(object)    # DataPoint
    force_received = pyqtSignal(float)
    position_received = pyqtSignal(float)
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._command_queue = queue.Queue()
        self._lock = threading.Lock()
    
    @staticmethod
    def list_ports() -> List[str]:
        """List available serial ports."""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        return ports
    
    @staticmethod
    def find_pico() -> Optional[str]:
        """Find Raspberry Pi Pico serial port."""
        for port in serial.tools.list_ports.comports():
            # Pico shows as "USB Serial Device" or contains "Pico"
            if "Pico" in port.description or "2E8A" in port.hwid:
                return port.device
            # Also check for generic USB serial (Pico in CDC mode)
            if "USB Serial" in port.description:
                return port.device
        return None
    
    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """
        Connect to serial port.
        
        Args:
            port: Serial port name
            baudrate: Baud rate (default 115200)
            
        Returns:
            True if connected successfully
        """
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=SERIAL_TIMEOUT,  # Pi-optimized
                write_timeout=1.0
            )
            time.sleep(0.5)  # Wait for connection
            
            # Clear any pending data
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Start read thread
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            
            self.connected.emit()
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        
        if self.serial:
            try:
                self.serial.close()
            except:
                pass
            self.serial = None
        
        self.disconnected.emit()
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.serial is not None and self.serial.is_open
    
    def send_command(self, command: str) -> bool:
        """
        Send command to controller.
        
        Args:
            command: Command string
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected():
            return False
        
        try:
            with self._lock:
                cmd = command.strip() + '\n'
                self.serial.write(cmd.encode('utf-8'))
                return True
        except Exception as e:
            self.error_occurred.emit(f"Send failed: {str(e)}")
            return False
    
    # Convenience methods for common commands
    def start_test(self) -> bool:
        return self.send_command("START")
    
    def stop_test(self) -> bool:
        return self.send_command("STOP")
    
    def pause_test(self) -> bool:
        return self.send_command("PAUSE")
    
    def resume_test(self) -> bool:
        return self.send_command("RESUME")
    
    def emergency_stop(self) -> bool:
        return self.send_command("ESTOP")
    
    def home(self) -> bool:
        return self.send_command("HOME")
    
    def jog_up(self, distance: float = 0) -> bool:
        if distance > 0:
            return self.send_command(f"UP {distance}")
        return self.send_command("UP")
    
    def jog_down(self, distance: float = 0) -> bool:
        if distance > 0:
            return self.send_command(f"DOWN {distance}")
        return self.send_command("DOWN")
    
    def stop_jog(self) -> bool:
        return self.send_command("HALT")
    
    def tare(self) -> bool:
        return self.send_command("TARE")
    
    def set_speed(self, speed: float) -> bool:
        return self.send_command(f"SPEED {speed}")
    
    def set_max_force(self, force: float) -> bool:
        return self.send_command(f"MAXFORCE {force}")
    
    def set_max_extension(self, extension: float) -> bool:
        return self.send_command(f"MAXEXT {extension}")
    
    def get_status(self) -> bool:
        return self.send_command("STATUS")
    
    def get_force(self) -> bool:
        return self.send_command("FORCE")
    
    def get_position(self) -> bool:
        return self.send_command("POS")
    
    def get_config(self) -> bool:
        return self.send_command("CONFIG")
    
    def identify(self) -> bool:
        return self.send_command("ID")
    
    def reset(self) -> bool:
        return self.send_command("RESET")
    
    def _read_loop(self):
        """Background thread for reading serial data (optimized for Pi)."""
        buffer = ""
        while self._running and self.serial:
            try:
                # Read available data in chunks (more efficient on Pi)
                if self.serial.in_waiting:
                    chunk = self.serial.read(min(self.serial.in_waiting, SERIAL_BUFFER_SIZE))
                    buffer += chunk.decode('utf-8', errors='ignore')
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self._parse_response(line)
                else:
                    # Small sleep when no data (reduces CPU usage on Pi)
                    time.sleep(0.01 if IS_RASPBERRY_PI else 0.001)
            except Exception as e:
                if self._running:
                    self.error_occurred.emit(f"Read error: {str(e)}")
                    time.sleep(0.1)
    
    def _parse_response(self, line: str):
        """Parse response from controller."""
        parts = line.split()
        if not parts:
            return
        
        cmd = parts[0].upper()
        
        if cmd == "OK":
            msg = " ".join(parts[1:]) if len(parts) > 1 else "OK"
            self.response_received.emit(msg)
            
        elif cmd == "ERROR":
            msg = " ".join(parts[1:]) if len(parts) > 1 else "Error"
            self.error_occurred.emit(msg)
            
        elif cmd == "STATUS":
            # STATUS <state> F:<force> P:<pos> R:<running>
            try:
                state = parts[1] if len(parts) > 1 else "UNKNOWN"
                force = 0.0
                position = 0.0
                running = False
                
                for part in parts[2:]:
                    if part.startswith("F:"):
                        force = float(part[2:])
                    elif part.startswith("P:"):
                        position = float(part[2:])
                    elif part.startswith("R:"):
                        running = part[2:] == "1"
                
                status = Status(state, force, position, running)
                self.status_received.emit(status)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "FORCE":
            try:
                force = float(parts[1])
                self.force_received.emit(force)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "POS":
            try:
                position = float(parts[1])
                self.position_received.emit(position)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "DATA":
            # DATA timestamp,force,extension,stress,strain
            try:
                values = parts[1].split(',')
                if len(values) >= 5:
                    data = DataPoint(
                        timestamp=float(values[0]),
                        force=float(values[1]),
                        extension=float(values[2]),
                        stress=float(values[3]),
                        strain=float(values[4])
                    )
                    self.data_received.emit(data)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "ID":
            self.response_received.emit(line)
            
        elif cmd == "CONFIG":
            self.response_received.emit(line)
