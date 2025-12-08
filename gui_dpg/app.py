#!/usr/bin/env python3
"""
Tensile Tester GUI - Dear PyGui Version (Professional)

Modern, GPU-accelerated GUI for tensile testing machine.
Optimized for Raspberry Pi 4 with real-time plotting.

Features:
- Comprehensive test configuration (ISO 527, ASTM D638)
- Real-time stress/strain calculations
- Multiple plot types
- Full mechanical properties analysis
- Export to CSV, Excel, JSON, PDF, XML

Author: DIY Tensile Tester Project
Version: 2.0.0
"""

import dearpygui.dearpygui as dpg
import sys
import os
import time
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from datetime import datetime
import numpy as np

# Add current directory first for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import professional modules
from models import TestConfiguration, MechanicalProperties, TestStage
from config_dialog import ConfigDialog
from results_window import ResultsWindow, TestData, ResultsAnalyzer
from export_system import DataExporter

# Configuration
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
PLOT_HISTORY = 5000  # Max points to display
UPDATE_RATE = 0.05   # 20 Hz update rate (50ms)

# Color scheme (dark theme)
COLORS = {
    'bg': (26, 26, 26),
    'panel': (45, 45, 45),
    'accent': (79, 195, 247),
    'success': (76, 175, 80),
    'warning': (255, 152, 0),
    'error': (244, 67, 54),
    'text': (255, 255, 255),
    'text_dim': (136, 136, 136),
    'header': (100, 181, 246),
}


@dataclass
class AppState:
    """Application state container."""
    # Connection
    connected: bool = False
    port: str = ""
    
    # Machine state
    state: str = "DISCONNECTED"
    force: float = 0.0
    position: float = 0.0
    is_running: bool = False
    test_stage: TestStage = TestStage.IDLE
    
    # Test data
    times: List[float] = field(default_factory=list)
    forces: List[float] = field(default_factory=list)
    extensions: List[float] = field(default_factory=list)
    stresses: List[float] = field(default_factory=list)
    strains: List[float] = field(default_factory=list)
    true_stresses: List[float] = field(default_factory=list)
    true_strains: List[float] = field(default_factory=list)
    
    # Calculated values
    max_force: float = 0.0
    max_stress: float = 0.0
    current_stress: float = 0.0
    current_strain: float = 0.0
    current_true_stress: float = 0.0
    current_true_strain: float = 0.0
    energy: float = 0.0
    rate: float = 0.0
    strain_rate: float = 0.0
    load_rate: float = 0.0
    
    # Test config
    speed: float = 1.0
    max_force_limit: float = 450.0
    max_extension: float = 100.0
    gauge_length: float = 50.0
    cross_section: float = 40.0  # mm² (4mm x 10mm)
    
    # Test timing
    test_start_time: float = 0.0
    data_points: int = 0


# Global state
state = AppState()
serial_handler = None
update_thread = None
running = True
config = TestConfiguration()
config_dialog: Optional[ConfigDialog] = None
results_window: Optional[ResultsWindow] = None
exporter: Optional[DataExporter] = None

# ============== Export Functions ==============

def set_status(message: str):
    """Update status bar."""
    try:
        dpg.set_value("status_text", message)
    except Exception:
        print(f"[Status] {message}")


def export_csv(sender=None, app_data=None, user_data=None):
    """Export to CSV."""
    print("[DEBUG] export_csv called")
    export_data("csv")


def export_excel(sender=None, app_data=None, user_data=None):
    """Export to Excel."""
    print("[DEBUG] export_excel called")
    export_data("excel")


def export_pdf(sender=None, app_data=None, user_data=None):
    """Export to PDF."""
    print("[DEBUG] export_pdf called")
    export_data("pdf")


def export_json(sender=None, app_data=None, user_data=None):
    """Export to JSON."""
    print("[DEBUG] export_json called")
    export_data("json")


