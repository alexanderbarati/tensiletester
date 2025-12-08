#!/usr/bin/env python3
"""
Raspberry Pi Configuration

Performance optimizations for running on Raspberry Pi 4
with Waveshare 7" 1024x600 display.
"""

import platform
import os

# Detect if running on Raspberry Pi
def is_raspberry_pi():
    """Check if running on Raspberry Pi."""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            return 'BCM' in cpuinfo or 'Raspberry' in cpuinfo
    except:
        return False

# Platform detection
IS_RASPBERRY_PI = is_raspberry_pi()
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Display settings
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 600
FULLSCREEN = IS_RASPBERRY_PI  # Fullscreen on Pi only

# Performance settings - CRITICAL for Pi
if IS_RASPBERRY_PI:
    # Pi-optimized settings
    PLOT_UPDATE_RATE_MS = 200      # 5 Hz plot updates (reduce GPU load)
    STATUS_POLL_RATE_MS = 500      # 2 Hz status polling
    PLOT_MAX_POINTS = 500          # Limit points in live plot
    PLOT_DOWNSAMPLE = True         # Enable downsampling
    USE_OPENGL = True              # Hardware acceleration
    ANTIALIAS = False              # Disable antialiasing (faster)
    DATA_BUFFER_SIZE = 10000       # Limit data buffer
    UI_ANIMATION = False           # Disable animations
else:
    # Desktop settings (can handle more)
    PLOT_UPDATE_RATE_MS = 100      # 10 Hz plot updates
    STATUS_POLL_RATE_MS = 200      # 5 Hz status polling
    PLOT_MAX_POINTS = 2000         # More points in live plot
    PLOT_DOWNSAMPLE = False        # Full resolution
    USE_OPENGL = False             # Software rendering OK
    ANTIALIAS = True               # Nice antialiasing
    DATA_BUFFER_SIZE = 50000       # Larger buffer
    UI_ANIMATION = True            # Smooth animations

# PyQtGraph configuration
def configure_pyqtgraph():
    """Apply pyqtgraph optimizations."""
    import pyqtgraph as pg
    
    # Set rendering options
    pg.setConfigOptions(
        antialias=ANTIALIAS,
        useOpenGL=USE_OPENGL,
        enableExperimental=False,
        crashWarning=False
    )
    
    # Reduce GPU memory on Pi
    if IS_RASPBERRY_PI:
        pg.setConfigOption('background', '#1a1a1a')
        pg.setConfigOption('foreground', 'w')

# Qt optimizations for Pi
def configure_qt_for_pi():
    """Configure Qt settings for Pi."""
    if not IS_RASPBERRY_PI:
        return
    
    # Set environment variables BEFORE creating QApplication
    os.environ['QT_QPA_PLATFORM'] = 'xcb'  # Use X11
    os.environ['QT_QUICK_BACKEND'] = 'software'  # Fallback renderer
    
    # Disable Qt animations
    os.environ['QT_ENABLE_ANIMATIONS'] = '0'
    
    # Use smaller font cache
    os.environ['QT_ENABLE_GLYPH_CACHE_WORKAROUND'] = '1'

# Color scheme (dark theme, good for labs)
COLORS = {
    'background': '#1a1a1a',
    'panel': '#2d2d2d', 
    'text': '#ffffff',
    'text_dim': '#888888',
    'accent': '#4fc3f7',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'plot_line': '#4fc3f7',
    'plot_grid': '#333333',
}

# Font sizes (slightly larger for touchscreen)
FONTS = {
    'title': 14 if IS_RASPBERRY_PI else 12,
    'normal': 11 if IS_RASPBERRY_PI else 10,
    'small': 10 if IS_RASPBERRY_PI else 9,
    'value': 16 if IS_RASPBERRY_PI else 14,
}

# Button sizes (larger for touch)
BUTTON_HEIGHT = 50 if IS_RASPBERRY_PI else 40
BUTTON_MIN_WIDTH = 100 if IS_RASPBERRY_PI else 80

# Stylesheet for Pi (larger touch targets)
PI_STYLESHEET = """
QMainWindow {
    background-color: #1a1a1a;
}
QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    font-size: 11px;
}
QGroupBox {
    background-color: #2d2d2d;
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QPushButton {
    background-color: #3d3d3d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 10px 16px;
    min-height: 40px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #4d4d4d;
}
QPushButton:pressed {
    background-color: #2d2d2d;
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666;
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
    font-weight: bold;
    font-size: 14px;
}
QPushButton#emergencyButton:hover {
    background-color: #c62828;
}
QComboBox {
    background-color: #3d3d3d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 8px;
    min-height: 30px;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QDoubleSpinBox, QSpinBox {
    background-color: #3d3d3d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 8px;
    min-height: 30px;
}
QLabel#valueLabel {
    color: #4fc3f7;
    font-size: 18px;
    font-weight: bold;
}
QLabel#unitLabel {
    color: #888;
    font-size: 12px;
}
QFrame {
    background-color: #2d2d2d;
    border-radius: 4px;
}
QStatusBar {
    background-color: #2d2d2d;
    color: #888;
}
QTabWidget::pane {
    border: 1px solid #444;
    background-color: #2d2d2d;
}
QTabBar::tab {
    background-color: #3d3d3d;
    padding: 10px 20px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #4fc3f7;
    color: #000;
}
"""

def get_stylesheet():
    """Get platform-appropriate stylesheet."""
    return PI_STYLESHEET


# Serial port settings
SERIAL_TIMEOUT = 0.1 if IS_RASPBERRY_PI else 0.05
SERIAL_BUFFER_SIZE = 4096

# Print configuration on import
def print_config():
    """Print current configuration."""
    print(f"Platform: {'Raspberry Pi' if IS_RASPBERRY_PI else platform.system()}")
    print(f"Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    print(f"Plot update rate: {PLOT_UPDATE_RATE_MS}ms")
    print(f"OpenGL: {USE_OPENGL}")
    print(f"Antialiasing: {ANTIALIAS}")
