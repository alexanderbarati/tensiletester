#!/usr/bin/env python3
"""
Serial Communication Handler for Dear PyGui

Manages serial communication with the Raspberry Pi Pico.
Uses callbacks instead of Qt signals.
"""

import serial
import serial.tools.list_ports
import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable, List


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


class SerialHandler:
    """
    Handles serial communication with the Pico controller.
    Uses callbacks instead of Qt signals for Dear PyGui compatibility.
    """
    
    def __init__(self):
        self.serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Callbacks (set these to handle events)
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_status: Optional[Callable[[Status], None]] = None
        self.on_data: Optional[Callable[[DataPoint], None]] = None
        self.on_force: Optional[Callable[[float], None]] = None
        self.on_position: Optional[Callable[[float], None]] = None
        self.on_response: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
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
            if "Pico" in port.description or "2E8A" in port.hwid:
                return port.device
            if "USB Serial" in port.description:
                return port.device
        return None
    
    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to serial port."""
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=0.1,
                write_timeout=1.0
            )
            time.sleep(0.5)
            
            # Clear buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Start read thread
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            
            if self.on_connected:
                self.on_connected()
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Connection failed: {str(e)}")
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
        
        if self.on_disconnected:
            self.on_disconnected()
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.serial is not None and self.serial.is_open
    
    def send_command(self, command: str) -> bool:
        """Send command to controller."""
        if not self.is_connected():
            return False
        
        try:
            with self._lock:
                cmd = command.strip() + '\n'
                self.serial.write(cmd.encode('utf-8'))
                return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Send failed: {str(e)}")
            return False
    
    # Convenience methods
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
    
    def identify(self) -> bool:
        return self.send_command("ID")
    
    def reset(self) -> bool:
        return self.send_command("RESET")
    
    def _read_loop(self):
        """Background thread for reading serial data."""
        buffer = ""
        while self._running and self.serial:
            try:
                if self.serial.in_waiting:
                    chunk = self.serial.read(min(self.serial.in_waiting, 4096))
                    buffer += chunk.decode('utf-8', errors='ignore')
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self._parse_response(line)
                else:
                    time.sleep(0.01)
            except Exception as e:
                if self._running and self.on_error:
                    self.on_error(f"Read error: {str(e)}")
                time.sleep(0.1)
    
    def _parse_response(self, line: str):
        """Parse response from controller."""
        parts = line.split()
        if not parts:
            return
        
        cmd = parts[0].upper()
        
        if cmd == "OK":
            msg = " ".join(parts[1:]) if len(parts) > 1 else "OK"
            if self.on_response:
                self.on_response(msg)
            
        elif cmd == "ERROR":
            msg = " ".join(parts[1:]) if len(parts) > 1 else "Error"
            if self.on_error:
                self.on_error(msg)
            
        elif cmd == "STATUS":
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
                if self.on_status:
                    self.on_status(status)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "FORCE":
            try:
                force = float(parts[1])
                if self.on_force:
                    self.on_force(force)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "POS":
            try:
                position = float(parts[1])
                if self.on_position:
                    self.on_position(position)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "DATA":
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
                    if self.on_data:
                        self.on_data(data)
            except (ValueError, IndexError):
                pass
                
        elif cmd == "ID":
            if self.on_response:
                self.on_response(line)
            
        elif cmd == "CONFIG":
            if self.on_response:
                self.on_response(line)
