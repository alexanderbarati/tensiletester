
# Tensile Tester Project

This repository contains the complete software and firmware for a DIY Tensile Tester machine, including:
- Embedded firmware for the Raspberry Pi Pico microcontroller (C++)
- Python GUI for controlling and simulating tests (PyQt5)
- Supporting scripts, documentation, and build files

---

## Architecture Overview

**Block Diagram:**

```
┌──────────────┐      USB Serial      ┌──────────────┐
│  Raspberry   │ <-----------------> │   Raspberry  │
│  Pi Pico     │                     │   Pi 4 (GUI) │
│  (Firmware)  │                     │   or PC      │
└─────┬────────┘                     └─────┬────────┘
      │                                      │
      │                                      │
      ▼                                      ▼
 ┌──────────────┐                    ┌──────────────┐
 │  Stepper     │                    │  7" Display  │
 │  Driver      │                    └──────────────┘
 └──────────────┘
      │
      ▼
 ┌──────────────┐
 │  Load Cell   │
 │  (NAU7802)   │
 └──────────────┘
```

**Firmware** runs on the Raspberry Pi Pico, handling motor control, load cell readings, and safety logic. It communicates with the GUI via USB serial.

**GUI** runs on a Raspberry Pi 4 or PC, providing a user interface, real-time plotting, and test management. It can also run in simulation mode (no hardware required).

---

## Hardware Wiring & Pinout

**Microcontroller:** Raspberry Pi Pico (RP2040)

**Stepper Motor Driver (DM542T):**
- PUL+ (Step): GP2 (Pico) via 270-1kΩ resistor
- DIR+ (Direction): GP3 (Pico) via 270-1kΩ resistor
- ENA+ (Enable): GP4 (Pico) via 270-1kΩ resistor (LOW = enabled)
- PUL-, DIR-, ENA-: Connect to GND

**Load Cell (via NAU7802 ADC, I2C):**
- SDA: GP8 (Pico)
- SCL: GP9 (Pico)
- I2C Address: 0x2A

**Limit Switches:**
- Top: GP10 (Active LOW, pull-up)
- Bottom: GP11 (Active LOW, pull-up)

**Emergency Stop:**
- GP12 (Active LOW, pull-up, NC contact)

**LEDs:**
- Status: GP25 (onboard)
- Error: GP15 (external)

**Other:**
- Display: Waveshare 7" (connected to Pi 4)

---

## Bill of Materials (BOM)

- Raspberry Pi Pico
- Raspberry Pi 4 (for GUI, or use a PC)
- DM542T Stepper Driver
- NEMA 23 Stepper Motor
- FBFTGMRMTA S-type Load Cell (500N)
- NAU7802 24-bit ADC Module
- Limit Switches (2x)
- Emergency Stop Button
- 7" HDMI Display (Waveshare or similar)
- Power supply (as required for motor/driver)
- Misc: resistors, wiring, connectors, enclosure

---

## Serial Communication Protocol

The firmware supports the following serial commands (sent over USB):

- `START`     : Start tensile test
- `STOP`      : Stop current test
- `PAUSE`     : Pause test
- `RESUME`    : Resume paused test
- `ESTOP`     : Emergency stop
- `HOME`      : Home the machine
- `UP [mm]`   : Jog up (optional distance)
- `DOWN [mm]` : Jog down (optional distance)
- `HALT`      : Stop movement
- `SPEED x`   : Set test speed (mm/s)
- `MAXFORCE x`: Set max force limit (N)
- `MAXEXT x`  : Set max extension limit (mm)
- `TARE`      : Tare load cell
- `STATUS`    : Get current status
- `FORCE`     : Get current force
- `POS`       : Get current position
- `CONFIG`    : Get configuration
- `ID`        : Get device identification
- `RESET`     : Reset system

---

## Project Structure

- `src/` — C++ source code for the embedded firmware (Pico)
- `gui/` — Python GUI application and test scripts
- `build/` — Build artifacts and CMake files
- `CMakeLists.txt` — Top-level CMake build configuration

---

## Features
- Real-time force vs extension plotting
- Simulated hardware mode for GUI development
- Serial communication with Raspberry Pi Pico
- Material behavior simulation (elastic, plastic, failure)
- Modular and extensible codebase

---

## Requirements

### Firmware
- Raspberry Pi Pico SDK
- CMake
- C++17 compatible compiler

### GUI
- Python 3.7+
- PyQt5
- pyqtgraph

Install Python dependencies with:
```sh
pip install -r gui/requirements.txt
```

---

## Building and Running

### Firmware
1. Install the Pico SDK and toolchain
2. Configure and build with CMake:
   ```sh
   cd tensiletester
   mkdir build && cd build
   cmake ..
   make
   ```
3. Flash the resulting UF2 file to your Pico

### GUI
- To start the GUI:
  ```sh
  cd tensiletester/gui
  python app.py
  ```
- To run the GUI in test mode (with simulated hardware):
  ```sh
  python test_gui.py
  ```

---

## Documentation
- See `gui/README.md` for GUI-specific instructions.

## License
See LICENSE file for details.
