#!/usr/bin/env python3
"""
Test Configuration Data Model

Contains all dataclasses for test configuration parameters.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime


# ============================================================================
# Enums for configuration options
# ============================================================================

class TestStandard(Enum):
    """Common test standards."""
    ISO_527 = "ISO 527 - Plastics Tensile"
    ISO_527_1 = "ISO 527-1 - Plastics General"
    ISO_527_2 = "ISO 527-2 - Plastics Molding"
    ASTM_D638 = "ASTM D638 - Plastics Tensile"
    ASTM_D412 = "ASTM D412 - Rubber Tensile"
    DIN_EN_ISO_6892_1 = "DIN EN ISO 6892-1 - Metals Tensile"
    ISO_6892_1 = "ISO 6892-1 - Metals Tensile"
    ASTM_E8 = "ASTM E8 - Metals Tensile"
    ISO_1924 = "ISO 1924 - Paper Tensile"
    CUSTOM = "Custom Test"


class MaterialType(Enum):
    """Material categories."""
    POLYMER = "Polymer / Plastic"
    METAL = "Metal / Alloy"
    COMPOSITE = "Composite"
    RUBBER = "Rubber / Elastomer"
    PAPER = "Paper / Cardboard"
    TEXTILE = "Textile / Fiber"
    FILM = "Film / Foil"
    ADHESIVE = "Adhesive"
    OTHER = "Other"


class SpecimenShape(Enum):
    """Specimen cross-section shapes."""
    RECTANGULAR = "Rectangular"
    CIRCULAR = "Circular"
    TUBULAR = "Tubular"
    DOG_BONE = "Dog-bone (ISO/ASTM)"
    CUSTOM = "Custom"


class LoadCellCapacity(Enum):
    """Load cell capacity options."""
    LC_100N = "100 N"
    LC_500N = "500 N"
    LC_1KN = "1 kN"
    LC_5KN = "5 kN"
    LC_10KN = "10 kN"
    LC_20KN = "20 kN"
    LC_50KN = "50 kN"
    LC_100KN = "100 kN"


class ExtensometerType(Enum):
    """Extensometer types."""
    NONE = "None (Crosshead only)"
    CLIP_ON = "Clip-on Extensometer"
    VIDEO = "Video Extensometer"
    LASER = "Laser Extensometer"
    NON_CONTACT = "Non-contact Optical"


class ControlMode(Enum):
    """Test control modes."""
    DISPLACEMENT = "Displacement Control"
    STRAIN = "Strain Control"
    LOAD = "Load Control"
    STRESS = "Stress Control"


class PreloadMethod(Enum):
    """Preload application methods."""
    NONE = "No Preload"
    FORCE = "Force-based"
    STRESS = "Stress-based"
    EXTENSION = "Extension-based"


class BreakDetection(Enum):
    """Break detection methods."""
    FORCE_DROP_PERCENT = "Force Drop %"
    FORCE_DROP_ABSOLUTE = "Force Drop (N)"
    FORCE_THRESHOLD = "Force Below Threshold"
    MANUAL = "Manual Only"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TestMetadata:
    """Test identification and metadata."""
    test_standard: TestStandard = TestStandard.CUSTOM
    sample_id: str = ""
    batch_id: str = ""
    operator_name: str = ""
    customer_name: str = ""
    project_name: str = ""
    material_type: MaterialType = MaterialType.POLYMER
    material_name: str = ""
    notes: str = ""
    test_date: datetime = field(default_factory=datetime.now)


@dataclass
class SpecimenGeometry:
    """Specimen dimensions and geometry."""
    shape: SpecimenShape = SpecimenShape.RECTANGULAR
    gauge_length: float = 50.0  # mm
    thickness: float = 4.0  # mm
    width: float = 10.0  # mm
    diameter: float = 0.0  # mm (for circular)
    inner_diameter: float = 0.0  # mm (for tubular)
    cross_section_area: float = 40.0  # mm² (calculated or manual)
    auto_calculate_area: bool = True
    
    def calculate_area(self) -> float:
        """Calculate cross-sectional area based on shape."""
        if self.shape == SpecimenShape.RECTANGULAR or self.shape == SpecimenShape.DOG_BONE:
            return self.thickness * self.width
        elif self.shape == SpecimenShape.CIRCULAR:
            import math
            return math.pi * (self.diameter / 2) ** 2
        elif self.shape == SpecimenShape.TUBULAR:
            import math
            outer_area = math.pi * (self.diameter / 2) ** 2
            inner_area = math.pi * (self.inner_diameter / 2) ** 2
            return outer_area - inner_area
        else:
            return self.cross_section_area


@dataclass
class EnvironmentalConditions:
    """Test environmental conditions."""
    record_conditions: bool = False
    temperature: float = 23.0  # °C
    humidity: float = 50.0  # %RH
    conditioning_time: float = 0.0  # hours
    conditioning_temp: float = 23.0  # °C
    conditioning_humidity: float = 50.0  # %RH


@dataclass
class HardwareSettings:
    """Machine and hardware configuration."""
    load_cell: LoadCellCapacity = LoadCellCapacity.LC_500N
    extensometer: ExtensometerType = ExtensometerType.NONE
    
    # Crosshead limits
    upper_limit: float = 150.0  # mm
    lower_limit: float = 0.0  # mm
    
    # Safety settings
    max_force_limit: float = 450.0  # N
    max_extension_limit: float = 100.0  # mm
    emergency_return_speed: float = 50.0  # mm/min
    
    # Preload settings
    preload_method: PreloadMethod = PreloadMethod.FORCE
    preload_value: float = 0.5  # N or MPa or mm depending on method
    preload_speed: float = 5.0  # mm/min


@dataclass
class ZeroSettings:
    """Zeroing configuration."""
    zero_force_before_test: bool = True
    zero_extension_before_test: bool = True
    zero_extensometer_before_test: bool = True
    zero_after_preload: bool = False
    tare_with_grips: bool = False


@dataclass 
class RampStage:
    """A single ramp/hold stage in a test profile."""
    name: str = "Ramp"
    control_mode: ControlMode = ControlMode.DISPLACEMENT
    target_value: float = 0.0  # mm, %, N, or MPa depending on mode
    speed: float = 1.0  # mm/min, %/min, N/s, MPa/s
    hold_time: float = 0.0  # seconds (0 = no hold)
    

@dataclass
class TestControlSettings:
    """Test control parameters."""
    control_mode: ControlMode = ControlMode.DISPLACEMENT
    
    # Speed settings
    test_speed: float = 2.0  # mm/min
    strain_rate: float = 0.0  # 1/min (for strain control)
    load_rate: float = 0.0  # N/s (for load control)
    stress_rate: float = 0.0  # MPa/s (for stress control)
    
    # Return settings
    return_speed: float = 50.0  # mm/min
    return_after_break: bool = True
    return_position: float = 0.0  # mm
    
    # Multi-stage profile
    use_multi_stage: bool = False
    stages: List[RampStage] = field(default_factory=list)
    
    # Approach settings (before test starts)
    approach_speed: float = 10.0  # mm/min
    approach_force: float = 0.1  # N (detect specimen contact)


@dataclass
class DataAcquisitionSettings:
    """Data acquisition configuration."""
    sampling_rate: float = 10.0  # Hz
    
    # Digital filtering
    apply_filter: bool = False
    filter_type: str = "Moving Average"  # "Moving Average", "Median", "Butterworth"
    filter_window: int = 5  # samples
    
    # Channels to record
    record_force: bool = True
    record_extension: bool = True
    record_strain: bool = True
    record_displacement: bool = True
    record_time: bool = True
    record_temperature: bool = False
    record_video: bool = False
    
    # Calculated channels
    calculate_stress: bool = True
    calculate_strain: bool = True
    calculate_modulus: bool = True


@dataclass
class TerminationCriteria:
    """Test termination/failure criteria."""
    # Break detection
    break_detection: BreakDetection = BreakDetection.FORCE_DROP_PERCENT
    force_drop_percent: float = 50.0  # %
    force_drop_absolute: float = 10.0  # N
    force_threshold: float = 1.0  # N
    
    # Limits
    max_force: float = 450.0  # N
    max_extension: float = 100.0  # mm
    max_strain: float = 500.0  # %
    max_time: float = 3600.0  # seconds (1 hour default)
    
    # Enable/disable criteria
    enable_break_detection: bool = True
    enable_max_force: bool = True
    enable_max_extension: bool = True
    enable_max_strain: bool = False
    enable_max_time: bool = False


@dataclass
class TestConfiguration:
    """Complete test configuration."""
    # Configuration name and version
    config_name: str = "Default"
    config_version: str = "1.0"
    
    # All sub-configurations
    metadata: TestMetadata = field(default_factory=TestMetadata)
    specimen: SpecimenGeometry = field(default_factory=SpecimenGeometry)
    environment: EnvironmentalConditions = field(default_factory=EnvironmentalConditions)
    hardware: HardwareSettings = field(default_factory=HardwareSettings)
    zeroing: ZeroSettings = field(default_factory=ZeroSettings)
    control: TestControlSettings = field(default_factory=TestControlSettings)
    acquisition: DataAcquisitionSettings = field(default_factory=DataAcquisitionSettings)
    termination: TerminationCriteria = field(default_factory=TerminationCriteria)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Specimen validation
        if self.specimen.gauge_length <= 0:
            errors.append("Gauge length must be positive")
        if self.specimen.auto_calculate_area:
            self.specimen.cross_section_area = self.specimen.calculate_area()
        if self.specimen.cross_section_area <= 0:
            errors.append("Cross-sectional area must be positive")
        
        # Hardware validation
        if self.hardware.upper_limit <= self.hardware.lower_limit:
            errors.append("Upper limit must be greater than lower limit")
        
        # Control validation
        if self.control.test_speed <= 0:
            errors.append("Test speed must be positive")
        
        # Termination validation
        if self.termination.enable_max_force and self.termination.max_force <= 0:
            errors.append("Max force must be positive")
        if self.termination.enable_max_extension and self.termination.max_extension <= 0:
            errors.append("Max extension must be positive")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary for saving."""
        import json
        from dataclasses import asdict
        
        def convert_value(obj):
            if isinstance(obj, Enum):
                return obj.name
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        result = asdict(self)
        # Convert enums and datetime to strings
        def process_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    process_dict(value)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            process_dict(item)
                else:
                    d[key] = convert_value(value)
        
        process_dict(result)
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestConfiguration':
        """Create configuration from dictionary."""
        # This would need proper enum conversion - simplified for now
        config = cls()
        # TODO: Implement full deserialization
        return config
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'TestConfiguration':
        """Load configuration from JSON file."""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class TestResults:
    """Results from a completed tensile test."""
    # Primary strength values
    max_force: float = 0.0  # N
    max_stress: float = 0.0  # MPa (UTS)
    max_strain: float = 0.0  # % at break
    max_extension: float = 0.0  # mm
    
    # Calculated properties
    yield_strength: float = 0.0  # MPa (Rp0.2)
    youngs_modulus: float = 0.0  # MPa
    elongation_at_break: float = 0.0  # %
    energy_absorbed: float = 0.0  # J (toughness)
    
    # Failure information
    failure_type: str = "Unknown"
    
    # Test metadata
    test_duration: float = 0.0  # seconds
    data_points: int = 0