def export_data(format_type: str = "csv"):
    """Export test data to specified format."""
    global exporter
    
    print(f"[DEBUG] export_data called with format: {format_type}")
    
    if not state.forces:
        set_status("No data to export!")
        print("[DEBUG] No data to export")
        return
    
    if exporter is None:
        exporter = DataExporter()
    
    # Calculate properties for export
    analyzer = ResultsAnalyzer()
    test_data = TestData(
        times=list(state.times),
        forces=list(state.forces),
        extensions=list(state.extensions),
        stresses=list(state.stresses),
        strains=list(state.strains),
        true_stresses=list(state.true_stresses),
        true_strains=list(state.true_strains)
    )
    properties = analyzer.analyze(test_data, config)
    
    # Debug output
    print(f"[DEBUG] Data points: {len(state.forces)}")
    print(f"[DEBUG] Max force: {max(state.forces) if state.forces else 0}")
    print(f"[DEBUG] Max stress: {max(state.stresses) if state.stresses else 0}")
    print(f"[DEBUG] Properties UTS: {properties.ultimate_tensile_strength}")
    print(f"[DEBUG] Properties Yield: {properties.yield_strength_offset}")
    print(f"[DEBUG] Properties Modulus: {properties.youngs_modulus}")
    
    try:
        if format_type == "csv":
            filename = exporter.export_csv(
                list(state.times), list(state.forces), list(state.extensions),
                list(state.stresses), list(state.strains), config, properties
            )
        elif format_type == "excel":
            filename = exporter.export_excel(
                list(state.times), list(state.forces), list(state.extensions),
                list(state.stresses), list(state.strains), config, properties
            )
        elif format_type == "json":
            filename = exporter.export_json(
                list(state.times), list(state.forces), list(state.extensions),
                list(state.stresses), list(state.strains), config, properties
            )
        elif format_type == "pdf":
            filename = exporter.export_pdf(
                list(state.times), list(state.forces), list(state.extensions),
                list(state.stresses), list(state.strains), config, properties
            )
        else:
            set_status(f"Unknown format: {format_type}")
            return
        
        set_status(f"Exported: {filename}")
        print(f"[DEBUG] Export successful: {filename}")
    except Exception as e:
        set_status(f"Export failed: {e}")
        print(f"[DEBUG] Export failed: {e}")
        import traceback
        traceback.print_exc()




