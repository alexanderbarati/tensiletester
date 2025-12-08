#!/bin/bash
#
# Tensile Tester Launch Script for Raspberry Pi
# 
# This script starts the tensile tester GUI with optimized settings
# for Raspberry Pi 4 with Waveshare 7" 1024x600 display.
#
# Installation:
#   1. chmod +x start_tensile_tester.sh
#   2. ./start_tensile_tester.sh
#
# Auto-start on boot:
#   Add to /etc/xdg/lxsession/LXDE-pi/autostart:
#   @/home/pi/tensile_tester/gui/start_tensile_tester.sh
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Performance optimizations
export PYTHONDONTWRITEBYTECODE=1       # Don't create .pyc files
export QT_QPA_PLATFORM=xcb             # Use X11 backend
export QT_ENABLE_ANIMATIONS=0          # Disable Qt animations
export QT_QUICK_BACKEND=software       # Use software rendering for Quick

# Reduce GPU memory pressure
export PYQTGRAPH_QT_LIB=PyQt5

# Pi-specific OpenGL settings
export QT_OPENGL=desktop               # Use desktop OpenGL (not ES)
export MESA_GL_VERSION_OVERRIDE=3.3    # Force GL 3.3 for pyqtgraph

# Memory optimization
export MALLOC_MMAP_THRESHOLD_=131072   # Optimize memory allocation

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import PyQt5, pyqtgraph, numpy, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Set CPU governor to performance (requires root)
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo "Setting CPU governor to performance..."
    echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1
fi

# Disable screen blanking
xset s off 2>/dev/null
xset -dpms 2>/dev/null
xset s noblank 2>/dev/null

echo "Starting Tensile Tester GUI..."
echo "Platform: Raspberry Pi"
echo "Display: Waveshare 7\" 1024x600"

# Run the application
python3 app.py

# Cleanup - restore CPU governor
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1
fi
