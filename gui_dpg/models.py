#!/usr/bin/env python3
"""
Data Models for Professional Tensile Testing System

Complete data structures for test configuration, execution, and results
following ISO 527, ASTM D638, DIN EN ISO 6892-1 standards.

Author: DIY Tensile Tester Project
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ============== Enumerations ==============

class TestStandard(Enum):
    """Supported test standards."""
    ISO_527 = "ISO 527 - Plastics"
    ASTM_D638 = "ASTM D638 - Plastics"
    DIN_EN_ISO_6892 = "DIN EN ISO 6892-1 - Metals"
    ASTM_E8 = "ASTM E8 - Metals"
    ISO_6892 = "ISO 6892-1 - Metals"
    CUSTOM = "Custom"


class MaterialType(Enum):
    """Material categories."""
    POLYMER = "Polymer"
    METAL = "Metal"
    COMPOSITE = "Composite"
    PAPER = "Paper/Cardboard"
    TEXTILE = "Textile"
    RUBBER = "Rubber/Elastomer"
    CERAMIC = "Ceramic"
    OTHER = "Other"


class ControlMode(Enum):
    """Test control modes."""
    DISPLACEMENT = "Displacement Control"
    STRAIN = "Strain Control"
    LOAD = "Load Control"
    STRESS = "Stress Control"


class ExtensometerType(Enum):
    """Extensometer types."""
    NONE = "None (Crosshead)"
    CLIP_ON = "Clip-on"
    VIDEO = "Video/Optical"
    LASER = "Laser"
    CONTACT = "Contact"


class LoadCellRange(Enum):
    """Load cell capacity options."""
    LC_100N = "100 N"
    LC_500N = "500 N"
    LC_1KN = "1 kN"
    LC_5KN = "5 kN"
    LC_10KN = "10 kN"
    LC_20KN = "20 kN"
    LC_50KN = "50 kN"
    LC_100KN = "100 kN"


class FailureType(Enum):
    """Failure classification."""
    BRITTLE = "Brittle"
    DUCTILE = "Ductile"
    NECKING = "Necking"
    SHEAR = "Shear"
    DELAMINATION = "Delamination"
    GRIP_FAILURE = "Grip Failure"
    NO_BREAK = "No Break"
    UNKNOWN = "Unknown"


class BreakLocation(Enum):
    """Break location classification."""
    MIDDLE = "Middle (Gauge)"
    NEAR_GRIP_TOP = "Near Top Grip"
    NEAR_GRIP_BOTTOM = "Near Bottom Grip"
    AT_GRIP = "At Grip"
    OUTSIDE_GAUGE = "Outside Gauge"
    UNKNOWN = "Unknown"


class TestStage(Enum):
    """Current test stage."""
    IDLE = "Idle"
    PRELOAD = "Preload"
    ZEROING = "Zeroing"
    APPROACH = "Approach"
    TESTING = "Testing"
    HOLD = "Hold"
    RETURN = "Return"
    COMPLETE = "Complete"
    ERROR = "Error"
    EMERGENCY = "Emergency Stop"


# ============== Configuration Data Classes ==============

@dataclass
class TestMetadata:
    """Test identification and metadata."""
    # Identification
    test_id: str = ""
    sample_id: str = ""
    batch_id: str = ""
    lot_number: str = ""
    
    # Personnel
    operator_name: str = ""
    customer_name: str = ""
    project_name: str = ""
    
    # Standard
    test_standard: TestStandard = TestStandard.ISO_527
    material_type: MaterialType = MaterialType.POLYMER
    material_name: str = ""
    material_grade: str = ""
    
    # Environment
    temperature: float = 23.0  # °C
    humidity: float = 50.0  # %RH
    
    # Timestamps
    test_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    test_time: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    
    # Notes
    notes: str = ""


@dataclass
class SpecimenConfig:
    """Specimen dimensions and geometry."""
    # Dimensions
    gauge_length: float = 50.0  # mm
    thickness: float = 4.0  # mm
    width: float = 10.0  # mm
    
    # Calculated or manual
    cross_section_area: float = 40.0  # mm² (auto-calculated: thickness * width)
    cross_section_manual: bool = False  # If True, use manual value
    
    # Specimen type
    specimen_type: str = "Type 1A"  # ISO 527 specimen types
    parallel_length: float = 80.0  # mm
    total_length: float = 150.0  # mm
    
    # Grip
    grip_distance: float = 115.0  # mm
    
    def calculate_area(self):
        """Calculate cross-sectional area."""
        if not self.cross_section_manual:
            self.cross_section_area = self.thickness * self.width
        return self.cross_section_area


@dataclass
class MachineConfig:
    """Machine and hardware settings."""
    # Load cell
    load_cell_range: LoadCellRange = LoadCellRange.LC_500N
    load_cell_serial: str = ""
    load_cell_calibration_date: str = ""
    
    # Extensometer
    extensometer_type: ExtensometerType = ExtensometerType.NONE
    extensometer_gauge: float = 50.0  # mm
    extensometer_serial: str = ""
    
    # Travel limits
    upper_limit: float = 150.0  # mm
    lower_limit: float = 0.0  # mm
    
    # Safety
    force_limit: float = 450.0  # N
    extension_limit: float = 100.0  # mm
    emergency_stop_enabled: bool = True
    
    # Zeroing
    zero_force_on_start: bool = True
    zero_extension_on_start: bool = True
    zero_extensometer_on_start: bool = True


@dataclass
class TestControlConfig:
    """Test control parameters."""
    # Control mode
    control_mode: ControlMode = ControlMode.DISPLACEMENT
    
    # Speed settings
    test_speed: float = 1.0  # mm/min for displacement
    strain_rate: float = 0.001  # 1/s for strain control
    load_rate: float = 10.0  # N/s for load control
    
    # Preload
    preload_enabled: bool = True
    preload_value: float = 0.5  # N
    preload_speed: float = 5.0  # mm/min
    
    # Multi-stage profile
    multi_stage_enabled: bool = False
    stages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Hold settings (for creep/relaxation)
    hold_enabled: bool = False
    hold_duration: float = 0.0  # seconds
    hold_at_load: float = 0.0  # N
    
    # Return settings
    return_enabled: bool = False
    return_speed: float = 50.0  # mm/min


@dataclass
class DataAcquisitionConfig:
    """Data acquisition settings."""
    # Sampling
    sampling_rate: float = 10.0  # Hz
    event_sampling_rate: float = 50.0  # Hz during events
    event_sampling_enabled: bool = True
    
    # Filters
    digital_filter_enabled: bool = False
    filter_cutoff: float = 10.0  # Hz
    median_filter_enabled: bool = False
    median_filter_window: int = 3
    
    # Channels to record
    record_force: bool = True
    record_extension: bool = True
    record_strain: bool = True
    record_displacement: bool = True
    record_time: bool = True
    record_temperature: bool = False
    record_video: bool = False
    
    # True stress/strain
    calculate_true_values: bool = True


@dataclass
class TerminationCriteria:
    """Test termination conditions."""
    # Break detection
    break_detection_enabled: bool = True
    break_force_drop: float = 50.0  # % force drop to detect break
    break_force_threshold: float = 0.5  # N minimum force after break
    
    # Limits
    max_force: float = 450.0  # N
    max_extension: float = 100.0  # mm
    max_strain: float = 500.0  # %
    max_time: float = 3600.0  # seconds
    
    # Completion
    stop_at_break: bool = True
    return_after_break: bool = False


# ============== Test Results Data Classes ==============

@dataclass
class DataPoint:
    """Single data point during test."""
    timestamp: float  # ms
    force: float  # N
    extension: float  # mm
    stress: float  # MPa
    strain: float  # ratio (not %)
    displacement: float = 0.0  # mm (crosshead)
    true_stress: float = 0.0  # MPa
    true_strain: float = 0.0  # ratio
    temperature: float = 0.0  # °C
    load_rate: float = 0.0  # N/s
    strain_rate: float = 0.0  # 1/s


@dataclass
class MechanicalProperties:
    """Calculated mechanical properties."""
    # Strength
    ultimate_tensile_strength: float = 0.0  # MPa (UTS)
    yield_strength_offset: float = 0.0  # MPa (Rp0.2)
    yield_strength_proportional: float = 0.0  # MPa
    break_stress: float = 0.0  # MPa
    
    # Force
    max_force: float = 0.0  # N
    force_at_yield: float = 0.0  # N
    force_at_break: float = 0.0  # N
    
    # Modulus
    youngs_modulus: float = 0.0  # MPa
    secant_modulus: float = 0.0  # MPa
    chord_modulus: float = 0.0  # MPa
    modulus_r_squared: float = 0.0  # R² of linear fit
    
    # Strain/Extension
    strain_at_yield: float = 0.0  # %
    strain_at_break: float = 0.0  # % (elongation at break)
    strain_at_uts: float = 0.0  # %
    extension_at_break: float = 0.0  # mm
    extension_at_yield: float = 0.0  # mm
    
    # Energy
    energy_to_yield: float = 0.0  # J
    energy_to_break: float = 0.0  # J (toughness)
    resilience: float = 0.0  # J/m³
    
    # True values
    true_stress_at_uts: float = 0.0  # MPa
    true_strain_at_break: float = 0.0  # ratio
    
    # Poisson ratio (if transverse measurement available)
    poisson_ratio: float = 0.0


@dataclass
class TestResults:
    """Complete test results."""
    # Metadata
    metadata: TestMetadata = field(default_factory=TestMetadata)
    specimen: SpecimenConfig = field(default_factory=SpecimenConfig)
    machine: MachineConfig = field(default_factory=MachineConfig)
    control: TestControlConfig = field(default_factory=TestControlConfig)
    
    # Mechanical properties
    properties: MechanicalProperties = field(default_factory=MechanicalProperties)
    
    # Failure info
    failure_type: FailureType = FailureType.UNKNOWN
    break_location: BreakLocation = BreakLocation.UNKNOWN
    
    # Test execution
    test_duration: float = 0.0  # seconds
    data_points_count: int = 0
    test_stage_final: TestStage = TestStage.COMPLETE
    
    # Pass/Fail
    pass_fail: Optional[bool] = None
    pass_fail_criteria: str = ""
    pass_fail_notes: str = ""
    
    # Raw data reference
    data_file_path: str = ""
    
    # Timestamps
    start_time: str = ""
    end_time: str = ""
    
    # Operator notes
    operator_notes: str = ""
    
    # Images
    failure_image_path: str = ""
    video_path: str = ""


@dataclass
class TestConfiguration:
    """Complete test configuration container."""
    metadata: TestMetadata = field(default_factory=TestMetadata)
    specimen: SpecimenConfig = field(default_factory=SpecimenConfig)
    machine: MachineConfig = field(default_factory=MachineConfig)
    control: TestControlConfig = field(default_factory=TestControlConfig)
    acquisition: DataAcquisitionConfig = field(default_factory=DataAcquisitionConfig)
    termination: TerminationCriteria = field(default_factory=TerminationCriteria)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        from dataclasses import asdict
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, dict):
                result[key] = {}
                for k, v in value.items():
                    if isinstance(v, Enum):
                        result[key][k] = v.value
                    else:
                        result[key][k] = v
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfiguration':
        """Create from dictionary."""
        config = cls()
        # Implementation for loading from dict
        return config


# ============== Export Formats ==============

@dataclass
class ExportConfig:
    """Export configuration."""
    # Format selection
    export_csv: bool = True
    export_excel: bool = True
    export_json: bool = False
    export_pdf: bool = True
    export_xml: bool = False
    
    # Content options
    include_raw_data: bool = True
    include_processed_data: bool = True
    include_metadata: bool = True
    include_machine_config: bool = True
    include_plots: bool = True
    include_summary: bool = True
    
    # PDF options
    include_company_logo: bool = True
    company_name: str = "DIY Tensile Tester"
    include_signature_fields: bool = True
    
    # File naming
    filename_pattern: str = "{sample_id}_{date}_{time}"
    output_directory: str = "./results"
