#!/usr/bin/env python3
"""
Tensile Tester GUI Application

Main entry point for the tensile testing machine GUI.
Runs on Raspberry Pi 4 with Waveshare 7" display (1024x600).
Optimized for Raspberry Pi performance.

Author: DIY Tensile Tester Project
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Pi configuration FIRST (sets environment variables)
from pi_config import (
    IS_RASPBERRY_PI, configure_qt_for_pi, configure_pyqtgraph,
    get_stylesheet, DISPLAY_WIDTH, DISPLAY_HEIGHT, FULLSCREEN,
    print_config
)

# Configure Qt BEFORE importing Qt
configure_qt_for_pi()

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from main_window import MainWindow


def main():
    """Main application entry point."""
    # Print configuration
    print_config()
    
    # Enable high DPI scaling (only on desktop)
    if not IS_RASPBERRY_PI:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Configure pyqtgraph (OpenGL, antialiasing)
    configure_pyqtgraph()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Tensile Tester")
    app.setOrganizationName("DIY")
    app.setApplicationVersion("2.0.0")
    
    # Set Pi-optimized stylesheet
    app.setStyleSheet(get_stylesheet())
    
    # Create main window
    window = MainWindow()
    
    # Show fullscreen on Raspberry Pi, windowed on desktop
    if FULLSCREEN:
        window.showFullScreen()
    else:
        window.resize(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
