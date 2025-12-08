#!/usr/bin/env python3
"""
Main Window for Tensile Tester GUI

Optimized for Waveshare 7" display (1024x600).
Enhanced with real-time calculations and multiple plot views.
Raspberry Pi performance optimizations.
"""

import os
import time
from datetime import datetime
from typing import List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QComboBox, QDoubleSpinBox,
    QStatusBar, QMessageBox, QFileDialog, QTabWidget, QFrame,
    QSplitter, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

import pyqtgraph as pg
import numpy as np
import pandas as pd

from serial_handler import SerialHandler, DataPoint, Status
from config_model import TestConfiguration, ControlMode, TestResults
from config_dialog import ConfigDialog
from results_analyzer import ResultsAnalyzer, MechanicalProperties
from report_generator import ReportGenerator
from results_dialog_fast import show_fast_results

# Import Pi configuration
from pi_config import (
    STATUS_POLL_RATE_MS, PLOT_UPDATE_RATE_MS, PLOT_MAX_POINTS,
    PLOT_DOWNSAMPLE, USE_OPENGL, ANTIALIAS, DATA_BUFFER_SIZE,
    IS_RASPBERRY_PI, COLORS
)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Tensile Tester")
        self.setMinimumSize(1024, 600)
        
        # Serial handler
        self.serial = SerialHandler(self)
        self._setup_serial_connections()
        
        # Test configuration
        self.config = TestConfiguration()
        
        # Results analyzer
        self.analyzer = ResultsAnalyzer(
            self.config.specimen.gauge_length,
            self.config.specimen.cross_section_area
        )
        
        # Test data storage
        self.test_data: List[DataPoint] = []
        self.is_test_running = False
        self.current_state = "DISCONNECTED"
        self.test_start_time = 0
        
        # Live calculation tracking
        self.cumulative_energy = 0.0
        self.last_data_time = 0
        self.test_results = None
        
        # Create UI
        self._create_ui()
        
        # Status update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._request_status)
        
        # Auto-connect on startup
        QTimer.singleShot(1000, self._auto_connect)
    
    def _setup_serial_connections(self):
        """Connect serial handler signals."""
        self.serial.connected.connect(self._on_connected)
        self.serial.disconnected.connect(self._on_disconnected)
        self.serial.status_received.connect(self._on_status)
        self.serial.data_received.connect(self._on_data)
        self.serial.force_received.connect(self._on_force)
        self.serial.position_received.connect(self._on_position)
        self.serial.response_received.connect(self._on_response)
        self.serial.error_occurred.connect(self._on_error)
    
    def _create_ui(self):
        """Create the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout - horizontal split
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel - Controls (300px width)
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        conn_layout.addWidget(self.port_combo)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(self.refresh_btn)
        
        left_layout.addWidget(conn_group)
        
        # Test Configuration button - prominent
        self.config_btn = QPushButton("⚙ TEST CONFIGURATION")
        self.config_btn.setMinimumHeight(45)
        self.config_btn.setStyleSheet("font-weight: bold;")
        self.config_btn.clicked.connect(self._open_config_dialog)
        left_layout.addWidget(self.config_btn)
        
        # Active config display
        config_info = QGroupBox("Active Test")
        config_info_layout = QGridLayout(config_info)
        config_info_layout.setSpacing(4)
        
        config_info_layout.addWidget(QLabel("Sample:"), 0, 0)
        self.sample_id_label = QLabel("-")
        self.sample_id_label.setStyleSheet("color: #4fc3f7;")
        config_info_layout.addWidget(self.sample_id_label, 0, 1)
        
        config_info_layout.addWidget(QLabel("Standard:"), 1, 0)
        self.standard_label = QLabel("-")
        self.standard_label.setStyleSheet("color: #888;")
        config_info_layout.addWidget(self.standard_label, 1, 1)
        
        config_info_layout.addWidget(QLabel("Area:"), 2, 0)
        self.area_label = QLabel("-")
        self.area_label.setStyleSheet("color: #888;")
        config_info_layout.addWidget(self.area_label, 2, 1)
        
        left_layout.addWidget(config_info)
        
        # Values display
        values_group = QGroupBox("Current Values")
        values_layout = QGridLayout(values_group)
        
        # Force display
        values_layout.addWidget(QLabel("Force:"), 0, 0)
        self.force_label = QLabel("0.00")
        self.force_label.setObjectName("valueLabel")
        self.force_label.setAlignment(Qt.AlignRight)
        values_layout.addWidget(self.force_label, 0, 1)
        unit_label = QLabel("N")
        unit_label.setObjectName("unitLabel")
        values_layout.addWidget(unit_label, 0, 2)
        
        # Position display
        values_layout.addWidget(QLabel("Position:"), 1, 0)
        self.position_label = QLabel("0.000")
        self.position_label.setObjectName("valueLabel")
        self.position_label.setAlignment(Qt.AlignRight)
        values_layout.addWidget(self.position_label, 1, 1)
        unit_label = QLabel("mm")
        unit_label.setObjectName("unitLabel")
        values_layout.addWidget(unit_label, 1, 2)
        
        # State display
        values_layout.addWidget(QLabel("State:"), 2, 0)
        self.state_label = QLabel("DISCONNECTED")
        self.state_label.setStyleSheet("color: #888888;")
        values_layout.addWidget(self.state_label, 2, 1, 1, 2)
        
        left_layout.addWidget(values_group)
        
        # Test parameters
        params_group = QGroupBox("Test Parameters")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Speed (mm/s):"), 0, 0)
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 50.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.valueChanged.connect(self._on_speed_changed)
        params_layout.addWidget(self.speed_spin, 0, 1)
        
        params_layout.addWidget(QLabel("Max Force (N):"), 1, 0)
        self.max_force_spin = QDoubleSpinBox()
        self.max_force_spin.setRange(1, 500)
        self.max_force_spin.setValue(450)
        self.max_force_spin.setSingleStep(10)
        self.max_force_spin.valueChanged.connect(self._on_max_force_changed)
        params_layout.addWidget(self.max_force_spin, 1, 1)
        
        params_layout.addWidget(QLabel("Max Extension (mm):"), 2, 0)
        self.max_ext_spin = QDoubleSpinBox()
        self.max_ext_spin.setRange(1, 150)
        self.max_ext_spin.setValue(100)
        self.max_ext_spin.setSingleStep(5)
        self.max_ext_spin.valueChanged.connect(self._on_max_ext_changed)
        params_layout.addWidget(self.max_ext_spin, 2, 1)
        
        left_layout.addWidget(params_group)
        
        # Control buttons
        control_group = QGroupBox("Controls")
        control_layout = QGridLayout(control_group)
        
        # Test control buttons
        self.start_btn = QPushButton("▶ START")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self._start_test)
        control_layout.addWidget(self.start_btn, 0, 0)
        
        self.stop_btn = QPushButton("■ STOP")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self._stop_test)
        control_layout.addWidget(self.stop_btn, 0, 1)
        
        self.pause_btn = QPushButton("⏸ PAUSE")
        self.pause_btn.clicked.connect(self._pause_test)
        control_layout.addWidget(self.pause_btn, 1, 0)
        
        self.resume_btn = QPushButton("▶ RESUME")
        self.resume_btn.clicked.connect(self._resume_test)
        control_layout.addWidget(self.resume_btn, 1, 1)
        
        # Jog buttons
        self.jog_up_btn = QPushButton("▲ JOG UP")
        self.jog_up_btn.pressed.connect(lambda: self.serial.jog_up())
        self.jog_up_btn.released.connect(lambda: self.serial.stop_jog())
        control_layout.addWidget(self.jog_up_btn, 2, 0)
        
        self.jog_down_btn = QPushButton("▼ JOG DOWN")
        self.jog_down_btn.pressed.connect(lambda: self.serial.jog_down())
        self.jog_down_btn.released.connect(lambda: self.serial.stop_jog())
        control_layout.addWidget(self.jog_down_btn, 2, 1)
        
        # Utility buttons
        self.home_btn = QPushButton("🏠 HOME")
        self.home_btn.clicked.connect(self._home)
        control_layout.addWidget(self.home_btn, 3, 0)
        
        self.tare_btn = QPushButton("⚖ TARE")
        self.tare_btn.clicked.connect(self._tare)
        control_layout.addWidget(self.tare_btn, 3, 1)
        
        left_layout.addWidget(control_group)
        
        # Emergency stop - large button
        self.emergency_btn = QPushButton("⚠ EMERGENCY STOP")
        self.emergency_btn.setObjectName("emergencyButton")
        self.emergency_btn.setMinimumHeight(60)
        self.emergency_btn.clicked.connect(self._emergency_stop)
        left_layout.addWidget(self.emergency_btn)
        
        # Export button
        self.export_btn = QPushButton("📊 Export Data")
        self.export_btn.clicked.connect(self._export_data)
        left_layout.addWidget(self.export_btn)
        
        # Spacer
        left_layout.addStretch()
        
        main_layout.addWidget(left_panel)
        
        # Right panel - Graph and live data
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # Plot controls row
        plot_controls = QWidget()
        plot_controls_layout = QHBoxLayout(plot_controls)
        plot_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        plot_controls_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "Force vs Extension",
            "Stress vs Strain", 
            "Force vs Time",
            "Stress vs Time",
            "Extension vs Time"
        ])
        self.plot_type_combo.currentIndexChanged.connect(self._update_plot_type)
        plot_controls_layout.addWidget(self.plot_type_combo)
        
        plot_controls_layout.addStretch()
        
        # Test stage indicator
        self.test_stage_label = QLabel("Stage: -")
        self.test_stage_label.setStyleSheet("color: #888; font-weight: bold;")
        plot_controls_layout.addWidget(self.test_stage_label)
        
        # Test time display
        self.test_time_label = QLabel("Time: 00:00.0")
        self.test_time_label.setStyleSheet("color: #4fc3f7; font-weight: bold;")
        plot_controls_layout.addWidget(self.test_time_label)
        
        right_layout.addWidget(plot_controls)
        
        # Create plot widget
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1a1a1a')
        self.plot_widget.setTitle("Force vs Extension", color='w', size='14pt')
        self.plot_widget.setLabel('left', 'Force', units='N', color='w')
        self.plot_widget.setLabel('bottom', 'Extension', units='mm', color='w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Create plot curve
        self.plot_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#4fc3f7', width=2)
        )
        
        # Add markers for key points
        self.max_force_marker = self.plot_widget.plot(
            [], [], pen=None, symbol='o', symbolBrush='#f44336', symbolSize=10
        )
        self.yield_point_marker = self.plot_widget.plot(
            [], [], pen=None, symbol='s', symbolBrush='#ff9800', symbolSize=10
        )
        
        right_layout.addWidget(self.plot_widget)
        
        # Live calculated values - primary row
        live_values_frame = QFrame()
        live_values_frame.setFrameShape(QFrame.StyledPanel)
        live_values_frame.setMaximumHeight(70)
        live_values_layout = QHBoxLayout(live_values_frame)
        live_values_layout.setSpacing(15)
        
        self.live_stress = self._create_result_label("Stress", "0.00", "MPa")
        live_values_layout.addWidget(self.live_stress)
        
        self.live_strain = self._create_result_label("Strain", "0.000", "%")
        live_values_layout.addWidget(self.live_strain)
        
        self.live_rate = self._create_result_label("Rate", "0.00", "mm/s")
        live_values_layout.addWidget(self.live_rate)
        
        self.live_energy = self._create_result_label("Energy", "0.000", "J")
        live_values_layout.addWidget(self.live_energy)
        
        right_layout.addWidget(live_values_frame)
        
        # Results display - secondary row
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.StyledPanel)
        results_frame.setMaximumHeight(70)
        results_layout = QHBoxLayout(results_frame)
        results_layout.setSpacing(15)
        
        self.max_force_result = self._create_result_label("Max Force", "0.00", "N")
        results_layout.addWidget(self.max_force_result)
        
        self.max_stress_result = self._create_result_label("UTS", "0.00", "MPa")
        results_layout.addWidget(self.max_stress_result)
        
        self.max_ext_result = self._create_result_label("Max Ext.", "0.000", "mm")
        results_layout.addWidget(self.max_ext_result)
        
        self.data_points_result = self._create_result_label("Points", "0", "")
        results_layout.addWidget(self.data_points_result)
        
        right_layout.addWidget(results_frame)
        
        # Results button row
        results_btn_row = QWidget()
        results_btn_layout = QHBoxLayout(results_btn_row)
        results_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view_results_btn = QPushButton("📊 View Full Results && Analysis")
        self.view_results_btn.setMinimumHeight(35)
        self.view_results_btn.setEnabled(False)
        self.view_results_btn.clicked.connect(self._show_results_dialog)
        results_btn_layout.addWidget(self.view_results_btn)
        
        right_layout.addWidget(results_btn_row)
        
        main_layout.addWidget(right_panel, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Connect to start")
        
        # Refresh ports
        self._refresh_ports()
        
        # Update button states
        self._update_button_states()
    
    def _create_result_label(self, title: str, value: str, unit: str) -> QWidget:
        """Create a result display widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_widget = QWidget()
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_label.setStyleSheet("color: #4fc3f7; font-size: 20px; font-weight: bold;")
        value_layout.addWidget(value_label)
        
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #888888; font-size: 12px;")
            value_layout.addWidget(unit_label)
        
        layout.addWidget(value_widget)
        
        # Store reference to value label
        widget.value_label = value_label
        
        return widget
    
    def _open_config_dialog(self):
        """Open test configuration dialog."""
        dialog = ConfigDialog(self.config, self)
        if dialog.exec_():
            self.config = dialog.get_config()
            self._update_config_display()
            self._apply_config_to_machine()
    
    def _update_config_display(self):
        """Update the active config display labels."""
        c = self.config
        
        # Sample ID
        sample = c.metadata.sample_id if c.metadata.sample_id else "-"
        self.sample_id_label.setText(sample)
        
        # Standard
        std_name = c.metadata.test_standard.value.split(" - ")[0] if c.metadata.test_standard else "-"
        self.standard_label.setText(std_name)
        
        # Cross-section area
        area = c.specimen.cross_section_area
        self.area_label.setText(f"{area:.2f} mm²")
        
        # Update parameter spinboxes from config
        self.speed_spin.setValue(c.control.test_speed / 60.0)  # Convert mm/min to mm/s
        self.max_force_spin.setValue(c.termination.max_force)
        self.max_ext_spin.setValue(c.termination.max_extension)
    
    def _apply_config_to_machine(self):
        """Send configuration to the machine."""
        if not self.serial.is_connected():
            return
        
        c = self.config
        
        # Send speed (convert mm/min to mm/s for the spinbox display)
        self.serial.set_speed(c.control.test_speed / 60.0)
        
        # Send limits
        self.serial.set_max_force(c.termination.max_force)
        self.serial.set_max_extension(c.termination.max_extension)
        
        # Update analyzer with new config
        self.analyzer = ResultsAnalyzer(
            c.specimen.gauge_length,
            c.specimen.cross_section_area
        )
    
    def _update_plot_type(self, index: int):
        """Update plot type and refresh data display."""
        plot_types = [
            ("Force vs Extension", "Force", "N", "Extension", "mm"),
            ("Stress vs Strain", "Stress", "MPa", "Strain", "%"),
            ("Force vs Time", "Force", "N", "Time", "s"),
            ("Stress vs Time", "Stress", "MPa", "Time", "s"),
            ("Extension vs Time", "Extension", "mm", "Time", "s"),
        ]
        
        title, y_label, y_unit, x_label, x_unit = plot_types[index]
        
        self.plot_widget.setTitle(title, color='w', size='14pt')
        self.plot_widget.setLabel('left', y_label, units=y_unit, color='w')
        self.plot_widget.setLabel('bottom', x_label, units=x_unit, color='w')
        
        # Refresh plot with current data
        self._refresh_plot()
    
    def _refresh_plot(self):
        """Refresh the plot with current data based on selected plot type."""
        if not self.test_data:
            self.plot_curve.setData([], [])
            return
        
        plot_type = self.plot_type_combo.currentIndex()
        
        if plot_type == 0:  # Force vs Extension
            x = [d.extension for d in self.test_data]
            y = [d.force for d in self.test_data]
        elif plot_type == 1:  # Stress vs Strain
            x = [d.strain * 100 for d in self.test_data]  # Convert to %
            y = [d.stress for d in self.test_data]
        elif plot_type == 2:  # Force vs Time
            x = [d.timestamp / 1000.0 for d in self.test_data]  # Convert ms to s
            y = [d.force for d in self.test_data]
        elif plot_type == 3:  # Stress vs Time
            x = [d.timestamp / 1000.0 for d in self.test_data]
            y = [d.stress for d in self.test_data]
        elif plot_type == 4:  # Extension vs Time
            x = [d.timestamp / 1000.0 for d in self.test_data]
            y = [d.extension for d in self.test_data]
        else:
            x, y = [], []
        
        # Downsample for live display on Pi (keep full data for analysis)
        if PLOT_DOWNSAMPLE and len(x) > PLOT_MAX_POINTS:
            step = len(x) // PLOT_MAX_POINTS
            x = x[::step]
            y = y[::step]
        
        self.plot_curve.setData(x, y)
    
    def _show_results_dialog(self):
        """Show the full results analysis dialog."""
        if not self.test_data:
            QMessageBox.information(self, "Results", "No test data available.")
            return
        
        # Create analyzer and load data in batch (fast)
        analyzer = ResultsAnalyzer(
            self.config.specimen.gauge_length,
            self.config.specimen.cross_section_area
        )
        
        # Extract data arrays
        times = [d.timestamp / 1000.0 for d in self.test_data]
        forces = [d.force for d in self.test_data]
        extensions = [d.extension for d in self.test_data]
        
        # Load all data at once (skips live calculations)
        analyzer.load_data_batch(times, forces, extensions)
        
        # Show fast results dialog
        show_fast_results(self.config, analyzer, self)
    
    def _calculate_final_results(self):
        """Calculate final test results after test completion."""
        if not self.test_data:
            return
        
        # Create a fresh analyzer
        analyzer = ResultsAnalyzer(
            self.config.specimen.gauge_length,
            self.config.specimen.cross_section_area
        )
        
        # Extract data arrays and load in batch (fast)
        times = [d.timestamp / 1000.0 for d in self.test_data]
        forces = [d.force for d in self.test_data]
        extensions = [d.extension for d in self.test_data]
        
        analyzer.load_data_batch(times, forces, extensions)
        
        # Calculate mechanical properties
        props = analyzer.calculate_results()
        
        # Create TestResults object
        self.test_results = TestResults(
            max_force=props.max_force,
            max_stress=props.ultimate_tensile_strength,
            max_strain=props.elongation_at_break,
            max_extension=props.extension_at_break,
            yield_strength=props.yield_strength_offset,
            youngs_modulus=props.youngs_modulus,
            elongation_at_break=props.elongation_at_break,
            energy_absorbed=props.energy_to_break,
            failure_type=props.failure_type.value if props.failure_type else "Unknown",
            test_duration=(times[-1] - times[0]) if len(times) > 1 else 0.0,
            data_points=len(self.test_data)
        )
    
    def _refresh_ports(self):
        """Refresh available serial ports."""
        self.port_combo.clear()
        ports = SerialHandler.list_ports()
        self.port_combo.addItems(ports)
        
        # Try to find Pico
        pico_port = SerialHandler.find_pico()
        if pico_port and pico_port in ports:
            self.port_combo.setCurrentText(pico_port)
    
    def _auto_connect(self):
        """Attempt auto-connection to Pico."""
        pico_port = SerialHandler.find_pico()
        if pico_port:
            self.port_combo.setCurrentText(pico_port)
            self._toggle_connection()
    
    def _toggle_connection(self):
        """Toggle serial connection."""
        if self.serial.is_connected():
            self.serial.disconnect()
        else:
            port = self.port_combo.currentText()
            if port:
                self.serial.connect(port)
    
    def _update_button_states(self):
        """Update button enabled states based on connection and test state."""
        connected = self.serial.is_connected()
        testing = self.is_test_running
        paused = self.current_state == "PAUSED"
        ready = self.current_state == "READY"
        
        # Connection controls
        self.port_combo.setEnabled(not connected)
        self.refresh_btn.setEnabled(not connected)
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        
        # Test controls
        self.start_btn.setEnabled(connected and ready and not testing)
        self.stop_btn.setEnabled(connected and testing)
        self.pause_btn.setEnabled(connected and testing and not paused)
        self.resume_btn.setEnabled(connected and paused)
        
        # Jog controls
        self.jog_up_btn.setEnabled(connected and not testing)
        self.jog_down_btn.setEnabled(connected and not testing)
        self.home_btn.setEnabled(connected and not testing)
        self.tare_btn.setEnabled(connected and not testing)
        
        # Parameters
        self.speed_spin.setEnabled(connected and not testing)
        self.max_force_spin.setEnabled(connected and not testing)
        self.max_ext_spin.setEnabled(connected and not testing)
        
        # Emergency stop always enabled when connected
        self.emergency_btn.setEnabled(connected)
        
        # Export enabled when we have data
        self.export_btn.setEnabled(len(self.test_data) > 0)
        
        # View results enabled when we have data and test is done
        self.view_results_btn.setEnabled(len(self.test_data) > 0 and not testing)
    
    @pyqtSlot()
    def _on_connected(self):
        """Handle connection established."""
        self.status_bar.showMessage("Connected")
        self.state_label.setText("CONNECTED")
        self.state_label.setStyleSheet("color: #4caf50;")
        
        # Start status polling (Pi-optimized interval)
        self.status_timer.start(STATUS_POLL_RATE_MS)
        
        # Request initial status
        self.serial.identify()
        self.serial.get_status()
        
        self._update_button_states()
    
    @pyqtSlot()
    def _on_disconnected(self):
        """Handle disconnection."""
        self.status_timer.stop()
        self.status_bar.showMessage("Disconnected")
        self.state_label.setText("DISCONNECTED")
        self.state_label.setStyleSheet("color: #888888;")
        self.current_state = "DISCONNECTED"
        self.is_test_running = False
        self._update_button_states()
    
    @pyqtSlot(object)
    def _on_status(self, status: Status):
        """Handle status update."""
        self.current_state = status.state
        self.is_test_running = status.is_running
        
        # Update displays
        self.force_label.setText(f"{status.force:.2f}")
        self.position_label.setText(f"{status.position:.3f}")
        self.state_label.setText(status.state)
        
        # Update state label color
        colors = {
            "IDLE": "#888888",
            "READY": "#4caf50",
            "RUNNING": "#2196f3",
            "PAUSED": "#ff9800",
            "STOPPED": "#9e9e9e",
            "ERROR": "#f44336",
            "EMERGENCY": "#b71c1c",
            "HOMING": "#9c27b0"
        }
        color = colors.get(status.state, "#888888")
        self.state_label.setStyleSheet(f"color: {color};")
        
        self._update_button_states()
    
    @pyqtSlot(object)
    def _on_data(self, data: DataPoint):
        """Handle test data point."""
        self.test_data.append(data)
        
        # Limit buffer size for memory efficiency (Pi optimized)
        if len(self.test_data) > DATA_BUFFER_SIZE:
            # Keep every other point in older data
            self.test_data = self.test_data[:100] + self.test_data[100::2]
        
        # Throttle plot updates on Pi (only update every N data points)
        if IS_RASPBERRY_PI and len(self.test_data) % 3 != 0:
            # Skip plot update for 2 out of 3 data points on Pi
            pass
        else:
            # Update plot using current plot type
            self._refresh_plot()
        
        # Calculate live values
        current_stress = data.stress
        current_strain = data.strain * 100  # Convert to %
        
        # Calculate rate (mm/s) from last two points
        rate = 0.0
        if len(self.test_data) >= 2:
            prev = self.test_data[-2]
            dt = (data.timestamp - prev.timestamp) / 1000.0  # Convert to seconds
            if dt > 0:
                rate = abs(data.extension - prev.extension) / dt
        
        # Calculate cumulative energy (trapezoidal integration)
        if len(self.test_data) >= 2:
            prev = self.test_data[-2]
            avg_force = (data.force + prev.force) / 2
            d_ext = abs(data.extension - prev.extension) / 1000.0  # Convert to meters
            self.cumulative_energy += avg_force * d_ext
        
        # Update live displays
        self.live_stress.value_label.setText(f"{current_stress:.2f}")
        self.live_strain.value_label.setText(f"{current_strain:.3f}")
        self.live_rate.value_label.setText(f"{rate:.2f}")
        self.live_energy.value_label.setText(f"{self.cumulative_energy:.3f}")
        
        # Update test time
        if len(self.test_data) > 0:
            elapsed_s = data.timestamp / 1000.0
            mins = int(elapsed_s // 60)
            secs = elapsed_s % 60
            self.test_time_label.setText(f"Time: {mins:02d}:{secs:04.1f}")
        
        # Determine test stage
        if len(self.test_data) < 10:
            stage = "Pre-load"
        else:
            forces = [d.force for d in self.test_data]
            max_force = max(forces)
            if data.force >= max_force * 0.95:
                stage = "Peak Load"
            elif data.force < max_force * 0.5 and len(self.test_data) > 20:
                stage = "Post-Failure"
            else:
                stage = "Loading"
        
        self.test_stage_label.setText(f"Stage: {stage}")
        
        # Update results summary
        max_force = max(d.force for d in self.test_data)
        max_stress = max(d.stress for d in self.test_data)
        max_ext = max(d.extension for d in self.test_data)
        
        self.max_force_result.value_label.setText(f"{max_force:.2f}")
        self.max_stress_result.value_label.setText(f"{max_stress:.2f}")
        self.max_ext_result.value_label.setText(f"{max_ext:.3f}")
        self.data_points_result.value_label.setText(str(len(self.test_data)))
    
    @pyqtSlot(float)
    def _on_force(self, force: float):
        """Handle force reading."""
        self.force_label.setText(f"{force:.2f}")
    
    @pyqtSlot(float)
    def _on_position(self, position: float):
        """Handle position reading."""
        self.position_label.setText(f"{position:.3f}")
    
    @pyqtSlot(str)
    def _on_response(self, response: str):
        """Handle command response."""
        self.status_bar.showMessage(response, 3000)
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """Handle error."""
        self.status_bar.showMessage(f"Error: {error}", 5000)
    
    def _request_status(self):
        """Request status update from controller."""
        if self.serial.is_connected():
            self.serial.get_status()
    
    def _start_test(self):
        """Start tensile test."""
        # Clear previous data
        self.test_data.clear()
        self.plot_curve.setData([], [])
        self.max_force_marker.setData([], [])
        self.yield_point_marker.setData([], [])
        
        # Reset tracking variables
        self.cumulative_energy = 0.0
        self.last_data_time = 0
        self.test_results = None
        
        # Reset live displays
        self.live_stress.value_label.setText("0.00")
        self.live_strain.value_label.setText("0.000")
        self.live_rate.value_label.setText("0.00")
        self.live_energy.value_label.setText("0.000")
        self.test_time_label.setText("Time: 00:00.0")
        self.test_stage_label.setText("Stage: Pre-load")
        
        # Reset results
        self.max_force_result.value_label.setText("0.00")
        self.max_stress_result.value_label.setText("0.00")
        self.max_ext_result.value_label.setText("0.000")
        self.data_points_result.value_label.setText("0")
        
        # Update analyzer with current config
        self.analyzer = ResultsAnalyzer(
            self.config.specimen.gauge_length,
            self.config.specimen.cross_section_area
        )
        
        self.serial.start_test()
    
    def _stop_test(self):
        """Stop tensile test."""
        self.serial.stop_test()
        
        # Calculate final results
        if len(self.test_data) > 10:
            self._calculate_final_results()
            self.test_stage_label.setText("Stage: Complete")
            self.test_stage_label.setStyleSheet("color: #4caf50; font-weight: bold;")
    
    def _pause_test(self):
        """Pause tensile test."""
        self.serial.pause_test()
    
    def _resume_test(self):
        """Resume tensile test."""
        self.serial.resume_test()
    
    def _emergency_stop(self):
        """Trigger emergency stop."""
        self.serial.emergency_stop()
        QMessageBox.warning(
            self, "Emergency Stop",
            "Emergency stop activated!\nCheck the machine before continuing."
        )
    
    def _home(self):
        """Home the machine."""
        self.serial.home()
    
    def _tare(self):
        """Tare the load cell."""
        self.serial.tare()
    
    def _on_speed_changed(self, value):
        """Handle speed parameter change."""
        if self.serial.is_connected():
            self.serial.set_speed(value)
    
    def _on_max_force_changed(self, value):
        """Handle max force parameter change."""
        if self.serial.is_connected():
            self.serial.set_max_force(value)
    
    def _on_max_ext_changed(self, value):
        """Handle max extension parameter change."""
        if self.serial.is_connected():
            self.serial.set_max_extension(value)
    
    def _export_data(self):
        """Export test data to CSV/Excel."""
        if not self.test_data:
            QMessageBox.information(self, "Export", "No data to export.")
            return
        
        # Get filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"tensile_test_{timestamp}.csv"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", default_name,
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        
        if not filename:
            return
        
        # Create DataFrame with test data
        df = pd.DataFrame([
            {
                'Time (ms)': d.timestamp,
                'Force (N)': d.force,
                'Extension (mm)': d.extension,
                'Stress (MPa)': d.stress,
                'Strain': d.strain
            }
            for d in self.test_data
        ])
        
        # Create metadata DataFrame
        c = self.config
        metadata = {
            'Parameter': [
                'Sample ID', 'Batch ID', 'Operator', 'Customer', 'Project',
                'Test Standard', 'Material Type', 'Material Name',
                'Gauge Length (mm)', 'Thickness (mm)', 'Width (mm)', 'Cross-Section Area (mm²)',
                'Test Speed (mm/min)', 'Max Force (N)', 'Max Extension (mm)',
                'Temperature (°C)', 'Humidity (%RH)',
                'Test Date'
            ],
            'Value': [
                c.metadata.sample_id, c.metadata.batch_id, c.metadata.operator_name,
                c.metadata.customer_name, c.metadata.project_name,
                c.metadata.test_standard.value, c.metadata.material_type.value, c.metadata.material_name,
                c.specimen.gauge_length, c.specimen.thickness, c.specimen.width, c.specimen.cross_section_area,
                c.control.test_speed, c.termination.max_force, c.termination.max_extension,
                c.environment.temperature, c.environment.humidity,
                c.metadata.test_date.strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        df_meta = pd.DataFrame(metadata)
        
        # Calculate results
        if self.test_data:
            max_force = max(d.force for d in self.test_data)
            max_ext = max(d.extension for d in self.test_data)
            max_stress = max(d.stress for d in self.test_data)
            max_strain = max(d.strain for d in self.test_data)
            
            results = {
                'Result': ['Max Force (N)', 'Max Extension (mm)', 'Max Stress (MPa)', 'Max Strain (%)'],
                'Value': [f"{max_force:.2f}", f"{max_ext:.3f}", f"{max_stress:.2f}", f"{max_strain*100:.2f}"]
            }
            df_results = pd.DataFrame(results)
        else:
            df_results = pd.DataFrame()
        
        # Export
        try:
            if filename.endswith('.xlsx'):
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df_meta.to_excel(writer, sheet_name='Test Info', index=False)
                    df_results.to_excel(writer, sheet_name='Results', index=False)
                    df.to_excel(writer, sheet_name='Data', index=False)
            else:
                # For CSV, save data only (or could save multiple files)
                df.to_csv(filename, index=False)
                # Also save metadata
                meta_filename = filename.replace('.csv', '_info.csv')
                df_meta.to_csv(meta_filename, index=False)
            
            self.status_bar.showMessage(f"Data exported to {filename}", 5000)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close."""
        self.serial.disconnect()
        event.accept()
