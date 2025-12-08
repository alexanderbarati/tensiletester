#!/usr/bin/env python3
"""
Test Configuration Dialog

Comprehensive dialog for configuring all test parameters.
Organized into tabs for easy navigation.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QTabWidget, QWidget, QPushButton, QLabel, QLineEdit, QTextEdit,
    QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QScrollArea, QFrame, QDateTimeEdit, QSplitter
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont

from config_model import (
    TestConfiguration, TestMetadata, SpecimenGeometry, EnvironmentalConditions,
    HardwareSettings, ZeroSettings, TestControlSettings, DataAcquisitionSettings,
    TerminationCriteria, RampStage, PRESET_CONFIGS,
    TestStandard, MaterialType, SpecimenShape, LoadCellCapacity,
    ExtensometerType, ControlMode, PreloadMethod, BreakDetection
)


class ConfigDialog(QDialog):
    """Test configuration dialog with tabbed interface."""
    
    def __init__(self, config: TestConfiguration = None, parent=None):
        super().__init__(parent)
        
        self.config = config if config else TestConfiguration()
        self.original_config = config  # Keep reference to original
        
        self.setWindowTitle("Test Configuration")
        self.setMinimumSize(900, 700)
        
        self._create_ui()
        self._load_config()
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Preset selector at top
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Load Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESET_CONFIGS.keys())
        self.preset_combo.currentTextChanged.connect(self._load_preset)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        
        # Save/Load buttons
        self.save_config_btn = QPushButton("Save Config...")
        self.save_config_btn.clicked.connect(self._save_config_file)
        preset_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("Load Config...")
        self.load_config_btn.clicked.connect(self._load_config_file)
        preset_layout.addWidget(self.load_config_btn)
        
        layout.addLayout(preset_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Create all tabs
        self.tabs.addTab(self._create_metadata_tab(), "📋 Test Info")
        self.tabs.addTab(self._create_specimen_tab(), "📐 Specimen")
        self.tabs.addTab(self._create_hardware_tab(), "🔧 Hardware")
        self.tabs.addTab(self._create_control_tab(), "⚙️ Control")
        self.tabs.addTab(self._create_acquisition_tab(), "📊 Acquisition")
        self.tabs.addTab(self._create_termination_tab(), "🛑 Termination")
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self._validate_config)
        btn_layout.addWidget(self.validate_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_config)
        self.apply_btn.setDefault(True)
        btn_layout.addWidget(self.apply_btn)
        
        layout.addLayout(btn_layout)
    
    # ========================================================================
    # Tab Creation Methods
    # ========================================================================
    
    def _create_metadata_tab(self) -> QWidget:
        """Create test metadata tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Test identification group
        id_group = QGroupBox("Test Identification")
        id_layout = QFormLayout(id_group)
        
        self.standard_combo = QComboBox()
        for std in TestStandard:
            self.standard_combo.addItem(std.value, std)
        id_layout.addRow("Test Standard:", self.standard_combo)
        
        self.sample_id_edit = QLineEdit()
        self.sample_id_edit.setPlaceholderText("e.g., SAMPLE-001")
        id_layout.addRow("Sample ID:", self.sample_id_edit)
        
        self.batch_id_edit = QLineEdit()
        self.batch_id_edit.setPlaceholderText("e.g., BATCH-2024-001")
        id_layout.addRow("Batch/Lot ID:", self.batch_id_edit)
        
        self.operator_edit = QLineEdit()
        id_layout.addRow("Operator:", self.operator_edit)
        
        self.customer_edit = QLineEdit()
        id_layout.addRow("Customer:", self.customer_edit)
        
        self.project_edit = QLineEdit()
        id_layout.addRow("Project:", self.project_edit)
        
        self.test_date_edit = QDateTimeEdit()
        self.test_date_edit.setDateTime(QDateTime.currentDateTime())
        self.test_date_edit.setCalendarPopup(True)
        id_layout.addRow("Test Date:", self.test_date_edit)
        
        layout.addWidget(id_group)
        
        # Material group
        material_group = QGroupBox("Material Information")
        material_layout = QFormLayout(material_group)
        
        self.material_type_combo = QComboBox()
        for mat in MaterialType:
            self.material_type_combo.addItem(mat.value, mat)
        material_layout.addRow("Material Type:", self.material_type_combo)
        
        self.material_name_edit = QLineEdit()
        self.material_name_edit.setPlaceholderText("e.g., ABS, Steel 304, HDPE")
        material_layout.addRow("Material Name:", self.material_name_edit)
        
        layout.addWidget(material_group)
        
        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Additional notes about the test...")
        notes_layout.addWidget(self.notes_edit)
        layout.addWidget(notes_group)
        
        layout.addStretch()
        return widget
    
    def _create_specimen_tab(self) -> QWidget:
        """Create specimen geometry tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Geometry group
        geom_group = QGroupBox("Specimen Geometry")
        geom_layout = QFormLayout(geom_group)
        
        self.shape_combo = QComboBox()
        for shape in SpecimenShape:
            self.shape_combo.addItem(shape.value, shape)
        self.shape_combo.currentIndexChanged.connect(self._update_geometry_fields)
        geom_layout.addRow("Cross-section Shape:", self.shape_combo)
        
        self.gauge_length_spin = QDoubleSpinBox()
        self.gauge_length_spin.setRange(1, 500)
        self.gauge_length_spin.setValue(50)
        self.gauge_length_spin.setSuffix(" mm")
        self.gauge_length_spin.setDecimals(2)
        geom_layout.addRow("Gauge Length:", self.gauge_length_spin)
        
        layout.addWidget(geom_group)
        
        # Dimensions group
        dim_group = QGroupBox("Dimensions")
        dim_layout = QGridLayout(dim_group)
        
        # Thickness
        dim_layout.addWidget(QLabel("Thickness:"), 0, 0)
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.01, 100)
        self.thickness_spin.setValue(4.0)
        self.thickness_spin.setSuffix(" mm")
        self.thickness_spin.setDecimals(3)
        self.thickness_spin.valueChanged.connect(self._calculate_area)
        dim_layout.addWidget(self.thickness_spin, 0, 1)
        
        # Width
        dim_layout.addWidget(QLabel("Width:"), 0, 2)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.01, 100)
        self.width_spin.setValue(10.0)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setDecimals(3)
        self.width_spin.valueChanged.connect(self._calculate_area)
        dim_layout.addWidget(self.width_spin, 0, 3)
        
        # Diameter (for circular)
        dim_layout.addWidget(QLabel("Diameter:"), 1, 0)
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(0.01, 100)
        self.diameter_spin.setValue(10.0)
        self.diameter_spin.setSuffix(" mm")
        self.diameter_spin.setDecimals(3)
        self.diameter_spin.valueChanged.connect(self._calculate_area)
        dim_layout.addWidget(self.diameter_spin, 1, 1)
        
        # Inner diameter (for tubular)
        dim_layout.addWidget(QLabel("Inner Diameter:"), 1, 2)
        self.inner_diameter_spin = QDoubleSpinBox()
        self.inner_diameter_spin.setRange(0, 100)
        self.inner_diameter_spin.setValue(0)
        self.inner_diameter_spin.setSuffix(" mm")
        self.inner_diameter_spin.setDecimals(3)
        self.inner_diameter_spin.valueChanged.connect(self._calculate_area)
        dim_layout.addWidget(self.inner_diameter_spin, 1, 3)
        
        layout.addWidget(dim_group)
        
        # Cross-sectional area
        area_group = QGroupBox("Cross-Sectional Area")
        area_layout = QHBoxLayout(area_group)
        
        self.auto_area_check = QCheckBox("Auto-calculate")
        self.auto_area_check.setChecked(True)
        self.auto_area_check.stateChanged.connect(self._toggle_auto_area)
        area_layout.addWidget(self.auto_area_check)
        
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(0.001, 10000)
        self.area_spin.setValue(40.0)
        self.area_spin.setSuffix(" mm²")
        self.area_spin.setDecimals(4)
        self.area_spin.setEnabled(False)
        area_layout.addWidget(self.area_spin)
        
        layout.addWidget(area_group)
        
        # Environmental conditions
        env_group = QGroupBox("Environmental Conditions")
        env_layout = QFormLayout(env_group)
        
        self.record_env_check = QCheckBox("Record environmental conditions")
        env_layout.addRow(self.record_env_check)
        
        temp_layout = QHBoxLayout()
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(-50, 200)
        self.temperature_spin.setValue(23.0)
        self.temperature_spin.setSuffix(" °C")
        temp_layout.addWidget(self.temperature_spin)
        temp_layout.addStretch()
        env_layout.addRow("Temperature:", temp_layout)
        
        humidity_layout = QHBoxLayout()
        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(0, 100)
        self.humidity_spin.setValue(50.0)
        self.humidity_spin.setSuffix(" %RH")
        humidity_layout.addWidget(self.humidity_spin)
        humidity_layout.addStretch()
        env_layout.addRow("Humidity:", humidity_layout)
        
        layout.addWidget(env_group)
        
        layout.addStretch()
        return widget
    
    def _create_hardware_tab(self) -> QWidget:
        """Create hardware settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sensors group
        sensor_group = QGroupBox("Sensors")
        sensor_layout = QFormLayout(sensor_group)
        
        self.load_cell_combo = QComboBox()
        for lc in LoadCellCapacity:
            self.load_cell_combo.addItem(lc.value, lc)
        self.load_cell_combo.setCurrentIndex(1)  # 500N default
        sensor_layout.addRow("Load Cell:", self.load_cell_combo)
        
        self.extensometer_combo = QComboBox()
        for ext in ExtensometerType:
            self.extensometer_combo.addItem(ext.value, ext)
        sensor_layout.addRow("Extensometer:", self.extensometer_combo)
        
        layout.addWidget(sensor_group)
        
        # Crosshead limits
        limits_group = QGroupBox("Crosshead Limits")
        limits_layout = QFormLayout(limits_group)
        
        self.upper_limit_spin = QDoubleSpinBox()
        self.upper_limit_spin.setRange(0, 1000)
        self.upper_limit_spin.setValue(150)
        self.upper_limit_spin.setSuffix(" mm")
        limits_layout.addRow("Upper Limit:", self.upper_limit_spin)
        
        self.lower_limit_spin = QDoubleSpinBox()
        self.lower_limit_spin.setRange(0, 1000)
        self.lower_limit_spin.setValue(0)
        self.lower_limit_spin.setSuffix(" mm")
        limits_layout.addRow("Lower Limit:", self.lower_limit_spin)
        
        layout.addWidget(limits_group)
        
        # Safety settings
        safety_group = QGroupBox("Safety Settings")
        safety_layout = QFormLayout(safety_group)
        
        self.hw_max_force_spin = QDoubleSpinBox()
        self.hw_max_force_spin.setRange(1, 100000)
        self.hw_max_force_spin.setValue(450)
        self.hw_max_force_spin.setSuffix(" N")
        safety_layout.addRow("Hardware Force Limit:", self.hw_max_force_spin)
        
        self.hw_max_ext_spin = QDoubleSpinBox()
        self.hw_max_ext_spin.setRange(1, 1000)
        self.hw_max_ext_spin.setValue(100)
        self.hw_max_ext_spin.setSuffix(" mm")
        safety_layout.addRow("Hardware Extension Limit:", self.hw_max_ext_spin)
        
        self.emergency_speed_spin = QDoubleSpinBox()
        self.emergency_speed_spin.setRange(1, 500)
        self.emergency_speed_spin.setValue(50)
        self.emergency_speed_spin.setSuffix(" mm/min")
        safety_layout.addRow("Emergency Return Speed:", self.emergency_speed_spin)
        
        layout.addWidget(safety_group)
        
        # Preload settings
        preload_group = QGroupBox("Preload Settings")
        preload_layout = QFormLayout(preload_group)
        
        self.preload_method_combo = QComboBox()
        for pm in PreloadMethod:
            self.preload_method_combo.addItem(pm.value, pm)
        self.preload_method_combo.currentIndexChanged.connect(self._update_preload_unit)
        preload_layout.addRow("Preload Method:", self.preload_method_combo)
        
        self.preload_value_spin = QDoubleSpinBox()
        self.preload_value_spin.setRange(0, 1000)
        self.preload_value_spin.setValue(0.5)
        self.preload_value_spin.setSuffix(" N")
        self.preload_value_spin.setDecimals(2)
        preload_layout.addRow("Preload Value:", self.preload_value_spin)
        
        self.preload_speed_spin = QDoubleSpinBox()
        self.preload_speed_spin.setRange(0.1, 100)
        self.preload_speed_spin.setValue(5)
        self.preload_speed_spin.setSuffix(" mm/min")
        preload_layout.addRow("Preload Speed:", self.preload_speed_spin)
        
        layout.addWidget(preload_group)
        
        # Zeroing settings
        zero_group = QGroupBox("Zeroing")
        zero_layout = QVBoxLayout(zero_group)
        
        self.zero_force_check = QCheckBox("Zero force before test")
        self.zero_force_check.setChecked(True)
        zero_layout.addWidget(self.zero_force_check)
        
        self.zero_ext_check = QCheckBox("Zero extension before test")
        self.zero_ext_check.setChecked(True)
        zero_layout.addWidget(self.zero_ext_check)
        
        self.zero_extensometer_check = QCheckBox("Zero extensometer before test")
        self.zero_extensometer_check.setChecked(True)
        zero_layout.addWidget(self.zero_extensometer_check)
        
        self.zero_after_preload_check = QCheckBox("Zero strain after preload")
        zero_layout.addWidget(self.zero_after_preload_check)
        
        layout.addWidget(zero_group)
        
        layout.addStretch()
        return widget
    
    def _create_control_tab(self) -> QWidget:
        """Create test control settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Control mode
        mode_group = QGroupBox("Control Mode")
        mode_layout = QFormLayout(mode_group)
        
        self.control_mode_combo = QComboBox()
        for mode in ControlMode:
            self.control_mode_combo.addItem(mode.value, mode)
        self.control_mode_combo.currentIndexChanged.connect(self._update_speed_fields)
        mode_layout.addRow("Primary Control:", self.control_mode_combo)
        
        layout.addWidget(mode_group)
        
        # Speed settings
        speed_group = QGroupBox("Speed Settings")
        speed_layout = QGridLayout(speed_group)
        
        speed_layout.addWidget(QLabel("Test Speed:"), 0, 0)
        self.test_speed_spin = QDoubleSpinBox()
        self.test_speed_spin.setRange(0.001, 1000)
        self.test_speed_spin.setValue(2.0)
        self.test_speed_spin.setSuffix(" mm/min")
        self.test_speed_spin.setDecimals(3)
        speed_layout.addWidget(self.test_speed_spin, 0, 1)
        
        speed_layout.addWidget(QLabel("Strain Rate:"), 1, 0)
        self.strain_rate_spin = QDoubleSpinBox()
        self.strain_rate_spin.setRange(0.00001, 10)
        self.strain_rate_spin.setValue(0.001)
        self.strain_rate_spin.setSuffix(" 1/s")
        self.strain_rate_spin.setDecimals(5)
        speed_layout.addWidget(self.strain_rate_spin, 1, 1)
        
        speed_layout.addWidget(QLabel("Load Rate:"), 2, 0)
        self.load_rate_spin = QDoubleSpinBox()
        self.load_rate_spin.setRange(0.01, 10000)
        self.load_rate_spin.setValue(10)
        self.load_rate_spin.setSuffix(" N/s")
        speed_layout.addWidget(self.load_rate_spin, 2, 1)
        
        speed_layout.addWidget(QLabel("Approach Speed:"), 3, 0)
        self.approach_speed_spin = QDoubleSpinBox()
        self.approach_speed_spin.setRange(0.1, 100)
        self.approach_speed_spin.setValue(10)
        self.approach_speed_spin.setSuffix(" mm/min")
        speed_layout.addWidget(self.approach_speed_spin, 3, 1)
        
        layout.addWidget(speed_group)
        
        # Return settings
        return_group = QGroupBox("Return Settings")
        return_layout = QFormLayout(return_group)
        
        self.return_after_break_check = QCheckBox("Return to start after break")
        self.return_after_break_check.setChecked(True)
        return_layout.addRow(self.return_after_break_check)
        
        self.return_speed_spin = QDoubleSpinBox()
        self.return_speed_spin.setRange(1, 500)
        self.return_speed_spin.setValue(50)
        self.return_speed_spin.setSuffix(" mm/min")
        return_layout.addRow("Return Speed:", self.return_speed_spin)
        
        self.return_position_spin = QDoubleSpinBox()
        self.return_position_spin.setRange(0, 500)
        self.return_position_spin.setValue(0)
        self.return_position_spin.setSuffix(" mm")
        return_layout.addRow("Return Position:", self.return_position_spin)
        
        layout.addWidget(return_group)
        
        # Multi-stage profile
        stage_group = QGroupBox("Multi-Stage Test Profile")
        stage_layout = QVBoxLayout(stage_group)
        
        self.use_multistage_check = QCheckBox("Enable multi-stage testing")
        self.use_multistage_check.stateChanged.connect(self._toggle_stages)
        stage_layout.addWidget(self.use_multistage_check)
        
        # Stage table
        self.stage_table = QTableWidget()
        self.stage_table.setColumnCount(5)
        self.stage_table.setHorizontalHeaderLabels([
            "Stage Name", "Control Mode", "Target", "Speed", "Hold (s)"
        ])
        self.stage_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stage_table.setEnabled(False)
        stage_layout.addWidget(self.stage_table)
        
        stage_btn_layout = QHBoxLayout()
        self.add_stage_btn = QPushButton("Add Stage")
        self.add_stage_btn.clicked.connect(self._add_stage)
        self.add_stage_btn.setEnabled(False)
        stage_btn_layout.addWidget(self.add_stage_btn)
        
        self.remove_stage_btn = QPushButton("Remove Stage")
        self.remove_stage_btn.clicked.connect(self._remove_stage)
        self.remove_stage_btn.setEnabled(False)
        stage_btn_layout.addWidget(self.remove_stage_btn)
        
        stage_btn_layout.addStretch()
        stage_layout.addLayout(stage_btn_layout)
        
        layout.addWidget(stage_group)
        
        layout.addStretch()
        return widget
    
    def _create_acquisition_tab(self) -> QWidget:
        """Create data acquisition settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sampling
        sample_group = QGroupBox("Sampling")
        sample_layout = QFormLayout(sample_group)
        
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(1, 1000)
        self.sample_rate_spin.setValue(10)
        self.sample_rate_spin.setSuffix(" Hz")
        sample_layout.addRow("Sampling Rate:", self.sample_rate_spin)
        
        layout.addWidget(sample_group)
        
        # Filtering
        filter_group = QGroupBox("Digital Filtering")
        filter_layout = QFormLayout(filter_group)
        
        self.apply_filter_check = QCheckBox("Apply digital filter")
        filter_layout.addRow(self.apply_filter_check)
        
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["Moving Average", "Median", "Butterworth"])
        filter_layout.addRow("Filter Type:", self.filter_type_combo)
        
        self.filter_window_spin = QSpinBox()
        self.filter_window_spin.setRange(3, 51)
        self.filter_window_spin.setValue(5)
        self.filter_window_spin.setSuffix(" samples")
        filter_layout.addRow("Filter Window:", self.filter_window_spin)
        
        layout.addWidget(filter_group)
        
        # Channels to record
        channels_group = QGroupBox("Channels to Record")
        channels_layout = QGridLayout(channels_group)
        
        self.record_force_check = QCheckBox("Force")
        self.record_force_check.setChecked(True)
        channels_layout.addWidget(self.record_force_check, 0, 0)
        
        self.record_ext_check = QCheckBox("Extension")
        self.record_ext_check.setChecked(True)
        channels_layout.addWidget(self.record_ext_check, 0, 1)
        
        self.record_strain_check = QCheckBox("Strain")
        self.record_strain_check.setChecked(True)
        channels_layout.addWidget(self.record_strain_check, 0, 2)
        
        self.record_disp_check = QCheckBox("Displacement")
        self.record_disp_check.setChecked(True)
        channels_layout.addWidget(self.record_disp_check, 1, 0)
        
        self.record_time_check = QCheckBox("Time")
        self.record_time_check.setChecked(True)
        channels_layout.addWidget(self.record_time_check, 1, 1)
        
        self.record_temp_check = QCheckBox("Temperature")
        channels_layout.addWidget(self.record_temp_check, 1, 2)
        
        layout.addWidget(channels_group)
        
        # Calculated values
        calc_group = QGroupBox("Calculated Values")
        calc_layout = QVBoxLayout(calc_group)
        
        self.calc_stress_check = QCheckBox("Calculate Stress (σ = F / A)")
        self.calc_stress_check.setChecked(True)
        calc_layout.addWidget(self.calc_stress_check)
        
        self.calc_strain_check = QCheckBox("Calculate Strain (ε = ΔL / L₀)")
        self.calc_strain_check.setChecked(True)
        calc_layout.addWidget(self.calc_strain_check)
        
        self.calc_modulus_check = QCheckBox("Calculate Modulus (E = Δσ / Δε)")
        self.calc_modulus_check.setChecked(True)
        calc_layout.addWidget(self.calc_modulus_check)
        
        layout.addWidget(calc_group)
        
        layout.addStretch()
        return widget
    
    def _create_termination_tab(self) -> QWidget:
        """Create termination criteria tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Break detection
        break_group = QGroupBox("Break Detection")
        break_layout = QFormLayout(break_group)
        
        self.enable_break_check = QCheckBox("Enable break detection")
        self.enable_break_check.setChecked(True)
        break_layout.addRow(self.enable_break_check)
        
        self.break_method_combo = QComboBox()
        for bd in BreakDetection:
            self.break_method_combo.addItem(bd.value, bd)
        self.break_method_combo.currentIndexChanged.connect(self._update_break_fields)
        break_layout.addRow("Detection Method:", self.break_method_combo)
        
        self.force_drop_percent_spin = QDoubleSpinBox()
        self.force_drop_percent_spin.setRange(1, 100)
        self.force_drop_percent_spin.setValue(50)
        self.force_drop_percent_spin.setSuffix(" %")
        break_layout.addRow("Force Drop:", self.force_drop_percent_spin)
        
        self.force_drop_abs_spin = QDoubleSpinBox()
        self.force_drop_abs_spin.setRange(0.1, 10000)
        self.force_drop_abs_spin.setValue(10)
        self.force_drop_abs_spin.setSuffix(" N")
        break_layout.addRow("Force Drop (abs):", self.force_drop_abs_spin)
        
        self.force_threshold_spin = QDoubleSpinBox()
        self.force_threshold_spin.setRange(0.01, 1000)
        self.force_threshold_spin.setValue(1)
        self.force_threshold_spin.setSuffix(" N")
        break_layout.addRow("Force Threshold:", self.force_threshold_spin)
        
        layout.addWidget(break_group)
        
        # Force limit
        force_group = QGroupBox("Force Limit")
        force_layout = QHBoxLayout(force_group)
        
        self.enable_max_force_check = QCheckBox("Enable")
        self.enable_max_force_check.setChecked(True)
        force_layout.addWidget(self.enable_max_force_check)
        
        force_layout.addWidget(QLabel("Max Force:"))
        self.term_max_force_spin = QDoubleSpinBox()
        self.term_max_force_spin.setRange(1, 100000)
        self.term_max_force_spin.setValue(450)
        self.term_max_force_spin.setSuffix(" N")
        force_layout.addWidget(self.term_max_force_spin)
        force_layout.addStretch()
        
        layout.addWidget(force_group)
        
        # Extension limit
        ext_group = QGroupBox("Extension Limit")
        ext_layout = QHBoxLayout(ext_group)
        
        self.enable_max_ext_check = QCheckBox("Enable")
        self.enable_max_ext_check.setChecked(True)
        ext_layout.addWidget(self.enable_max_ext_check)
        
        ext_layout.addWidget(QLabel("Max Extension:"))
        self.term_max_ext_spin = QDoubleSpinBox()
        self.term_max_ext_spin.setRange(1, 1000)
        self.term_max_ext_spin.setValue(100)
        self.term_max_ext_spin.setSuffix(" mm")
        ext_layout.addWidget(self.term_max_ext_spin)
        ext_layout.addStretch()
        
        layout.addWidget(ext_group)
        
        # Strain limit
        strain_group = QGroupBox("Strain Limit")
        strain_layout = QHBoxLayout(strain_group)
        
        self.enable_max_strain_check = QCheckBox("Enable")
        strain_layout.addWidget(self.enable_max_strain_check)
        
        strain_layout.addWidget(QLabel("Max Strain:"))
        self.term_max_strain_spin = QDoubleSpinBox()
        self.term_max_strain_spin.setRange(1, 10000)
        self.term_max_strain_spin.setValue(500)
        self.term_max_strain_spin.setSuffix(" %")
        strain_layout.addWidget(self.term_max_strain_spin)
        strain_layout.addStretch()
        
        layout.addWidget(strain_group)
        
        # Time limit
        time_group = QGroupBox("Time Limit")
        time_layout = QHBoxLayout(time_group)
        
        self.enable_max_time_check = QCheckBox("Enable")
        time_layout.addWidget(self.enable_max_time_check)
        
        time_layout.addWidget(QLabel("Max Time:"))
        self.term_max_time_spin = QDoubleSpinBox()
        self.term_max_time_spin.setRange(1, 86400)
        self.term_max_time_spin.setValue(3600)
        self.term_max_time_spin.setSuffix(" s")
        time_layout.addWidget(self.term_max_time_spin)
        time_layout.addStretch()
        
        layout.addWidget(time_group)
        
        layout.addStretch()
        return widget
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def _update_geometry_fields(self):
        """Update geometry input fields based on shape."""
        shape = self.shape_combo.currentData()
        
        is_rect = shape in [SpecimenShape.RECTANGULAR, SpecimenShape.DOG_BONE]
        is_circular = shape == SpecimenShape.CIRCULAR
        is_tubular = shape == SpecimenShape.TUBULAR
        
        self.thickness_spin.setEnabled(is_rect)
        self.width_spin.setEnabled(is_rect)
        self.diameter_spin.setEnabled(is_circular or is_tubular)
        self.inner_diameter_spin.setEnabled(is_tubular)
        
        self._calculate_area()
    
    def _calculate_area(self):
        """Calculate and display cross-sectional area."""
        if not self.auto_area_check.isChecked():
            return
        
        shape = self.shape_combo.currentData()
        import math
        
        if shape in [SpecimenShape.RECTANGULAR, SpecimenShape.DOG_BONE]:
            area = self.thickness_spin.value() * self.width_spin.value()
        elif shape == SpecimenShape.CIRCULAR:
            area = math.pi * (self.diameter_spin.value() / 2) ** 2
        elif shape == SpecimenShape.TUBULAR:
            outer = math.pi * (self.diameter_spin.value() / 2) ** 2
            inner = math.pi * (self.inner_diameter_spin.value() / 2) ** 2
            area = outer - inner
        else:
            area = self.area_spin.value()
        
        self.area_spin.setValue(area)
    
    def _toggle_auto_area(self, state):
        """Toggle auto area calculation."""
        self.area_spin.setEnabled(not state)
        if state:
            self._calculate_area()
    
    def _update_preload_unit(self):
        """Update preload value unit based on method."""
        method = self.preload_method_combo.currentData()
        
        if method == PreloadMethod.FORCE:
            self.preload_value_spin.setSuffix(" N")
        elif method == PreloadMethod.STRESS:
            self.preload_value_spin.setSuffix(" MPa")
        elif method == PreloadMethod.EXTENSION:
            self.preload_value_spin.setSuffix(" mm")
        else:
            self.preload_value_spin.setSuffix("")
    
    def _update_speed_fields(self):
        """Update speed field availability based on control mode."""
        mode = self.control_mode_combo.currentData()
        
        self.test_speed_spin.setEnabled(mode == ControlMode.DISPLACEMENT)
        self.strain_rate_spin.setEnabled(mode == ControlMode.STRAIN)
        self.load_rate_spin.setEnabled(mode in [ControlMode.LOAD, ControlMode.STRESS])
    
    def _toggle_stages(self, state):
        """Toggle multi-stage profile controls."""
        enabled = bool(state)
        self.stage_table.setEnabled(enabled)
        self.add_stage_btn.setEnabled(enabled)
        self.remove_stage_btn.setEnabled(enabled)
    
    def _add_stage(self):
        """Add a new stage to the table."""
        row = self.stage_table.rowCount()
        self.stage_table.insertRow(row)
        
        # Stage name
        self.stage_table.setItem(row, 0, QTableWidgetItem(f"Stage {row + 1}"))
        
        # Control mode combo
        mode_combo = QComboBox()
        for mode in ControlMode:
            mode_combo.addItem(mode.value, mode)
        self.stage_table.setCellWidget(row, 1, mode_combo)
        
        # Target, Speed, Hold
        self.stage_table.setItem(row, 2, QTableWidgetItem("100"))
        self.stage_table.setItem(row, 3, QTableWidgetItem("2"))
        self.stage_table.setItem(row, 4, QTableWidgetItem("0"))
    
    def _remove_stage(self):
        """Remove selected stage from table."""
        row = self.stage_table.currentRow()
        if row >= 0:
            self.stage_table.removeRow(row)
    
    def _update_break_fields(self):
        """Update break detection field visibility."""
        method = self.break_method_combo.currentData()
        
        self.force_drop_percent_spin.setEnabled(method == BreakDetection.FORCE_DROP_PERCENT)
        self.force_drop_abs_spin.setEnabled(method == BreakDetection.FORCE_DROP_ABSOLUTE)
        self.force_threshold_spin.setEnabled(method == BreakDetection.FORCE_THRESHOLD)
    
    def _load_preset(self, preset_name: str):
        """Load a preset configuration."""
        if preset_name in PRESET_CONFIGS:
            self.config = PRESET_CONFIGS[preset_name]
            self._load_config()
    
    def _save_config_file(self):
        """Save configuration to file."""
        self._save_to_config()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                self.config.save_to_file(filename)
                QMessageBox.information(self, "Saved", f"Configuration saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def _load_config_file(self):
        """Load configuration from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                self.config = TestConfiguration.load_from_file(filename)
                self._load_config()
                QMessageBox.information(self, "Loaded", f"Configuration loaded from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")
    
    # ========================================================================
    # Config Load/Save
    # ========================================================================
    
    def _load_config(self):
        """Load configuration into UI fields."""
        c = self.config
        
        # Metadata
        self._set_combo_by_data(self.standard_combo, c.metadata.test_standard)
        self.sample_id_edit.setText(c.metadata.sample_id)
        self.batch_id_edit.setText(c.metadata.batch_id)
        self.operator_edit.setText(c.metadata.operator_name)
        self.customer_edit.setText(c.metadata.customer_name)
        self.project_edit.setText(c.metadata.project_name)
        self._set_combo_by_data(self.material_type_combo, c.metadata.material_type)
        self.material_name_edit.setText(c.metadata.material_name)
        self.notes_edit.setPlainText(c.metadata.notes)
        
        # Specimen
        self._set_combo_by_data(self.shape_combo, c.specimen.shape)
        self.gauge_length_spin.setValue(c.specimen.gauge_length)
        self.thickness_spin.setValue(c.specimen.thickness)
        self.width_spin.setValue(c.specimen.width)
        self.diameter_spin.setValue(c.specimen.diameter)
        self.inner_diameter_spin.setValue(c.specimen.inner_diameter)
        self.auto_area_check.setChecked(c.specimen.auto_calculate_area)
        self.area_spin.setValue(c.specimen.cross_section_area)
        
        # Environment
        self.record_env_check.setChecked(c.environment.record_conditions)
        self.temperature_spin.setValue(c.environment.temperature)
        self.humidity_spin.setValue(c.environment.humidity)
        
        # Hardware
        self._set_combo_by_data(self.load_cell_combo, c.hardware.load_cell)
        self._set_combo_by_data(self.extensometer_combo, c.hardware.extensometer)
        self.upper_limit_spin.setValue(c.hardware.upper_limit)
        self.lower_limit_spin.setValue(c.hardware.lower_limit)
        self.hw_max_force_spin.setValue(c.hardware.max_force_limit)
        self.hw_max_ext_spin.setValue(c.hardware.max_extension_limit)
        self.emergency_speed_spin.setValue(c.hardware.emergency_return_speed)
        self._set_combo_by_data(self.preload_method_combo, c.hardware.preload_method)
        self.preload_value_spin.setValue(c.hardware.preload_value)
        self.preload_speed_spin.setValue(c.hardware.preload_speed)
        
        # Zeroing
        self.zero_force_check.setChecked(c.zeroing.zero_force_before_test)
        self.zero_ext_check.setChecked(c.zeroing.zero_extension_before_test)
        self.zero_extensometer_check.setChecked(c.zeroing.zero_extensometer_before_test)
        self.zero_after_preload_check.setChecked(c.zeroing.zero_after_preload)
        
        # Control
        self._set_combo_by_data(self.control_mode_combo, c.control.control_mode)
        self.test_speed_spin.setValue(c.control.test_speed)
        self.strain_rate_spin.setValue(c.control.strain_rate)
        self.load_rate_spin.setValue(c.control.load_rate)
        self.approach_speed_spin.setValue(c.control.approach_speed)
        self.return_after_break_check.setChecked(c.control.return_after_break)
        self.return_speed_spin.setValue(c.control.return_speed)
        self.return_position_spin.setValue(c.control.return_position)
        self.use_multistage_check.setChecked(c.control.use_multi_stage)
        
        # Load stages
        self.stage_table.setRowCount(0)
        for stage in c.control.stages:
            self._add_stage()
            row = self.stage_table.rowCount() - 1
            self.stage_table.item(row, 0).setText(stage.name)
            combo = self.stage_table.cellWidget(row, 1)
            self._set_combo_by_data(combo, stage.control_mode)
            self.stage_table.item(row, 2).setText(str(stage.target_value))
            self.stage_table.item(row, 3).setText(str(stage.speed))
            self.stage_table.item(row, 4).setText(str(stage.hold_time))
        
        # Acquisition
        self.sample_rate_spin.setValue(c.acquisition.sampling_rate)
        self.apply_filter_check.setChecked(c.acquisition.apply_filter)
        self.filter_type_combo.setCurrentText(c.acquisition.filter_type)
        self.filter_window_spin.setValue(c.acquisition.filter_window)
        self.record_force_check.setChecked(c.acquisition.record_force)
        self.record_ext_check.setChecked(c.acquisition.record_extension)
        self.record_strain_check.setChecked(c.acquisition.record_strain)
        self.record_disp_check.setChecked(c.acquisition.record_displacement)
        self.record_time_check.setChecked(c.acquisition.record_time)
        self.record_temp_check.setChecked(c.acquisition.record_temperature)
        self.calc_stress_check.setChecked(c.acquisition.calculate_stress)
        self.calc_strain_check.setChecked(c.acquisition.calculate_strain)
        self.calc_modulus_check.setChecked(c.acquisition.calculate_modulus)
        
        # Termination
        self.enable_break_check.setChecked(c.termination.enable_break_detection)
        self._set_combo_by_data(self.break_method_combo, c.termination.break_detection)
        self.force_drop_percent_spin.setValue(c.termination.force_drop_percent)
        self.force_drop_abs_spin.setValue(c.termination.force_drop_absolute)
        self.force_threshold_spin.setValue(c.termination.force_threshold)
        self.enable_max_force_check.setChecked(c.termination.enable_max_force)
        self.term_max_force_spin.setValue(c.termination.max_force)
        self.enable_max_ext_check.setChecked(c.termination.enable_max_extension)
        self.term_max_ext_spin.setValue(c.termination.max_extension)
        self.enable_max_strain_check.setChecked(c.termination.enable_max_strain)
        self.term_max_strain_spin.setValue(c.termination.max_strain)
        self.enable_max_time_check.setChecked(c.termination.enable_max_time)
        self.term_max_time_spin.setValue(c.termination.max_time)
        
        # Update dependent fields
        self._update_geometry_fields()
        self._update_preload_unit()
        self._update_speed_fields()
        self._update_break_fields()
        self._toggle_stages(c.control.use_multi_stage)
    
    def _save_to_config(self):
        """Save UI fields to configuration object."""
        c = self.config
        
        # Metadata
        c.metadata.test_standard = self.standard_combo.currentData()
        c.metadata.sample_id = self.sample_id_edit.text()
        c.metadata.batch_id = self.batch_id_edit.text()
        c.metadata.operator_name = self.operator_edit.text()
        c.metadata.customer_name = self.customer_edit.text()
        c.metadata.project_name = self.project_edit.text()
        c.metadata.material_type = self.material_type_combo.currentData()
        c.metadata.material_name = self.material_name_edit.text()
        c.metadata.notes = self.notes_edit.toPlainText()
        c.metadata.test_date = self.test_date_edit.dateTime().toPyDateTime()
        
        # Specimen
        c.specimen.shape = self.shape_combo.currentData()
        c.specimen.gauge_length = self.gauge_length_spin.value()
        c.specimen.thickness = self.thickness_spin.value()
        c.specimen.width = self.width_spin.value()
        c.specimen.diameter = self.diameter_spin.value()
        c.specimen.inner_diameter = self.inner_diameter_spin.value()
        c.specimen.auto_calculate_area = self.auto_area_check.isChecked()
        c.specimen.cross_section_area = self.area_spin.value()
        
        # Environment
        c.environment.record_conditions = self.record_env_check.isChecked()
        c.environment.temperature = self.temperature_spin.value()
        c.environment.humidity = self.humidity_spin.value()
        
        # Hardware
        c.hardware.load_cell = self.load_cell_combo.currentData()
        c.hardware.extensometer = self.extensometer_combo.currentData()
        c.hardware.upper_limit = self.upper_limit_spin.value()
        c.hardware.lower_limit = self.lower_limit_spin.value()
        c.hardware.max_force_limit = self.hw_max_force_spin.value()
        c.hardware.max_extension_limit = self.hw_max_ext_spin.value()
        c.hardware.emergency_return_speed = self.emergency_speed_spin.value()
        c.hardware.preload_method = self.preload_method_combo.currentData()
        c.hardware.preload_value = self.preload_value_spin.value()
        c.hardware.preload_speed = self.preload_speed_spin.value()
        
        # Zeroing
        c.zeroing.zero_force_before_test = self.zero_force_check.isChecked()
        c.zeroing.zero_extension_before_test = self.zero_ext_check.isChecked()
        c.zeroing.zero_extensometer_before_test = self.zero_extensometer_check.isChecked()
        c.zeroing.zero_after_preload = self.zero_after_preload_check.isChecked()
        
        # Control
        c.control.control_mode = self.control_mode_combo.currentData()
        c.control.test_speed = self.test_speed_spin.value()
        c.control.strain_rate = self.strain_rate_spin.value()
        c.control.load_rate = self.load_rate_spin.value()
        c.control.approach_speed = self.approach_speed_spin.value()
        c.control.return_after_break = self.return_after_break_check.isChecked()
        c.control.return_speed = self.return_speed_spin.value()
        c.control.return_position = self.return_position_spin.value()
        c.control.use_multi_stage = self.use_multistage_check.isChecked()
        
        # Save stages
        c.control.stages = []
        for row in range(self.stage_table.rowCount()):
            stage = RampStage()
            stage.name = self.stage_table.item(row, 0).text()
            combo = self.stage_table.cellWidget(row, 1)
            stage.control_mode = combo.currentData() if combo else ControlMode.DISPLACEMENT
            try:
                stage.target_value = float(self.stage_table.item(row, 2).text())
                stage.speed = float(self.stage_table.item(row, 3).text())
                stage.hold_time = float(self.stage_table.item(row, 4).text())
            except:
                pass
            c.control.stages.append(stage)
        
        # Acquisition
        c.acquisition.sampling_rate = self.sample_rate_spin.value()
        c.acquisition.apply_filter = self.apply_filter_check.isChecked()
        c.acquisition.filter_type = self.filter_type_combo.currentText()
        c.acquisition.filter_window = self.filter_window_spin.value()
        c.acquisition.record_force = self.record_force_check.isChecked()
        c.acquisition.record_extension = self.record_ext_check.isChecked()
        c.acquisition.record_strain = self.record_strain_check.isChecked()
        c.acquisition.record_displacement = self.record_disp_check.isChecked()
        c.acquisition.record_time = self.record_time_check.isChecked()
        c.acquisition.record_temperature = self.record_temp_check.isChecked()
        c.acquisition.calculate_stress = self.calc_stress_check.isChecked()
        c.acquisition.calculate_strain = self.calc_strain_check.isChecked()
        c.acquisition.calculate_modulus = self.calc_modulus_check.isChecked()
        
        # Termination
        c.termination.enable_break_detection = self.enable_break_check.isChecked()
        c.termination.break_detection = self.break_method_combo.currentData()
        c.termination.force_drop_percent = self.force_drop_percent_spin.value()
        c.termination.force_drop_absolute = self.force_drop_abs_spin.value()
        c.termination.force_threshold = self.force_threshold_spin.value()
        c.termination.enable_max_force = self.enable_max_force_check.isChecked()
        c.termination.max_force = self.term_max_force_spin.value()
        c.termination.enable_max_extension = self.enable_max_ext_check.isChecked()
        c.termination.max_extension = self.term_max_ext_spin.value()
        c.termination.enable_max_strain = self.enable_max_strain_check.isChecked()
        c.termination.max_strain = self.term_max_strain_spin.value()
        c.termination.enable_max_time = self.enable_max_time_check.isChecked()
        c.termination.max_time = self.term_max_time_spin.value()
    
    def _set_combo_by_data(self, combo: QComboBox, data):
        """Set combo box selection by data value."""
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                combo.setCurrentIndex(i)
                return
    
    def _validate_config(self):
        """Validate configuration and show results."""
        self._save_to_config()
        errors = self.config.validate()
        
        if errors:
            QMessageBox.warning(
                self, "Validation Errors",
                "Configuration has the following issues:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
        else:
            QMessageBox.information(self, "Validation", "Configuration is valid!")
    
    def _apply_config(self):
        """Apply configuration and close dialog."""
        self._save_to_config()
        errors = self.config.validate()
        
        if errors:
            result = QMessageBox.question(
                self, "Validation Warnings",
                "Configuration has issues:\n\n" + "\n".join(f"• {e}" for e in errors) +
                "\n\nApply anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return
        
        self.accept()
    
    def get_config(self) -> TestConfiguration:
        """Get the configured test configuration."""
        return self.config
