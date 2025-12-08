#!/usr/bin/env python3
"""
Tensile Tester GUI Application

Main entry point for the tensile testing machine GUI.
Runs on Raspberry Pi 4 with Waveshare 7" display (1024x600).

Author: DIY Tensile Tester Project
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from main_window import MainWindow


def main():
    """Main application entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Tensile Tester")
    app.setOrganizationName("DIY")
    app.setApplicationVersion("2.0.0")
    
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
        QStatusBar {
            background-color: #1a1a1a;
            color: #888888;
        }
        QMenuBar {
            background-color: #1a1a1a;
        }
        QMenuBar::item:selected {
            background-color: #3c3c3c;
        }
        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #555555;
        }
        QMenu::item:selected {
            background-color: #3c3c3c;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 10px 20px;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
        }
    """)
    
    # Create main window
    window = MainWindow()
    
    # Show fullscreen on Raspberry Pi, windowed on desktop
    if os.path.exists('/proc/device-tree/model'):
        # Running on Raspberry Pi
        window.showFullScreen()
    else:
        # Running on desktop for development
        window.resize(1024, 600)
        window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