# ============================================================================
# Preset Configurations
# ============================================================================

def get_iso527_preset() -> TestConfiguration:
    """Get ISO 527 standard preset for plastics."""
    config = TestConfiguration()
    config.config_name = "ISO 527 - Plastics"
    config.metadata.test_standard = TestStandard.ISO_527
    config.metadata.material_type = MaterialType.POLYMER
    config.specimen.shape = SpecimenShape.DOG_BONE
    config.specimen.gauge_length = 50.0
    config.specimen.width = 10.0
    config.specimen.thickness = 4.0
    config.control.test_speed = 1.0  # 1 mm/min for modulus
    config.control.use_multi_stage = True
    config.control.stages = [
        RampStage("Modulus", ControlMode.DISPLACEMENT, 0.25, 1.0, 0),  # 0.25% strain for modulus
        RampStage("Yield/Break", ControlMode.DISPLACEMENT, 100.0, 50.0, 0),  # 50 mm/min to break
    ]
    config.termination.break_detection = BreakDetection.FORCE_DROP_PERCENT
    config.termination.force_drop_percent = 50.0
    return config


def get_astm_d638_preset() -> TestConfiguration:
    """Get ASTM D638 standard preset for plastics."""
    config = TestConfiguration()
    config.config_name = "ASTM D638 - Plastics"
    config.metadata.test_standard = TestStandard.ASTM_D638
    config.metadata.material_type = MaterialType.POLYMER
    config.specimen.shape = SpecimenShape.DOG_BONE
    config.specimen.gauge_length = 50.0
    config.control.test_speed = 5.0  # 5 mm/min typical
    return config


def get_metal_tensile_preset() -> TestConfiguration:
    """Get ISO 6892-1 standard preset for metals."""
    config = TestConfiguration()
    config.config_name = "ISO 6892-1 - Metals"
    config.metadata.test_standard = TestStandard.ISO_6892_1
    config.metadata.material_type = MaterialType.METAL
    config.specimen.shape = SpecimenShape.DOG_BONE
    config.specimen.gauge_length = 50.0
    config.hardware.extensometer = ExtensometerType.CLIP_ON
    config.control.control_mode = ControlMode.STRAIN
    config.control.strain_rate = 0.00025  # 0.00025/s for modulus
    return config


PRESET_CONFIGS = {
    "Default": TestConfiguration(),
    "ISO 527 - Plastics": get_iso527_preset(),
    "ASTM D638 - Plastics": get_astm_d638_preset(),
    "ISO 6892-1 - Metals": get_metal_tensile_preset(),
}
