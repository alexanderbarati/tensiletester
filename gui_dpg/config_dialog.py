#!/usr/bin/env python3
"""
Configuration Dialog for Professional Tensile Testing System

Multi-tab configuration dialog with all inputs required for
professional tensile testing following ISO 527, ASTM D638 standards.

Author: DIY Tensile Tester Project
Version: 2.0.0
"""

import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from datetime import datetime
import json
import os

from models import (
    TestConfiguration, TestMetadata, SpecimenConfig, MachineConfig,
    TestControlConfig, DataAcquisitionConfig, TerminationCriteria,
    TestStandard, MaterialType, ControlMode, ExtensometerType,
    LoadCellRange
)

# Color scheme
COLORS = {
    'accent': (79, 195, 247),
    'success': (76, 175, 80),
    'warning': (255, 152, 0),
    'error': (244, 67, 54),
    'text': (255, 255, 255),
    'text_dim': (136, 136, 136),
    'header': (100, 181, 246),
}


class ConfigDialog:
    """Professional multi-tab configuration dialog."""
    
    def __init__(self):
        self.config = TestConfiguration()
        self.on_config_applied: Optional[Callable[[TestConfiguration], None]] = None
        self.window_tag = "config_dialog_window"
        
    def show(self):
        """Show the configuration dialog."""
        if dpg.does_item_exist(self.window_tag):
            dpg.show_item(self.window_tag)
            return
        
        self._create_dialog()
        dpg.show_item(self.window_tag)
    
    def hide(self):
        """Hide the configuration dialog."""
        if dpg.does_item_exist(self.window_tag):
            dpg.hide_item(self.window_tag)
    
    def _create_dialog(self):
        """Create the configuration dialog with tabs."""
        with dpg.window(
            label="Test Configuration",
            tag=self.window_tag,
            width=700,
            height=550,
            show=False,
            modal=True,
            no_collapse=True,
            pos=(162, 25)
        ):
            # Tab bar
            with dpg.tab_bar(tag="config_tabs"):
                self._create_metadata_tab()
                self._create_specimen_tab()
                self._create_machine_tab()
                self._create_control_tab()
                self._create_acquisition_tab()
                self._create_termination_tab()
            
            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Apply", width=100, callback=self._on_apply)
                dpg.add_button(label="OK", width=100, callback=self._on_ok)
                dpg.add_button(label="Cancel", width=100, callback=self._on_cancel)
                dpg.add_spacer(width=50)
                dpg.add_button(label="Load...", width=80, callback=self._on_load)
                dpg.add_button(label="Save...", width=80, callback=self._on_save)
                dpg.add_button(label="Reset", width=80, callback=self._on_reset)
    
    # ============== Tab Creation ==============
    
    def _create_metadata_tab(self):
        """Create metadata/identification tab."""
        with dpg.tab(label="Identification"):
            dpg.add_spacer(height=10)
            
            # Test Standard selection
            self._section_header("Test Standard")
            with dpg.group(horizontal=True):
                dpg.add_text("Standard:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=[e.value for e in TestStandard],
                    default_value=self.config.metadata.test_standard.value,
                    width=250,
                    tag="cfg_test_standard"
                )
            
            dpg.add_spacer(height=10)
            
            # Sample Identification
            self._section_header("Sample Identification")
            self._input_row("Test ID:", "cfg_test_id", self.config.metadata.test_id, "Auto-generated if empty")
            self._input_row("Sample ID:", "cfg_sample_id", self.config.metadata.sample_id, "e.g., PLA-001")
            self._input_row("Batch ID:", "cfg_batch_id", self.config.metadata.batch_id, "")
            self._input_row("Lot Number:", "cfg_lot_number", self.config.metadata.lot_number, "")
            
            dpg.add_spacer(height=10)
            
            # Material Information
            self._section_header("Material Information")
            with dpg.group(horizontal=True):
                dpg.add_text("Material Type:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=[e.value for e in MaterialType],
                    default_value=self.config.metadata.material_type.value,
                    width=200,
                    tag="cfg_material_type"
                )
            self._input_row("Material Name:", "cfg_material_name", self.config.metadata.material_name, "e.g., PLA")
            self._input_row("Material Grade:", "cfg_material_grade", self.config.metadata.material_grade, "e.g., eSUN PLA+")
            
            dpg.add_spacer(height=10)
            
            # Personnel
            self._section_header("Personnel & Project")
            self._input_row("Operator:", "cfg_operator", self.config.metadata.operator_name, "")
            self._input_row("Customer:", "cfg_customer", self.config.metadata.customer_name, "")
            self._input_row("Project:", "cfg_project", self.config.metadata.project_name, "")
            
            dpg.add_spacer(height=10)
            
            # Environment
            self._section_header("Environment Conditions")
            with dpg.group(horizontal=True):
                dpg.add_text("Temperature:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.metadata.temperature,
                    width=100, tag="cfg_temperature", step=0.5
                )
                dpg.add_text("°C", color=COLORS['text_dim'])
                dpg.add_spacer(width=30)
                dpg.add_text("Humidity:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.metadata.humidity,
                    width=100, tag="cfg_humidity", step=1.0
                )
                dpg.add_text("% RH", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=10)
            
            # Notes
            self._section_header("Notes")
            dpg.add_input_text(
                default_value=self.config.metadata.notes,
                width=-1, height=60,
                multiline=True,
                tag="cfg_notes"
            )
    
    def _create_specimen_tab(self):
        """Create specimen dimensions tab."""
        with dpg.tab(label="Specimen"):
            dpg.add_spacer(height=10)
            
            # Specimen Type
            self._section_header("Specimen Type")
            with dpg.group(horizontal=True):
                dpg.add_text("Specimen Type:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=["Type 1A (ISO 527)", "Type 1B (ISO 527)", "Type V (ASTM D638)", 
                           "Type I (ASTM D638)", "Round Bar", "Custom"],
                    default_value=self.config.specimen.specimen_type,
                    width=200,
                    tag="cfg_specimen_type",
                    callback=self._on_specimen_type_changed
                )
            
            dpg.add_spacer(height=15)
            
            # Primary Dimensions
            self._section_header("Primary Dimensions")
            
            with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column()
                
                # Gauge Length
                with dpg.table_row():
                    dpg.add_text("Gauge Length:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.specimen.gauge_length,
                        width=120, tag="cfg_gauge_length", step=1.0,
                        callback=self._on_dimension_changed
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                    dpg.add_text("(Lo - measurement length)", color=COLORS['text_dim'])
                
                # Thickness
                with dpg.table_row():
                    dpg.add_text("Thickness:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.specimen.thickness,
                        width=120, tag="cfg_thickness", step=0.1,
                        callback=self._on_dimension_changed
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                    dpg.add_text("", color=COLORS['text_dim'])
                
                # Width
                with dpg.table_row():
                    dpg.add_text("Width:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.specimen.width,
                        width=120, tag="cfg_width", step=0.1,
                        callback=self._on_dimension_changed
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                    dpg.add_text("", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=10)
            
            # Cross-section Area
            self._section_header("Cross-Sectional Area")
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    label="Manual entry",
                    default_value=self.config.specimen.cross_section_manual,
                    tag="cfg_cross_section_manual",
                    callback=self._on_cross_section_mode_changed
                )
            with dpg.group(horizontal=True):
                dpg.add_text("Area:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.specimen.cross_section_area,
                    width=120, tag="cfg_cross_section", step=0.1,
                    enabled=self.config.specimen.cross_section_manual
                )
                dpg.add_text("mm²", color=COLORS['text_dim'])
                dpg.add_text("(W × T = ", color=COLORS['text_dim'])
                dpg.add_text(f"{self.config.specimen.width * self.config.specimen.thickness:.2f}", 
                            tag="cfg_calculated_area", color=COLORS['accent'])
                dpg.add_text(" mm²)", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Secondary Dimensions
            self._section_header("Secondary Dimensions")
            with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column()
                
                # Parallel Length
                with dpg.table_row():
                    dpg.add_text("Parallel Length:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.specimen.parallel_length,
                        width=120, tag="cfg_parallel_length", step=1.0
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                    dpg.add_text("(constant cross-section)", color=COLORS['text_dim'])
                
                # Total Length
                with dpg.table_row():
                    dpg.add_text("Total Length:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.specimen.total_length,
                        width=120, tag="cfg_total_length", step=1.0
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                    dpg.add_text("", color=COLORS['text_dim'])
                
                # Grip Distance
                with dpg.table_row():
                    dpg.add_text("Grip Distance:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.specimen.grip_distance,
                        width=120, tag="cfg_grip_distance", step=1.0
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                    dpg.add_text("(between grips)", color=COLORS['text_dim'])
    
    def _create_machine_tab(self):
        """Create machine configuration tab."""
        with dpg.tab(label="Machine"):
            dpg.add_spacer(height=10)
            
            # Load Cell
            self._section_header("Load Cell")
            with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column()
                
                with dpg.table_row():
                    dpg.add_text("Capacity:", color=COLORS['text_dim'])
                    dpg.add_combo(
                        items=[e.value for e in LoadCellRange],
                        default_value=self.config.machine.load_cell_range.value,
                        width=150,
                        tag="cfg_load_cell_range"
                    )
                
                with dpg.table_row():
                    dpg.add_text("Serial Number:", color=COLORS['text_dim'])
                    dpg.add_input_text(
                        default_value=self.config.machine.load_cell_serial,
                        width=200, tag="cfg_load_cell_serial"
                    )
                
                with dpg.table_row():
                    dpg.add_text("Calibration Date:", color=COLORS['text_dim'])
                    dpg.add_input_text(
                        default_value=self.config.machine.load_cell_calibration_date,
                        width=150, tag="cfg_calibration_date"
                    )
            
            dpg.add_spacer(height=15)
            
            # Extensometer
            self._section_header("Extensometer")
            with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column()
                
                with dpg.table_row():
                    dpg.add_text("Type:", color=COLORS['text_dim'])
                    dpg.add_combo(
                        items=[e.value for e in ExtensometerType],
                        default_value=self.config.machine.extensometer_type.value,
                        width=200,
                        tag="cfg_extensometer_type"
                    )
                
                with dpg.table_row():
                    dpg.add_text("Gauge Length:", color=COLORS['text_dim'])
                    with dpg.group(horizontal=True):
                        dpg.add_input_float(
                            default_value=self.config.machine.extensometer_gauge,
                            width=100, tag="cfg_extensometer_gauge", step=5.0
                        )
                        dpg.add_text("mm", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Travel Limits
            self._section_header("Travel Limits")
            with dpg.group(horizontal=True):
                dpg.add_text("Upper Limit:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.machine.upper_limit,
                    width=100, tag="cfg_upper_limit", step=5.0
                )
                dpg.add_text("mm", color=COLORS['text_dim'])
                dpg.add_spacer(width=30)
                dpg.add_text("Lower Limit:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.machine.lower_limit,
                    width=100, tag="cfg_lower_limit", step=1.0
                )
                dpg.add_text("mm", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Safety Limits
            self._section_header("Safety Limits")
            with dpg.group(horizontal=True):
                dpg.add_text("Max Force:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.machine.force_limit,
                    width=100, tag="cfg_force_limit", step=10.0
                )
                dpg.add_text("N", color=COLORS['text_dim'])
                dpg.add_spacer(width=30)
                dpg.add_text("Max Extension:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.machine.extension_limit,
                    width=100, tag="cfg_extension_limit", step=5.0
                )
                dpg.add_text("mm", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=10)
            dpg.add_checkbox(
                label="Emergency Stop Enabled",
                default_value=self.config.machine.emergency_stop_enabled,
                tag="cfg_emergency_enabled"
            )
            
            dpg.add_spacer(height=15)
            
            # Zeroing Options
            self._section_header("Zeroing on Test Start")
            dpg.add_checkbox(
                label="Zero force (tare load cell)",
                default_value=self.config.machine.zero_force_on_start,
                tag="cfg_zero_force"
            )
            dpg.add_checkbox(
                label="Zero extension (reset position)",
                default_value=self.config.machine.zero_extension_on_start,
                tag="cfg_zero_extension"
            )
            dpg.add_checkbox(
                label="Zero extensometer",
                default_value=self.config.machine.zero_extensometer_on_start,
                tag="cfg_zero_extensometer"
            )
    
    def _create_control_tab(self):
        """Create test control parameters tab."""
        with dpg.tab(label="Control"):
            dpg.add_spacer(height=10)
            
            # Control Mode
            self._section_header("Control Mode")
            with dpg.group(horizontal=True):
                dpg.add_text("Mode:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=[e.value for e in ControlMode],
                    default_value=self.config.control.control_mode.value,
                    width=200,
                    tag="cfg_control_mode",
                    callback=self._on_control_mode_changed
                )
            
            dpg.add_spacer(height=15)
            
            # Speed Settings
            self._section_header("Speed Settings")
            with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column()
                
                with dpg.table_row():
                    dpg.add_text("Test Speed:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.control.test_speed,
                        width=100, tag="cfg_test_speed", step=0.5
                    )
                    dpg.add_text("mm/min", color=COLORS['text_dim'])
                
                with dpg.table_row():
                    dpg.add_text("Strain Rate:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.control.strain_rate,
                        width=100, tag="cfg_strain_rate", step=0.0001, format="%.4f"
                    )
                    dpg.add_text("1/s", color=COLORS['text_dim'])
                
                with dpg.table_row():
                    dpg.add_text("Load Rate:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.control.load_rate,
                        width=100, tag="cfg_load_rate", step=1.0
                    )
                    dpg.add_text("N/s", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Preload
            self._section_header("Preload")
            dpg.add_checkbox(
                label="Enable preload",
                default_value=self.config.control.preload_enabled,
                tag="cfg_preload_enabled"
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Preload:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.control.preload_value,
                    width=100, tag="cfg_preload_value", step=0.1
                )
                dpg.add_text("N", color=COLORS['text_dim'])
                dpg.add_spacer(width=30)
                dpg.add_text("Speed:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.control.preload_speed,
                    width=100, tag="cfg_preload_speed", step=1.0
                )
                dpg.add_text("mm/min", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Hold Settings
            self._section_header("Hold Settings")
            dpg.add_checkbox(
                label="Enable hold at load",
                default_value=self.config.control.hold_enabled,
                tag="cfg_hold_enabled"
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Hold at:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.control.hold_at_load,
                    width=100, tag="cfg_hold_at_load", step=10.0
                )
                dpg.add_text("N", color=COLORS['text_dim'])
                dpg.add_spacer(width=30)
                dpg.add_text("Duration:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.control.hold_duration,
                    width=100, tag="cfg_hold_duration", step=1.0
                )
                dpg.add_text("s", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Return Settings
            self._section_header("Return to Start")
            dpg.add_checkbox(
                label="Return after test",
                default_value=self.config.control.return_enabled,
                tag="cfg_return_enabled"
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Return Speed:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.control.return_speed,
                    width=100, tag="cfg_return_speed", step=5.0
                )
                dpg.add_text("mm/min", color=COLORS['text_dim'])
    
    def _create_acquisition_tab(self):
        """Create data acquisition settings tab."""
        with dpg.tab(label="Acquisition"):
            dpg.add_spacer(height=10)
            
            # Sampling Rate
            self._section_header("Sampling Rate")
            with dpg.group(horizontal=True):
                dpg.add_text("Base Rate:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.acquisition.sampling_rate,
                    width=100, tag="cfg_sampling_rate", step=1.0
                )
                dpg.add_text("Hz", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=5)
            dpg.add_checkbox(
                label="Enable event-based high-speed sampling",
                default_value=self.config.acquisition.event_sampling_enabled,
                tag="cfg_event_sampling"
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Event Rate:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.acquisition.event_sampling_rate,
                    width=100, tag="cfg_event_rate", step=10.0
                )
                dpg.add_text("Hz (during yield, break)", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Filtering
            self._section_header("Data Filtering")
            dpg.add_checkbox(
                label="Enable digital filter",
                default_value=self.config.acquisition.digital_filter_enabled,
                tag="cfg_digital_filter"
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Cutoff Frequency:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.acquisition.filter_cutoff,
                    width=100, tag="cfg_filter_cutoff", step=1.0
                )
                dpg.add_text("Hz", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=5)
            dpg.add_checkbox(
                label="Enable median filter (noise reduction)",
                default_value=self.config.acquisition.median_filter_enabled,
                tag="cfg_median_filter"
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Window Size:", color=COLORS['text_dim'])
                dpg.add_input_int(
                    default_value=self.config.acquisition.median_filter_window,
                    width=100, tag="cfg_median_window", step=2, min_value=3, max_value=11
                )
                dpg.add_text("samples", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Channels
            self._section_header("Recording Channels")
            with dpg.group(horizontal=True):
                dpg.add_checkbox(label="Force", default_value=True, enabled=False)
                dpg.add_checkbox(label="Extension", default_value=True, enabled=False)
                dpg.add_checkbox(label="Time", default_value=True, enabled=False)
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    label="Strain", 
                    default_value=self.config.acquisition.record_strain,
                    tag="cfg_record_strain"
                )
                dpg.add_checkbox(
                    label="Temperature", 
                    default_value=self.config.acquisition.record_temperature,
                    tag="cfg_record_temp"
                )
                dpg.add_checkbox(
                    label="Video", 
                    default_value=self.config.acquisition.record_video,
                    tag="cfg_record_video"
                )
            
            dpg.add_spacer(height=15)
            
            # Calculations
            self._section_header("Real-time Calculations")
            dpg.add_checkbox(
                label="Calculate true stress/strain (large deformation)",
                default_value=self.config.acquisition.calculate_true_values,
                tag="cfg_true_values"
            )
    
    def _create_termination_tab(self):
        """Create termination criteria tab."""
        with dpg.tab(label="Termination"):
            dpg.add_spacer(height=10)
            
            # Break Detection
            self._section_header("Break Detection")
            dpg.add_checkbox(
                label="Enable automatic break detection",
                default_value=self.config.termination.break_detection_enabled,
                tag="cfg_break_detection"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_text("Force Drop:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.termination.break_force_drop,
                    width=100, tag="cfg_break_drop", step=5.0
                )
                dpg.add_text("% from peak", color=COLORS['text_dim'])
            
            with dpg.group(horizontal=True):
                dpg.add_text("Min Force After Break:", color=COLORS['text_dim'])
                dpg.add_input_float(
                    default_value=self.config.termination.break_force_threshold,
                    width=100, tag="cfg_break_threshold", step=0.1
                )
                dpg.add_text("N", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Safety Limits
            self._section_header("Safety Limits (Test will stop if exceeded)")
            with dpg.table(header_row=False, borders_innerV=False, borders_outerH=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column()
                
                with dpg.table_row():
                    dpg.add_text("Maximum Force:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.termination.max_force,
                        width=100, tag="cfg_term_max_force", step=10.0
                    )
                    dpg.add_text("N", color=COLORS['text_dim'])
                
                with dpg.table_row():
                    dpg.add_text("Maximum Extension:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.termination.max_extension,
                        width=100, tag="cfg_term_max_ext", step=5.0
                    )
                    dpg.add_text("mm", color=COLORS['text_dim'])
                
                with dpg.table_row():
                    dpg.add_text("Maximum Strain:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.termination.max_strain,
                        width=100, tag="cfg_term_max_strain", step=10.0
                    )
                    dpg.add_text("%", color=COLORS['text_dim'])
                
                with dpg.table_row():
                    dpg.add_text("Maximum Time:", color=COLORS['text_dim'])
                    dpg.add_input_float(
                        default_value=self.config.termination.max_time,
                        width=100, tag="cfg_term_max_time", step=60.0
                    )
                    dpg.add_text("s", color=COLORS['text_dim'])
            
            dpg.add_spacer(height=15)
            
            # Post-Break Actions
            self._section_header("Post-Break Actions")
            dpg.add_checkbox(
                label="Stop test at break",
                default_value=self.config.termination.stop_at_break,
                tag="cfg_stop_at_break"
            )
            dpg.add_checkbox(
                label="Return to start after break",
                default_value=self.config.termination.return_after_break,
                tag="cfg_return_after_break"
            )
    
    # ============== Helper Methods ==============
    
    def _section_header(self, text: str):
        """Create a section header."""
        dpg.add_text(text, color=COLORS['header'])
        dpg.add_separator()
        dpg.add_spacer(height=5)
    
    def _input_row(self, label: str, tag: str, default: str, hint: str = ""):
        """Create an input row with label."""
        with dpg.group(horizontal=True):
            dpg.add_text(label, color=COLORS['text_dim'])
            dpg.add_input_text(default_value=default, width=200, tag=tag, hint=hint)
    
    # ============== Callbacks ==============
    
    def _on_dimension_changed(self, sender, app_data):
        """Handle dimension change - recalculate area."""
        thickness = dpg.get_value("cfg_thickness")
        width = dpg.get_value("cfg_width")
        calculated = thickness * width
        dpg.set_value("cfg_calculated_area", f"{calculated:.2f}")
        
        if not dpg.get_value("cfg_cross_section_manual"):
            dpg.set_value("cfg_cross_section", calculated)
    
    def _on_cross_section_mode_changed(self, sender, app_data):
        """Handle cross-section mode change."""
        manual = app_data
        dpg.configure_item("cfg_cross_section", enabled=manual)
        if not manual:
            thickness = dpg.get_value("cfg_thickness")
            width = dpg.get_value("cfg_width")
            dpg.set_value("cfg_cross_section", thickness * width)
    
    def _on_specimen_type_changed(self, sender, app_data):
        """Apply specimen type preset."""
        presets = {
            "Type 1A (ISO 527)": {"gauge": 50, "thickness": 4, "width": 10, "parallel": 80, "total": 150, "grip": 115},
            "Type 1B (ISO 527)": {"gauge": 50, "thickness": 4, "width": 10, "parallel": 60, "total": 150, "grip": 115},
            "Type V (ASTM D638)": {"gauge": 7.62, "thickness": 3.2, "width": 3.18, "parallel": 9.53, "total": 63.5, "grip": 25.4},
            "Type I (ASTM D638)": {"gauge": 50, "thickness": 3.2, "width": 13, "parallel": 57, "total": 165, "grip": 115},
        }
        
        if app_data in presets:
            p = presets[app_data]
            dpg.set_value("cfg_gauge_length", p["gauge"])
            dpg.set_value("cfg_thickness", p["thickness"])
            dpg.set_value("cfg_width", p["width"])
            dpg.set_value("cfg_parallel_length", p["parallel"])
            dpg.set_value("cfg_total_length", p["total"])
            dpg.set_value("cfg_grip_distance", p["grip"])
            self._on_dimension_changed(None, None)
    
    def _on_control_mode_changed(self, sender, app_data):
        """Handle control mode change."""
        # Could enable/disable relevant fields based on mode
        pass
    
    def _on_apply(self):
        """Apply configuration without closing."""
        self._read_config()
        if self.on_config_applied:
            self.on_config_applied(self.config)
    
    def _on_ok(self):
        """Apply and close."""
        self._on_apply()
        self.hide()
    
    def _on_cancel(self):
        """Cancel and close."""
        self.hide()
    
    def _on_load(self):
        """Load configuration from file."""
        # TODO: Implement file dialog
        pass
    
    def _on_save(self):
        """Save configuration to file."""
        # TODO: Implement file dialog
        config_dict = self.config.to_dict()
        filename = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            print(f"Configuration saved to {filename}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _on_reset(self):
        """Reset to defaults."""
        self.config = TestConfiguration()
        self._update_ui_from_config()
    
    def _read_config(self):
        """Read all values from UI into config."""
        # Metadata
        std_str = dpg.get_value("cfg_test_standard")
        for std in TestStandard:
            if std.value == std_str:
                self.config.metadata.test_standard = std
                break
        
        mat_str = dpg.get_value("cfg_material_type")
        for mat in MaterialType:
            if mat.value == mat_str:
                self.config.metadata.material_type = mat
                break
        
        self.config.metadata.test_id = dpg.get_value("cfg_test_id")
        self.config.metadata.sample_id = dpg.get_value("cfg_sample_id")
        self.config.metadata.batch_id = dpg.get_value("cfg_batch_id")
        self.config.metadata.lot_number = dpg.get_value("cfg_lot_number")
        self.config.metadata.material_name = dpg.get_value("cfg_material_name")
        self.config.metadata.material_grade = dpg.get_value("cfg_material_grade")
        self.config.metadata.operator_name = dpg.get_value("cfg_operator")
        self.config.metadata.customer_name = dpg.get_value("cfg_customer")
        self.config.metadata.project_name = dpg.get_value("cfg_project")
        self.config.metadata.temperature = dpg.get_value("cfg_temperature")
        self.config.metadata.humidity = dpg.get_value("cfg_humidity")
        self.config.metadata.notes = dpg.get_value("cfg_notes")
        
        # Specimen
        self.config.specimen.specimen_type = dpg.get_value("cfg_specimen_type")
        self.config.specimen.gauge_length = dpg.get_value("cfg_gauge_length")
        self.config.specimen.thickness = dpg.get_value("cfg_thickness")
        self.config.specimen.width = dpg.get_value("cfg_width")
        self.config.specimen.cross_section_manual = dpg.get_value("cfg_cross_section_manual")
        self.config.specimen.cross_section_area = dpg.get_value("cfg_cross_section")
        self.config.specimen.parallel_length = dpg.get_value("cfg_parallel_length")
        self.config.specimen.total_length = dpg.get_value("cfg_total_length")
        self.config.specimen.grip_distance = dpg.get_value("cfg_grip_distance")
        
        # Machine
        lc_str = dpg.get_value("cfg_load_cell_range")
        for lc in LoadCellRange:
            if lc.value == lc_str:
                self.config.machine.load_cell_range = lc
                break
        
        ext_str = dpg.get_value("cfg_extensometer_type")
        for ext in ExtensometerType:
            if ext.value == ext_str:
                self.config.machine.extensometer_type = ext
                break
        
        self.config.machine.load_cell_serial = dpg.get_value("cfg_load_cell_serial")
        self.config.machine.load_cell_calibration_date = dpg.get_value("cfg_calibration_date")
        self.config.machine.extensometer_gauge = dpg.get_value("cfg_extensometer_gauge")
        self.config.machine.upper_limit = dpg.get_value("cfg_upper_limit")
        self.config.machine.lower_limit = dpg.get_value("cfg_lower_limit")
        self.config.machine.force_limit = dpg.get_value("cfg_force_limit")
        self.config.machine.extension_limit = dpg.get_value("cfg_extension_limit")
        self.config.machine.emergency_stop_enabled = dpg.get_value("cfg_emergency_enabled")
        self.config.machine.zero_force_on_start = dpg.get_value("cfg_zero_force")
        self.config.machine.zero_extension_on_start = dpg.get_value("cfg_zero_extension")
        self.config.machine.zero_extensometer_on_start = dpg.get_value("cfg_zero_extensometer")
        
        # Control
        ctrl_str = dpg.get_value("cfg_control_mode")
        for ctrl in ControlMode:
            if ctrl.value == ctrl_str:
                self.config.control.control_mode = ctrl
                break
        
        self.config.control.test_speed = dpg.get_value("cfg_test_speed")
        self.config.control.strain_rate = dpg.get_value("cfg_strain_rate")
        self.config.control.load_rate = dpg.get_value("cfg_load_rate")
        self.config.control.preload_enabled = dpg.get_value("cfg_preload_enabled")
        self.config.control.preload_value = dpg.get_value("cfg_preload_value")
        self.config.control.preload_speed = dpg.get_value("cfg_preload_speed")
        self.config.control.hold_enabled = dpg.get_value("cfg_hold_enabled")
        self.config.control.hold_at_load = dpg.get_value("cfg_hold_at_load")
        self.config.control.hold_duration = dpg.get_value("cfg_hold_duration")
        self.config.control.return_enabled = dpg.get_value("cfg_return_enabled")
        self.config.control.return_speed = dpg.get_value("cfg_return_speed")
        
        # Acquisition
        self.config.acquisition.sampling_rate = dpg.get_value("cfg_sampling_rate")
        self.config.acquisition.event_sampling_enabled = dpg.get_value("cfg_event_sampling")
        self.config.acquisition.event_sampling_rate = dpg.get_value("cfg_event_rate")
        self.config.acquisition.digital_filter_enabled = dpg.get_value("cfg_digital_filter")
        self.config.acquisition.filter_cutoff = dpg.get_value("cfg_filter_cutoff")
        self.config.acquisition.median_filter_enabled = dpg.get_value("cfg_median_filter")
        self.config.acquisition.median_filter_window = dpg.get_value("cfg_median_window")
        self.config.acquisition.record_strain = dpg.get_value("cfg_record_strain")
        self.config.acquisition.record_temperature = dpg.get_value("cfg_record_temp")
        self.config.acquisition.record_video = dpg.get_value("cfg_record_video")
        self.config.acquisition.calculate_true_values = dpg.get_value("cfg_true_values")
        
        # Termination
        self.config.termination.break_detection_enabled = dpg.get_value("cfg_break_detection")
        self.config.termination.break_force_drop = dpg.get_value("cfg_break_drop")
        self.config.termination.break_force_threshold = dpg.get_value("cfg_break_threshold")
        self.config.termination.max_force = dpg.get_value("cfg_term_max_force")
        self.config.termination.max_extension = dpg.get_value("cfg_term_max_ext")
        self.config.termination.max_strain = dpg.get_value("cfg_term_max_strain")
        self.config.termination.max_time = dpg.get_value("cfg_term_max_time")
        self.config.termination.stop_at_break = dpg.get_value("cfg_stop_at_break")
        self.config.termination.return_after_break = dpg.get_value("cfg_return_after_break")
    
    def _update_ui_from_config(self):
        """Update UI controls from config values."""
        # This would set all UI values from self.config
        # Implementation similar to _read_config but in reverse
        pass
    
    def get_config(self) -> TestConfiguration:
        """Get current configuration."""
        self._read_config()
        return self.config
    
    def set_config(self, config: TestConfiguration):
        """Set configuration and update UI."""
        self.config = config
        self._update_ui_from_config()
