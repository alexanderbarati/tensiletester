#!/usr/bin/env python3
"""
Test Runner for Tensile Tester GUI

Runs the GUI with a mock serial port to simulate hardware.
No physical hardware required!
"""

import sys
import os

# Add gui directory to path
gui_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, gui_dir)

# IMPORTANT: Patch serial BEFORE importing serial_handler
print("=" * 60)
print("  TENSILE TESTER GUI - TEST MODE (No Hardware)")
print("=" * 60)
print("\nPatching serial module with mock implementation...")

from mock_serial import patch_serial
patch_serial()

print("Mock serial ready!")
print("\n" + "-" * 60)
print("SIMULATED HARDWARE:")
print("  - Raspberry Pi Pico (Mock)")
print("  - NAU7802 24-bit ADC (simulated)")
print("  - DM542T Stepper Driver (simulated)")
print("  - 500N S-type Load Cell (simulated material response)")
print("-" * 60)
print("\nINSTRUCTIONS:")
print("  1. Click 'Connect' to connect to mock controller")
print("  2. Click 'HOME' to initialize (simulated)")
print("  3. Click 'START' to run a simulated tensile test")
print("  4. Watch the real-time force vs extension plot")
print("  5. The simulation includes realistic material behavior:")
print("     - Initial settling")
print("     - Linear elastic region")
print("     - Yield and plastic deformation")
print("     - Material failure")
print("-" * 60 + "\n")

# Now import and run the GUI
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import after patching
from main_window import MainWindow


def main():
    """Main test entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Tensile Tester (TEST MODE)")
    app.setOrganizationName("DIY")
    app.setApplicationVersion("2.0.0-TEST")
    
    # Set dark theme stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-size: 14px;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 10px 20px;
            min-height: 40px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        QPushButton:disabled {
            background-color: #1a1a1a;
            color: #666666;
        }
        QPushButton#startButton {
            background-color: #2e7d32;
        }
        QPushButton#startButton:hover {
            background-color: #388e3c;
        }
        QPushButton#stopButton {
            background-color: #c62828;
        }
        QPushButton#stopButton:hover {
            background-color: #d32f2f;
        }
        QPushButton#emergencyButton {
            background-color: #b71c1c;
            font-size: 18px;
            font-weight: bold;
        }
        QLabel {
            color: #ffffff;
        }
        QLabel#valueLabel {
            font-size: 32px;
            font-weight: bold;
            color: #4fc3f7;
        }
        QLabel#unitLabel {
            font-size: 16px;
            color: #888888;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            min-height: 30px;
        }
        QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            min-height: 30px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            selection-background-color: #4a4a4a;
        }
        QStatusBar {
            background-color: #1a1a1a;
            color: #888888;
        }
        QFrame {
            border-radius: 5px;
        }
    """)
    
    # Create main window
    window = MainWindow()
    window.setWindowTitle("Tensile Tester - TEST MODE (No Hardware)")
    
    # Always windowed for testing
    window.resize(1024, 600)
    window.show()
    
    print("GUI started! Window should be visible now.")
    print("\nNote: Select 'MOCK_PICO' from the port dropdown and click Connect.\n")
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
