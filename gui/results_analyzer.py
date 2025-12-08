#!/usr/bin/env python3
"""
Results Analyzer Module

Calculates mechanical properties from tensile test data.
Implements standard calculations per ISO/ASTM methods.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class FailureType(Enum):
    """Types of specimen failure."""
    BRITTLE = "Brittle"
    DUCTILE = "Ductile"
    NECKING = "Necking/Ductile"
    GRIP_FAILURE = "Grip Failure"
    PARTIAL = "Partial Break"
    NO_BREAK = "No Break"
    UNKNOWN = "Unknown"


class BreakLocation(Enum):
    """Location of specimen break."""
    CENTER = "Center (Acceptable)"
    QUARTER = "25% from grip (Acceptable)"
    NEAR_GRIP = "Near Grip (Marginal)"
    AT_GRIP = "At Grip (Invalid)"
    OUTSIDE_GAUGE = "Outside Gauge"
    UNKNOWN = "Unknown"


@dataclass
class TestDataPoint:
    """Single data point from test."""
    time: float  # seconds
    force: float  # N
    extension: float  # mm
    displacement: float  # mm (crosshead)
    stress: float  # MPa
    strain: float  # ratio (not %)


@dataclass
class MechanicalProperties:
    """Calculated mechanical properties from tensile test."""
    # Strength properties
    ultimate_tensile_strength: float = 0.0  # MPa (UTS)
    yield_strength_offset: float = 0.0  # MPa (Rp0.2)
    yield_strength_upper: float = 0.0  # MPa (ReH - upper yield)
    yield_strength_lower: float = 0.0  # MPa (ReL - lower yield)
    break_stress: float = 0.0  # MPa
    
    # Modulus
    youngs_modulus: float = 0.0  # MPa (E)
    modulus_chord: float = 0.0  # MPa (chord modulus)
    modulus_secant: float = 0.0  # MPa (secant modulus)
    
    # Strain/elongation
    strain_at_yield: float = 0.0  # ratio
    strain_at_uts: float = 0.0  # ratio
    strain_at_break: float = 0.0  # ratio
    elongation_at_break: float = 0.0  # % (engineering)
    uniform_elongation: float = 0.0  # %
    
    # Force values
    max_force: float = 0.0  # N
    force_at_yield: float = 0.0  # N
    force_at_break: float = 0.0  # N
    
    # Extension values
    extension_at_yield: float = 0.0  # mm
    extension_at_uts: float = 0.0  # mm
    extension_at_break: float = 0.0  # mm
    
    # Energy
    energy_to_yield: float = 0.0  # J (area under curve)
    energy_to_uts: float = 0.0  # J
    energy_to_break: float = 0.0  # J (toughness)
    
    # True stress-strain
    true_stress_at_uts: float = 0.0  # MPa
    true_strain_at_uts: float = 0.0  # ratio
    
    # Failure info
    failure_type: FailureType = FailureType.UNKNOWN
    break_location: BreakLocation = BreakLocation.UNKNOWN
    
    # Quality indicators
    modulus_r_squared: float = 0.0  # R² for modulus fit
    is_valid_test: bool = True
    validity_notes: str = ""


@dataclass
class LiveCalculations:
    """Real-time calculated values during test."""
    current_stress: float = 0.0  # MPa
    current_strain: float = 0.0  # ratio
    current_true_stress: float = 0.0  # MPa
    current_true_strain: float = 0.0  # ratio
    loading_rate_force: float = 0.0  # N/s
    loading_rate_stress: float = 0.0  # MPa/s
    strain_rate: float = 0.0  # 1/s
    displacement_rate: float = 0.0  # mm/s
    energy_absorbed: float = 0.0  # J
    instantaneous_modulus: float = 0.0  # MPa
    test_stage: str = "Idle"


class ResultsAnalyzer:
    """
    Analyzes tensile test data and calculates mechanical properties.
    
    Implements calculations according to:
    - ISO 527 (Plastics)
    - ISO 6892-1 (Metals)
    - ASTM D638 (Plastics)
    - ASTM E8 (Metals)
    """
    
    def __init__(self, gauge_length: float, cross_section_area: float):
        """
        Initialize analyzer.
        
        Args:
            gauge_length: Original gauge length in mm
            cross_section_area: Original cross-sectional area in mm²
        """
        self.gauge_length = gauge_length
        self.cross_section_area = cross_section_area
        
        # Data storage
        self.data: List[TestDataPoint] = []
        self.time_data: List[float] = []
        self.force_data: List[float] = []
        self.extension_data: List[float] = []
        self.displacement_data: List[float] = []
        self.stress_data: List[float] = []
        self.strain_data: List[float] = []
        
        # Configuration
        self.yield_offset = 0.002  # 0.2% offset for Rp0.2
        self.modulus_strain_start = 0.0005  # Start of modulus region
        self.modulus_strain_end = 0.0025  # End of modulus region
        self.break_detection_drop = 0.5  # 50% force drop = break
        
        # Live calculations
        self.live = LiveCalculations()
        
    def add_data_point(self, time: float, force: float, extension: float, 
                       displacement: float = None):
        """
        Add a new data point and update live calculations.
        
        Args:
            time: Time in seconds
            force: Force in N
            extension: Extension in mm
            displacement: Crosshead displacement in mm (optional)
        """
        if displacement is None:
            displacement = extension
        
        # Calculate stress and strain
        stress = force / self.cross_section_area  # MPa
        strain = extension / self.gauge_length  # ratio
        
        # Store data
        point = TestDataPoint(time, force, extension, displacement, stress, strain)
        self.data.append(point)
        
        self.time_data.append(time)
        self.force_data.append(force)
        self.extension_data.append(extension)
        self.displacement_data.append(displacement)
        self.stress_data.append(stress)
        self.strain_data.append(strain)
        
        # Update live calculations
        self._update_live_calculations()
    
    def _update_live_calculations(self):
        """Update real-time calculated values."""
        if len(self.data) < 2:
            return
        
        current = self.data[-1]
        prev = self.data[-2]
        
        # Current values
        self.live.current_stress = current.stress
        self.live.current_strain = current.strain
        
        # True stress and strain (valid until necking)
        if current.strain < 0.5:  # Reasonable limit
            self.live.current_true_strain = np.log(1 + current.strain)
            self.live.current_true_stress = current.stress * (1 + current.strain)
        
        # Rates
        dt = current.time - prev.time
        if dt > 0:
            self.live.loading_rate_force = (current.force - prev.force) / dt
            self.live.loading_rate_stress = (current.stress - prev.stress) / dt
            self.live.strain_rate = (current.strain - prev.strain) / dt
            self.live.displacement_rate = (current.displacement - prev.displacement) / dt
        
        # Energy absorbed (incremental trapezoidal integration - more efficient)
        if len(self.data) >= 2:
            # Add incremental energy
            d_ext = current.extension - prev.extension
            avg_force = (current.force + prev.force) / 2
            self.live.energy_absorbed += (avg_force * d_ext) / 1000  # J (convert N*mm to J)
        
        # Instantaneous modulus (from recent points)
        if len(self.data) >= 10:
            recent_stress = self.stress_data[-10:]
            recent_strain = self.strain_data[-10:]
            d_strain = recent_strain[-1] - recent_strain[0]
            if d_strain > 1e-6:
                self.live.instantaneous_modulus = (recent_stress[-1] - recent_stress[0]) / d_strain
        
        # Determine test stage
        self._determine_test_stage()
    
    def _determine_test_stage(self):
        """Determine current test stage based on data."""
        if len(self.data) < 5:
            self.live.test_stage = "Starting"
            return
        
        current = self.data[-1]
        max_force = max(self.force_data)
        max_stress = max(self.stress_data)
        
        # Check for break (force dropped significantly)
        if current.force < 0.5 * max_force and max_force > 10:
            self.live.test_stage = "Break Detected"
            return
        
        # Check if in elastic region (low strain, increasing force)
        if current.strain < 0.01 and self.live.loading_rate_force > 0:
            self.live.test_stage = "Elastic Region"
            return
        
        # Check if yielding (stress plateau or slight drop)
        if len(self.stress_data) > 20:
            recent_stress = self.stress_data[-20:]
            stress_change = max(recent_stress) - min(recent_stress)
            if stress_change < 0.05 * max_stress and current.strain > 0.005:
                self.live.test_stage = "Yielding"
                return
        
        # Check if past yield (strain hardening or softening)
        if current.stress > 0.8 * max_stress:
            self.live.test_stage = "Strain Hardening"
        else:
            self.live.test_stage = "Post-Yield"
    
    def calculate_results(self) -> MechanicalProperties:
        """
        Calculate all mechanical properties from collected data.
        
        Returns:
            MechanicalProperties object with all calculated values
        """
        results = MechanicalProperties()
        
        if len(self.data) < 10:
            results.is_valid_test = False
            results.validity_notes = "Insufficient data points"
            return results
        
        # Convert to numpy arrays for calculations
        force = np.array(self.force_data)
        extension = np.array(self.extension_data)
        stress = np.array(self.stress_data)
        strain = np.array(self.strain_data)
        
        # Maximum values
        results.max_force = float(np.max(force))
        uts_idx = int(np.argmax(stress))
        results.ultimate_tensile_strength = float(stress[uts_idx])
        results.strain_at_uts = float(strain[uts_idx])
        results.extension_at_uts = float(extension[uts_idx])
        
        # Break values (last point or where force dropped)
        break_idx = self._find_break_point(force)
        results.force_at_break = float(force[break_idx])
        results.break_stress = float(stress[break_idx])
        results.strain_at_break = float(strain[break_idx])
        results.extension_at_break = float(extension[break_idx])
        results.elongation_at_break = float(strain[break_idx] * 100)  # Convert to %
        
        # Uniform elongation (strain at UTS)
        results.uniform_elongation = float(strain[uts_idx] * 100)
        
        # Calculate Young's modulus
        modulus, r_squared = self._calculate_youngs_modulus(stress, strain)
        results.youngs_modulus = modulus
        results.modulus_r_squared = r_squared
        
        # Calculate yield strength (0.2% offset method)
        yield_stress, yield_strain, yield_force, yield_ext = self._calculate_yield_strength(
            stress, strain, force, extension, modulus
        )
        results.yield_strength_offset = yield_stress
        results.strain_at_yield = yield_strain
        results.force_at_yield = yield_force
        results.extension_at_yield = yield_ext
        
        # Energy calculations
        results.energy_to_break = float(np.trapz(force, extension) / 1000)  # J
        
        # Energy to yield
        if yield_strain > 0:
            yield_idx = np.searchsorted(strain, yield_strain)
            if yield_idx > 0:
                results.energy_to_yield = float(np.trapz(force[:yield_idx], extension[:yield_idx]) / 1000)
        
        # Energy to UTS
        results.energy_to_uts = float(np.trapz(force[:uts_idx+1], extension[:uts_idx+1]) / 1000)
        
        # True stress-strain at UTS
        results.true_strain_at_uts = float(np.log(1 + strain[uts_idx]))
        results.true_stress_at_uts = float(stress[uts_idx] * (1 + strain[uts_idx]))
        
        # Determine failure type
        results.failure_type = self._determine_failure_type(stress, strain, uts_idx, break_idx)
        
        # Validate test
        self._validate_test(results)
        
        return results
    
    def _find_break_point(self, force: np.ndarray) -> int:
        """Find the index where specimen broke."""
        max_force = np.max(force)
        max_idx = np.argmax(force)
        
        # Look for force drop after maximum
        for i in range(max_idx, len(force)):
            if force[i] < self.break_detection_drop * max_force:
                return i
        
        # No clear break, return last point
        return len(force) - 1
    
    def _calculate_youngs_modulus(self, stress: np.ndarray, strain: np.ndarray) -> Tuple[float, float]:
        """
        Calculate Young's modulus from linear region.
        
        Returns:
            Tuple of (modulus in MPa, R² value)
        """
        # Find points in the specified strain range
        mask = (strain >= self.modulus_strain_start) & (strain <= self.modulus_strain_end)
        
        if np.sum(mask) < 5:
            # Not enough points, try auto-detect linear region
            mask = (strain >= 0.0001) & (strain <= 0.01)
        
        if np.sum(mask) < 5:
            return 0.0, 0.0
        
        strain_linear = strain[mask]
        stress_linear = stress[mask]
        
        # Linear regression
        try:
            coeffs = np.polyfit(strain_linear, stress_linear, 1)
            modulus = coeffs[0]  # Slope = E
            
            # Calculate R²
            predicted = np.polyval(coeffs, strain_linear)
            ss_res = np.sum((stress_linear - predicted) ** 2)
            ss_tot = np.sum((stress_linear - np.mean(stress_linear)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return float(modulus), float(r_squared)
        except:
            return 0.0, 0.0
    
    def _calculate_yield_strength(self, stress: np.ndarray, strain: np.ndarray,
                                   force: np.ndarray, extension: np.ndarray,
                                   modulus: float) -> Tuple[float, float, float, float]:
        """
        Calculate yield strength using 0.2% offset method.
        
        Returns:
            Tuple of (yield_stress, yield_strain, yield_force, yield_extension)
        """
        if modulus <= 0:
            return 0.0, 0.0, 0.0, 0.0
        
        # Create offset line: σ = E * (ε - 0.002)
        offset_line = modulus * (strain - self.yield_offset)
        
        # Find intersection with stress-strain curve
        # Where stress_curve crosses offset_line from above
        diff = stress - offset_line
        
        # Find sign change (crossing point)
        for i in range(1, len(diff)):
            if diff[i-1] > 0 and diff[i] <= 0:
                # Linear interpolation for exact crossing
                t = diff[i-1] / (diff[i-1] - diff[i])
                yield_strain = strain[i-1] + t * (strain[i] - strain[i-1])
                yield_stress = stress[i-1] + t * (stress[i] - stress[i-1])
                yield_force = force[i-1] + t * (force[i] - force[i-1])
                yield_ext = extension[i-1] + t * (extension[i] - extension[i-1])
                return float(yield_stress), float(yield_strain), float(yield_force), float(yield_ext)
        
        # No clear yield point found, use proportional limit estimate
        # (point where curve deviates from linear by 0.1%)
        return 0.0, 0.0, 0.0, 0.0
    
    def _determine_failure_type(self, stress: np.ndarray, strain: np.ndarray,
                                 uts_idx: int, break_idx: int) -> FailureType:
        """Determine the type of failure based on stress-strain behavior."""
        
        # Check strain at break
        strain_at_break = strain[break_idx]
        
        # Brittle: breaks with little plastic deformation
        if strain_at_break < 0.02:  # < 2% strain
            return FailureType.BRITTLE
        
        # Check for necking (stress drop before break)
        post_uts_strain = strain[break_idx] - strain[uts_idx]
        
        if post_uts_strain > 0.05:  # Significant strain after UTS
            return FailureType.NECKING
        
        if strain_at_break > 0.05:  # > 5% strain
            return FailureType.DUCTILE
        
        return FailureType.UNKNOWN
    
    def _validate_test(self, results: MechanicalProperties):
        """Validate test results and add notes."""
        notes = []
        
        # Check modulus fit quality
        if results.modulus_r_squared < 0.99:
            notes.append(f"Modulus fit R²={results.modulus_r_squared:.3f} (ideal > 0.99)")
        
        # Check for reasonable values
        if results.youngs_modulus <= 0:
            notes.append("Could not determine Young's modulus")
            results.is_valid_test = False
        
        if results.yield_strength_offset <= 0:
            notes.append("Could not determine yield strength")
        
        if results.ultimate_tensile_strength < results.yield_strength_offset:
            notes.append("UTS less than yield strength (unusual)")
        
        if results.elongation_at_break <= 0:
            notes.append("No elongation at break recorded")
        
        results.validity_notes = "; ".join(notes) if notes else "Test valid"
    
    def get_stress_strain_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get stress-strain arrays for plotting."""
        return np.array(self.strain_data), np.array(self.stress_data)
    
    def get_force_extension_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get force-extension arrays for plotting."""
        return np.array(self.extension_data), np.array(self.force_data)
    
    def get_true_stress_strain_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get true stress-strain arrays for plotting."""
        strain = np.array(self.strain_data)
        stress = np.array(self.stress_data)
        
        # Valid only up to necking (roughly UTS)
        uts_idx = np.argmax(stress)
        strain = strain[:uts_idx+1]
        stress = stress[:uts_idx+1]
        
        true_strain = np.log(1 + strain)
        true_stress = stress * (1 + strain)
        
        return true_strain, true_stress
    
    def get_modulus_fit_line(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get the modulus regression line for plotting."""
        strain = np.array(self.strain_data)
        modulus = self.calculate_results().youngs_modulus
        
        # Line from 0 to ~1% strain
        x = np.array([0, 0.01])
        y = modulus * x
        
        return x, y
    
    def get_yield_offset_line(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get the 0.2% offset line for plotting."""
        strain = np.array(self.strain_data)
        modulus = self.calculate_results().youngs_modulus
        
        # Offset line: σ = E * (ε - 0.002)
        x = np.array([self.yield_offset, max(0.02, strain.max() * 0.5)])
        y = modulus * (x - self.yield_offset)
        
        return x, y
    
    def clear_data(self):
        """Clear all stored data."""
        self.data.clear()
        self.time_data.clear()
        self.force_data.clear()
        self.extension_data.clear()
        self.displacement_data.clear()
        self.stress_data.clear()
        self.strain_data.clear()
        self.live = LiveCalculations()


def calculate_statistics(values: List[float]) -> dict:
    """Calculate statistical measures for a set of values."""
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
    
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": len(values),
        "cv": float(np.std(arr) / np.mean(arr) * 100) if np.mean(arr) != 0 else 0  # Coefficient of variation %
    }