def setup_theme():
    """Create custom dark theme."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Window/background
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COLORS['bg'])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['panel'])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, COLORS['panel'])
            
            # Frame/input backgrounds
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (60, 60, 60))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (70, 70, 70))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (80, 80, 80))
            
            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 70, 70))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (80, 80, 80))
            
            # Headers
            dpg.add_theme_color(dpg.mvThemeCol_Header, (60, 60, 60))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (70, 70, 70))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, COLORS['accent'])
            
            # Tabs
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (50, 50, 50))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (70, 70, 70))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, COLORS['accent'])
            
            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['text'])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, COLORS['text_dim'])
            
            # Plot
            dpg.add_theme_color(dpg.mvThemeCol_PlotLines, COLORS['accent'])
            
            # Styling
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)
            
    dpg.bind_theme(global_theme)
    
    # Button themes
    with dpg.theme(tag="theme_start"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (46, 125, 50))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (56, 142, 60))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (67, 160, 71))
            
    with dpg.theme(tag="theme_stop"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (198, 40, 40))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (211, 47, 47))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (229, 57, 53))
            
    with dpg.theme(tag="theme_emergency"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (183, 28, 28))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (198, 40, 40))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (211, 47, 47))


def create_control_panel():
    """Create the left control panel."""
    with dpg.child_window(width=300, tag="control_panel"):
        # Connection section
        dpg.add_text("Connection", color=COLORS['accent'])
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            dpg.add_combo(
                items=["MOCK_PICO"],
                default_value="MOCK_PICO",
                width=160,
                tag="port_combo"
            )
            dpg.add_button(label="Connect", callback=toggle_connection, tag="connect_btn")
            dpg.add_button(label="⟳", width=30, callback=refresh_ports)
        
        dpg.add_spacer(height=10)
        
        # Status section
        dpg.add_text("Status", color=COLORS['accent'])
        dpg.add_separator()
        
        with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
            dpg.add_table_column(width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column()
            dpg.add_table_column(width_fixed=True, init_width_or_weight=50)
            
            with dpg.table_row():
                dpg.add_text("State:")
                dpg.add_text("DISCONNECTED", tag="state_label", color=COLORS['text_dim'])
                dpg.add_text("")
                
            with dpg.table_row():
                dpg.add_text("Force:")
                dpg.add_text("0.00", tag="force_label", color=COLORS['accent'])
                dpg.add_text("N", color=COLORS['text_dim'])
                
            with dpg.table_row():
                dpg.add_text("Position:")
                dpg.add_text("0.000", tag="position_label", color=COLORS['accent'])
                dpg.add_text("mm", color=COLORS['text_dim'])
                
            with dpg.table_row():
                dpg.add_text("Stage:")
                dpg.add_text("Idle", tag="stage_display", color=COLORS['text_dim'])
                dpg.add_text("")
        
        dpg.add_spacer(height=10)
        
        # Test Parameters section
        dpg.add_text("Test Parameters", color=COLORS['accent'])
        dpg.add_separator()
        
        dpg.add_text("Speed (mm/min):", color=COLORS['text_dim'])
        dpg.add_input_float(
            default_value=1.0, min_value=0.1, max_value=500.0,
            step=0.5, width=-1, tag="speed_input",
            callback=on_speed_changed
        )
        
        dpg.add_text("Gauge Length (mm):", color=COLORS['text_dim'])
        dpg.add_input_float(
            default_value=50.0, min_value=1, max_value=200,
            step=5, width=-1, tag="gauge_length_input",
            callback=on_gauge_changed
        )
        
        dpg.add_text("Cross-Section (mm²):", color=COLORS['text_dim'])
        dpg.add_input_float(
            default_value=40.0, min_value=0.1, max_value=1000,
            step=1, width=-1, tag="cross_section_input",
            callback=on_cross_section_changed
        )
        
        dpg.add_spacer(height=5)
        dpg.add_button(label="⚙ Full Configuration...", width=-1, height=30, 
                      callback=show_config_dialog)
        
        dpg.add_spacer(height=10)
        
        # Control buttons
        dpg.add_text("Controls", color=COLORS['accent'])
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            btn = dpg.add_button(label="▶ START", width=135, height=40, callback=start_test, tag="start_btn")
            dpg.bind_item_theme(btn, "theme_start")
            btn = dpg.add_button(label="■ STOP", width=135, height=40, callback=stop_test, tag="stop_btn")
            dpg.bind_item_theme(btn, "theme_stop")
            
        with dpg.group(horizontal=True):
            dpg.add_button(label="⏸ PAUSE", width=135, height=40, callback=pause_test)
            dpg.add_button(label="▶ RESUME", width=135, height=40, callback=resume_test)
            
        with dpg.group(horizontal=True):
            dpg.add_button(label="🏠 HOME", width=135, height=40, callback=home)
            dpg.add_button(label="⚖ TARE", width=135, height=40, callback=tare)
        
        dpg.add_spacer(height=10)
        
        # Emergency stop
        btn = dpg.add_button(
            label="⚠ EMERGENCY STOP",
            width=-1, height=50,
            callback=emergency_stop,
            tag="emergency_btn"
        )
        dpg.bind_item_theme(btn, "theme_emergency")
        
        dpg.add_spacer(height=10)
        
        # Results & Export
        dpg.add_text("Results & Export", color=COLORS['accent'])
        dpg.add_separator()
        dpg.add_button(label="📈 Analyze Results", width=-1, height=35, callback=show_results)
        with dpg.group(horizontal=True):
            dpg.add_button(label="� CSV", width=65, height=30, callback=export_csv)
            dpg.add_button(label="📊 Excel", width=65, height=30, callback=export_excel)
            dpg.add_button(label="� PDF", width=65, height=30, callback=export_pdf)
            dpg.add_button(label="{ } JSON", width=65, height=30, callback=export_json)


def create_plot_panel():
    """Create the main plot panel."""
    with dpg.child_window(tag="plot_panel"):
        # Plot type selector row
        with dpg.group(horizontal=True):
            dpg.add_text("Plot:", color=COLORS['text_dim'])
            dpg.add_combo(
                items=[
                    "Force vs Extension",
                    "Stress vs Strain",
                    "Force vs Time",
                    "Stress vs Time",
                    "Extension vs Time",
                    "True Stress vs True Strain"
                ],
                default_value="Force vs Extension",
                width=180,
                tag="plot_type_combo",
                callback=on_plot_type_changed
            )
            dpg.add_spacer(width=15)
            dpg.add_text("Time:", color=COLORS['text_dim'])
            dpg.add_text("00:00.0", tag="time_label", color=COLORS['accent'])
            dpg.add_spacer(width=15)
            dpg.add_text("Points:", color=COLORS['text_dim'])
            dpg.add_text("0", tag="points_label", color=COLORS['accent'])
            dpg.add_spacer(width=15)
            dpg.add_text("Stage:", color=COLORS['text_dim'])
            dpg.add_text("Idle", tag="stage_label", color=COLORS['warning'])
        
        dpg.add_spacer(height=5)
        
        # Main plot
        with dpg.plot(label="", height=-160, width=-1, tag="main_plot", 
                      anti_aliased=True):
            dpg.add_plot_legend()
            
            # X axis
            dpg.add_plot_axis(dpg.mvXAxis, label="Extension (mm)", tag="x_axis")
            
            # Y axis with line series
            with dpg.plot_axis(dpg.mvYAxis, label="Force (N)", tag="y_axis"):
                dpg.add_line_series([], [], label="Data", tag="plot_series")
                dpg.add_scatter_series([], [], label="Max", tag="max_marker")
                dpg.add_scatter_series([], [], label="Yield", tag="yield_marker")
        
        dpg.add_spacer(height=8)
        
        # Live values - Primary row
        with dpg.group(horizontal=True):
            create_value_display("Force", "0.00", "N", "live_force", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Stress", "0.00", "MPa", "live_stress", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Extension", "0.000", "mm", "live_ext", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Strain", "0.000", "%", "live_strain", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Rate", "0.00", "mm/s", "live_rate", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Energy", "0.000", "J", "live_energy", width=90)
        
        dpg.add_spacer(height=5)
        
        # Live values - Secondary row (results)
        with dpg.group(horizontal=True):
            create_value_display("Max Force", "0.00", "N", "max_force_display", width=90)
            dpg.add_spacer(width=10)
            create_value_display("UTS", "0.00", "MPa", "uts_display", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Max Ext", "0.000", "mm", "max_ext_display", width=90)
            dpg.add_spacer(width=10)
            create_value_display("True σ", "0.00", "MPa", "live_true_stress", width=90)
            dpg.add_spacer(width=10)
            create_value_display("True ε", "0.000", "", "live_true_strain", width=90)
            dpg.add_spacer(width=10)
            create_value_display("Load Rate", "0.0", "N/s", "live_load_rate", width=90)


def create_value_display(title: str, value: str, unit: str, tag_prefix: str, width: int = 100):
    """Create a value display widget."""
    with dpg.group():
        dpg.add_text(title, color=COLORS['text_dim'])
        with dpg.group(horizontal=True):
            dpg.add_text(value, tag=f"{tag_prefix}_value", color=COLORS['accent'])
            if unit:
                dpg.add_text(unit, color=COLORS['text_dim'])


def create_status_bar():
    """Create bottom status bar."""
    with dpg.child_window(height=25, no_scrollbar=True, tag="status_bar"):
        dpg.add_text("Ready - Connect to start", tag="status_text", color=COLORS['text_dim'])


# ============== Callbacks ==============

def refresh_ports():
    """Refresh available serial ports."""
    if serial_handler:
        ports = serial_handler.list_ports()
        if not ports:
            ports = ["MOCK_PICO"]
        dpg.configure_item("port_combo", items=ports)


def toggle_connection():
    """Toggle serial connection."""
    global serial_handler
    
    if state.connected:
        # Disconnect
        if serial_handler:
            serial_handler.disconnect()
        state.connected = False
        state.state = "DISCONNECTED"
        dpg.set_value("connect_btn", "Connect")
        dpg.set_value("state_label", "DISCONNECTED")
        dpg.configure_item("state_label", color=COLORS['text_dim'])
        set_status("Disconnected")
    else:
        # Connect
        port = dpg.get_value("port_combo")
        if serial_handler:
            if serial_handler.connect(port):
                state.connected = True
                state.port = port
                dpg.set_value("connect_btn", "Disconnect")
                dpg.set_value("state_label", "CONNECTED")
                dpg.configure_item("state_label", color=COLORS['success'])
                set_status(f"Connected to {port}")
                
                # Request initial status
                serial_handler.identify()
                serial_handler.get_status()
            else:
                set_status("Connection failed!")


def on_speed_changed(sender, app_data):
    """Handle speed change."""
    state.speed = app_data
    config.control.test_speed = app_data
    if serial_handler and state.connected:
        serial_handler.set_speed(app_data / 60.0)  # Convert mm/min to mm/s


def on_gauge_changed(sender, app_data):
    """Handle gauge length change."""
    state.gauge_length = app_data
    config.specimen.gauge_length = app_data


def on_cross_section_changed(sender, app_data):
    """Handle cross-section area change."""
    state.cross_section = app_data
    config.specimen.cross_section_area = app_data


def show_config_dialog():
    """Show the full configuration dialog."""
    global config_dialog
    if config_dialog is None:
        config_dialog = ConfigDialog()
        config_dialog.on_config_applied = on_config_applied
    config_dialog.config = config
    config_dialog.show()


def on_config_applied(new_config: TestConfiguration):
    """Handle configuration applied from dialog."""
    global config
    config = new_config
    
    # Update UI with new config values
    state.gauge_length = config.specimen.gauge_length
    state.cross_section = config.specimen.cross_section_area
    state.speed = config.control.test_speed
    state.max_force_limit = config.termination.max_force
    state.max_extension = config.termination.max_extension
    
    # Update UI inputs
    dpg.set_value("speed_input", config.control.test_speed)
    dpg.set_value("gauge_length_input", config.specimen.gauge_length)
    dpg.set_value("cross_section_input", config.specimen.cross_section_area)
    
    set_status("Configuration applied")


def on_plot_type_changed(sender, app_data):
    """Handle plot type change."""
    plot_type = app_data
    
    # Update axis labels
    if plot_type == "Force vs Extension":
        dpg.set_item_label("x_axis", "Extension (mm)")
        dpg.set_item_label("y_axis", "Force (N)")
    elif plot_type == "Stress vs Strain":
        dpg.set_item_label("x_axis", "Strain (%)")
        dpg.set_item_label("y_axis", "Stress (MPa)")
    elif plot_type == "Force vs Time":
        dpg.set_item_label("x_axis", "Time (s)")
        dpg.set_item_label("y_axis", "Force (N)")
    elif plot_type == "Stress vs Time":
        dpg.set_item_label("x_axis", "Time (s)")
        dpg.set_item_label("y_axis", "Stress (MPa)")
    elif plot_type == "Extension vs Time":
        dpg.set_item_label("x_axis", "Time (s)")
        dpg.set_item_label("y_axis", "Extension (mm)")
    elif plot_type == "True Stress vs True Strain":
        dpg.set_item_label("x_axis", "True Strain")
        dpg.set_item_label("y_axis", "True Stress (MPa)")
    
    update_plot()


def start_test():
    """Start tensile test."""
    if not state.connected:
        set_status("Not connected!")
        return
    
    # Get speed from UI and set it
    speed = dpg.get_value("speed_input")
    if serial_handler:
        serial_handler.set_speed(speed)
    
    # Clear data
    state.times.clear()
    state.forces.clear()
    state.extensions.clear()
    state.stresses.clear()
    state.strains.clear()
    state.true_stresses.clear()
    state.true_strains.clear()
    state.max_force = 0.0
    state.max_stress = 0.0
    state.energy = 0.0
    state.data_points = 0
    state.test_start_time = time.time()
    state.test_stage = TestStage.TESTING
    
    # Clear plot
    dpg.set_value("plot_series", [[], []])
    dpg.set_value("max_marker", [[], []])
    dpg.set_value("yield_marker", [[], []])
    
    if serial_handler:
        serial_handler.start_test()
    
    set_status(f"Test started at {speed} mm/s")


def stop_test():
    """Stop tensile test."""
    if serial_handler:
        serial_handler.stop_test()
    set_status("Test stopped")


def pause_test():
    """Pause tensile test."""
    if serial_handler:
        serial_handler.pause_test()
    set_status("Test paused")


def resume_test():
    """Resume tensile test."""
    if serial_handler:
        serial_handler.resume_test()
    set_status("Test resumed")


def home():
    """Home the machine."""
    if serial_handler:
        serial_handler.home()
    state.test_stage = TestStage.RETURN
    set_status("Homing...")


def tare():
    """Tare the load cell."""
    if serial_handler:
        serial_handler.tare()
    set_status("Taring...")


def emergency_stop():
    """Emergency stop."""
    if serial_handler:
        serial_handler.emergency_stop()
    state.test_stage = TestStage.EMERGENCY
    set_status("EMERGENCY STOP!")




def show_results():
    """Show results dialog."""
    global results_window
    
    if not state.forces:
        set_status("No data to analyze!")
        return
    
    if results_window is None:
        results_window = ResultsWindow()
        results_window.on_export = on_results_export
    
    # Create test data container with COPIES of the data
    test_data = TestData(
        times=list(state.times),
        forces=list(state.forces),
        extensions=list(state.extensions),
        stresses=list(state.stresses),
        strains=list(state.strains),
        true_stresses=list(state.true_stresses),
        true_strains=list(state.true_strains)
    )
    
    print(f"[show_results] Passing {len(test_data.forces)} data points to ResultsWindow")
    
    results_window.show(test_data, config)


def on_results_export(format_type: str, properties, test_data, cfg):
    """Handle export from results window."""
    export_data(format_type)


def update_plot():
    """Update plot with current data."""
    if not state.forces or len(state.forces) < 2:
        return
    
    plot_type = dpg.get_value("plot_type_combo")
    
    # Select data based on plot type
    if plot_type == "Force vs Extension":
        x_data = list(state.extensions)
        y_data = list(state.forces)
    elif plot_type == "Stress vs Strain":
        x_data = [s * 100 for s in state.strains]  # Convert to %
        y_data = list(state.stresses)
    elif plot_type == "Force vs Time":
        x_data = list(state.times)
        y_data = list(state.forces)
    elif plot_type == "Stress vs Time":
        x_data = list(state.times)
        y_data = list(state.stresses)
    elif plot_type == "Extension vs Time":
        x_data = list(state.times)
        y_data = list(state.extensions)
    elif plot_type == "True Stress vs True Strain":
        if state.true_strains and state.true_stresses:
            x_data = list(state.true_strains)
            y_data = list(state.true_stresses)
        else:
            return
    else:
        return
    
    # Downsample for performance if needed
    if len(x_data) > PLOT_HISTORY:
        step = len(x_data) // PLOT_HISTORY
        x_data = x_data[::step]
        y_data = y_data[::step]
    
    # Update series
    dpg.set_value("plot_series", [x_data, y_data])
    
    # Update max marker
    if state.forces:
        max_idx = state.forces.index(max(state.forces))
        if max_idx < len(state.extensions) and max_idx < len(state.stresses):
            if plot_type == "Force vs Extension":
                dpg.set_value("max_marker", [[state.extensions[max_idx]], [state.forces[max_idx]]])
            elif plot_type == "Stress vs Strain":
                dpg.set_value("max_marker", [[state.strains[max_idx] * 100], [state.stresses[max_idx]]])
            elif plot_type == "Force vs Time":
                dpg.set_value("max_marker", [[state.times[max_idx]], [state.forces[max_idx]]])
            elif plot_type == "True Stress vs True Strain" and state.true_stresses:
                dpg.set_value("max_marker", [[state.true_strains[max_idx]], [state.true_stresses[max_idx]]])
    
    # Auto-fit axes
    dpg.fit_axis_data("x_axis")
    dpg.fit_axis_data("y_axis")


def update_displays():
    """Update all display values."""
    # Force and position
    dpg.set_value("force_label", f"{state.force:.2f}")
    dpg.set_value("position_label", f"{state.position:.3f}")
    
    # State with color
    state_colors = {
        "IDLE": COLORS['success'],
        "RUNNING": COLORS['accent'],
        "PAUSED": COLORS['warning'],
        "ERROR": COLORS['error'],
        "HOMING": COLORS['warning'],
        "DISCONNECTED": COLORS['text_dim'],
    }
    dpg.set_value("state_label", state.state)
    dpg.configure_item("state_label", color=state_colors.get(state.state, COLORS['text']))
    
    # Live values - Primary row
    dpg.set_value("live_force_value", f"{state.force:.2f}")
    dpg.set_value("live_stress_value", f"{state.current_stress:.2f}")
    current_ext = state.extensions[-1] if state.extensions else 0
    dpg.set_value("live_ext_value", f"{current_ext:.3f}")
    dpg.set_value("live_strain_value", f"{state.current_strain:.3f}")
    dpg.set_value("live_rate_value", f"{state.rate:.2f}")
    dpg.set_value("live_energy_value", f"{state.energy:.4f}")
    
    # Live values - Secondary row
    dpg.set_value("max_force_display_value", f"{state.max_force:.2f}")
    dpg.set_value("uts_display_value", f"{state.max_stress:.2f}")
    max_ext = max(state.extensions) if state.extensions else 0
    dpg.set_value("max_ext_display_value", f"{max_ext:.3f}")
    dpg.set_value("live_true_stress_value", f"{state.current_true_stress:.2f}")
    dpg.set_value("live_true_strain_value", f"{state.current_true_strain:.4f}")
    dpg.set_value("live_load_rate_value", f"{state.load_rate:.1f}")
    
    # Time
    if state.is_running and state.test_start_time > 0:
        elapsed = time.time() - state.test_start_time
        mins = int(elapsed // 60)
        secs = elapsed % 60
        dpg.set_value("time_label", f"{mins:02d}:{secs:04.1f}")
    
    # Points
    dpg.set_value("points_label", f"{state.data_points}")
    
    # Stage display
    stage_colors = {
        TestStage.IDLE: COLORS['text_dim'],
        TestStage.PRELOAD: COLORS['warning'],
        TestStage.TESTING: COLORS['accent'],
        TestStage.HOLD: COLORS['warning'],
        TestStage.COMPLETE: COLORS['success'],
        TestStage.ERROR: COLORS['error'],
        TestStage.EMERGENCY: COLORS['error'],
    }
    
    # Auto-detect test stage
    if state.is_running and state.forces:
        if state.data_points < 10:
            state.test_stage = TestStage.PRELOAD
        elif state.force >= state.max_force * 0.95:
            state.test_stage = TestStage.TESTING
        elif state.force < state.max_force * 0.5 and state.data_points > 20:
            state.test_stage = TestStage.COMPLETE
        else:
            state.test_stage = TestStage.TESTING
    
    dpg.set_value("stage_label", state.test_stage.value)
    dpg.configure_item("stage_label", color=stage_colors.get(state.test_stage, COLORS['text']))
    dpg.set_value("stage_display", state.test_stage.value)
    dpg.configure_item("stage_display", color=stage_colors.get(state.test_stage, COLORS['text']))


# ============== Serial Callbacks ==============

def on_connected():
    """Serial connected callback."""
    state.connected = True
    state.test_stage = TestStage.IDLE
    dpg.set_value("connect_btn", "Disconnect")
    set_status("Connected")


def on_disconnected():
    """Serial disconnected callback."""
    state.connected = False
    state.state = "DISCONNECTED"
    state.test_stage = TestStage.IDLE
    dpg.set_value("connect_btn", "Connect")
    set_status("Disconnected")


def on_status(status):
    """Status update callback."""
    state.state = status.state
    state.force = status.force
    state.position = status.position
    state.is_running = status.is_running


def on_data(data):
    """Data point callback."""
    # Store data
    state.times.append(data.timestamp / 1000.0)  # Convert to seconds
    state.forces.append(data.force)
    state.extensions.append(data.extension)
    state.stresses.append(data.stress)
    state.strains.append(data.strain)
    state.data_points = len(state.forces)
    
    # Update current values
    state.force = data.force
    state.current_stress = data.stress
    state.current_strain = data.strain * 100
    
    # Calculate true stress and true strain
    # True strain: ε_true = ln(1 + ε_eng)
    # True stress: σ_true = σ_eng * (1 + ε_eng)
    eng_strain = data.strain  # Already ratio
    if eng_strain > -0.99:  # Avoid log of zero/negative
        true_strain = np.log(1 + eng_strain)
        true_stress = data.stress * (1 + eng_strain)
        state.true_strains.append(true_strain)
        state.true_stresses.append(true_stress)
        state.current_true_stress = true_stress
        state.current_true_strain = true_strain
    
    # Max values
    if data.force > state.max_force:
        state.max_force = data.force
    if data.stress > state.max_stress:
        state.max_stress = data.stress
    
    # Rate calculations
    if len(state.times) >= 2:
        dt = state.times[-1] - state.times[-2]
        if dt > 0:
            # Extension rate (mm/s)
            state.rate = abs(state.extensions[-1] - state.extensions[-2]) / dt
            # Load rate (N/s)
            state.load_rate = abs(state.forces[-1] - state.forces[-2]) / dt
            # Strain rate (1/s)
            state.strain_rate = abs(state.strains[-1] - state.strains[-2]) / dt
    
    # Energy calculation (trapezoidal)
    if len(state.forces) >= 2:
        avg_force = (state.forces[-1] + state.forces[-2]) / 2
        d_ext = abs(state.extensions[-1] - state.extensions[-2]) / 1000.0  # to meters
        state.energy += avg_force * d_ext

def on_force(force):
    """Force reading callback."""
    state.force = force


def on_position(position):
    """Position reading callback."""
    state.position = position


def on_response(response):
    """Response callback."""
    set_status(response)


def on_error(error):
    """Error callback."""
    set_status(f"Error: {error}")


# ============== Main Loop ==============

def frame_update():
    """Called every frame to update UI (runs in main thread)."""
    try:
        # Update displays
        update_displays()
        
        # Update plot continuously when test is running
        if state.is_running or state.data_points > 0:
            update_plot()
    except Exception as e:
        print(f"Update error: {e}")


def main():
    """Main entry point."""
    global serial_handler, running, config_dialog, results_window, exporter
    
    print("=" * 60)
    print("  TENSILE TESTER GUI - Dear PyGui Professional v2.0")
    print("  Features: ISO 527, ASTM D638 Support")
    print("=" * 60)
    
    # Check for test mode
    test_mode = "--test" in sys.argv or "-t" in sys.argv
    
    if test_mode:
        print("\n[TEST MODE] Using mock serial...")
        from mock_serial import MockSerialHandler
        serial_handler = MockSerialHandler()
    else:
        from serial_handler_dpg import SerialHandler
        serial_handler = SerialHandler()
    
    # Setup callbacks
    serial_handler.on_connected = on_connected
    serial_handler.on_disconnected = on_disconnected
    serial_handler.on_status = on_status
    serial_handler.on_data = on_data
    serial_handler.on_force = on_force
    serial_handler.on_position = on_position
    serial_handler.on_response = on_response
    serial_handler.on_error = on_error
    
    # Initialize config dialog and export system
    config_dialog = ConfigDialog()
    config_dialog.on_config_applied = on_config_applied
    results_window = ResultsWindow()
    results_window.on_export = on_results_export
    exporter = DataExporter()
    
    # Create DearPyGui context
    dpg.create_context()
    
    # Setup theme
    setup_theme()
    
    # Create viewport
    dpg.create_viewport(
        title="Tensile Tester - Professional",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=True,
        vsync=True
    )
    
    # Create main window
    with dpg.window(tag="main_window"):
        with dpg.group(horizontal=True):
            create_control_panel()
            create_plot_panel()
        
        create_status_bar()
    
    # Set primary window
    dpg.set_primary_window("main_window", True)
    
    # Refresh ports
    refresh_ports()
    
    # Setup and show
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    print("\nGUI started!")
    if test_mode:
        print("Select 'MOCK_PICO' and click Connect to start testing.")
    print("\nFeatures:")
    print("  - Full Configuration: Click '⚙ Full Configuration...'")
    print("  - Multiple Plot Types: Force/Stress vs Extension/Strain/Time")
    print("  - Real-time True Stress/Strain calculations")
    print("  - Export: CSV, Excel, JSON, PDF")
    print("  - Comprehensive Results Analysis\n")
    
    # Main loop with frame updates
    frame_count = 0
    while dpg.is_dearpygui_running():
        # Update UI every few frames (throttled for performance)
        frame_count += 1
        if frame_count % 3 == 0:  # ~20 Hz update rate at 60 FPS
            frame_update()
        
        dpg.render_dearpygui_frame()
    
    # Cleanup
    running = False
    if serial_handler:
        serial_handler.disconnect()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
