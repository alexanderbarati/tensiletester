#!/usr/bin/env python3
"""
Results Window for Professional Tensile Testing System

Comprehensive results display with mechanical properties calculations,
failure analysis, and compliance checking following industry standards.

Author: DIY Tensile Tester Project
Version: 2.0.0
"""

import dearpygui.dearpygui as dpg
import numpy as np
from typing import List, Optional, Callable
from dataclasses import dataclass, field

from models import (
    TestConfiguration, MechanicalProperties, TestResults,
    FailureType, BreakLocation, TestStage
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
    'pass': (76, 175, 80),
    'fail': (244, 67, 54),
}


@dataclass
class TestData:
    """Container for test data arrays."""
    times: List[float] = field(default_factory=list)
    forces: List[float] = field(default_factory=list)
    extensions: List[float] = field(default_factory=list)
    stresses: List[float] = field(default_factory=list)
    strains: List[float] = field(default_factory=list)
    true_stresses: List[float] = field(default_factory=list)
    true_strains: List[float] = field(default_factory=list)


class ResultsAnalyzer:
    """Analyzes test data and calculates mechanical properties."""
    
    def __init__(self):
        self.properties = MechanicalProperties()
    
    def analyze(self, data: TestData, config: TestConfiguration) -> MechanicalProperties:
        """Perform complete analysis of test data."""
        self.properties = MechanicalProperties()
        
        if not data.forces or len(data.forces) < 5:
            return self.properties
        
        forces = np.array(data.forces)
        extensions = np.array(data.extensions)
        stresses = np.array(data.stresses)
        strains = np.array(data.strains)
        
        # Maximum values
        self._calculate_max_values(forces, extensions, stresses, strains)
        
        # Young's Modulus
        self._calculate_modulus(stresses, strains)
        
        # Yield strength (0.2% offset)
        self._calculate_yield(stresses, strains)
        
        # Energy calculations
        self._calculate_energy(forces, extensions, stresses, strains)
        
        # Break values
        self._calculate_break_values(forces, extensions, stresses, strains)
        
        # True stress/strain if available
        if data.true_stresses:
            self._calculate_true_values(data.true_stresses, data.true_strains)
        
        return self.properties
    
    def _calculate_max_values(self, forces, extensions, stresses, strains):
        """Calculate maximum values."""
        max_idx = np.argmax(forces)
        
        self.properties.max_force = float(np.max(forces))
        self.properties.ultimate_tensile_strength = float(np.max(stresses))
        self.properties.strain_at_uts = float(strains[max_idx] * 100)  # Convert to %
    
    def _calculate_modulus(self, stresses, strains):
        """Calculate Young's modulus from linear region."""
        # Find linear region (typically 0.05% to 0.25% strain)
        strain_pct = strains * 100
        
        # Find indices in linear region
        linear_mask = (strain_pct >= 0.05) & (strain_pct <= 0.25)
        
        # If not enough points in standard range, use first 20% of data
        if np.sum(linear_mask) < 5:
            n_points = len(strains) // 5
            if n_points < 5:
                n_points = min(20, len(strains))
            linear_mask = np.zeros(len(strains), dtype=bool)
            linear_mask[:n_points] = True
        
        if np.sum(linear_mask) >= 3:
            lin_strains = strain_pct[linear_mask]
            lin_stresses = stresses[linear_mask]
            
            # Linear regression
            coeffs = np.polyfit(lin_strains, lin_stresses, 1)
            
            # Young's modulus is slope (MPa/%)
            # Convert to MPa by multiplying by 100 (since strain was in %)
            self.properties.youngs_modulus = float(coeffs[0] * 100)
            
            # R-squared
            predicted = np.polyval(coeffs, lin_strains)
            ss_res = np.sum((lin_stresses - predicted) ** 2)
            ss_tot = np.sum((lin_stresses - np.mean(lin_stresses)) ** 2)
            if ss_tot > 0:
                self.properties.modulus_r_squared = float(1 - ss_res / ss_tot)
            
            # Secant modulus (stress at 1% strain / 0.01)
            if len(strain_pct) > 0:
                idx_1pct = np.argmin(np.abs(strain_pct - 1.0))
                if strain_pct[idx_1pct] > 0:
                    self.properties.secant_modulus = float(stresses[idx_1pct] / (strain_pct[idx_1pct] / 100))
    
    def _calculate_yield(self, stresses, strains):
        """Calculate yield strength using 0.2% offset method."""
        strain_pct = strains * 100
        
        if self.properties.youngs_modulus > 0:
            # Offset line: stress = E * (strain - 0.2)
            offset_strain = 0.2  # %
            E = self.properties.youngs_modulus
            
            # Find intersection with stress-strain curve
            offset_line = E * (strain_pct - offset_strain) / 100
            
            # Find where stress-strain curve crosses offset line
            diff = stresses - offset_line
            
            # Look for sign change (crossing point)
            for i in range(1, len(diff)):
                if diff[i-1] < 0 and diff[i] >= 0:
                    # Linear interpolation to find exact crossing
                    t = -diff[i-1] / (diff[i] - diff[i-1])
                    yield_stress = stresses[i-1] + t * (stresses[i] - stresses[i-1])
                    yield_strain = strain_pct[i-1] + t * (strain_pct[i] - strain_pct[i-1])
                    
                    self.properties.yield_strength_offset = float(yield_stress)
                    self.properties.strain_at_yield = float(yield_strain)
                    
                    # Find corresponding force
                    if i < len(stresses):
                        # Approximate from stress ratio
                        ratio = yield_stress / stresses[i] if stresses[i] > 0 else 1
                        self.properties.force_at_yield = float(self.properties.max_force * ratio)
                    
                    break
            
            # If no crossing found, use alternative method (first significant deviation)
            if self.properties.yield_strength_offset == 0:
                # Find where stress deviates >5% from linear
                linear_stress = E * strain_pct / 100
                deviation = np.abs(stresses - linear_stress) / (linear_stress + 0.001)
                
                yield_idx = np.argmax(deviation > 0.05)
                if yield_idx > 0:
                    self.properties.yield_strength_offset = float(stresses[yield_idx])
                    self.properties.strain_at_yield = float(strain_pct[yield_idx])
    
    def _calculate_energy(self, forces, extensions, stresses, strains):
        """Calculate energy values."""
        # Energy to break (area under force-extension curve in Joules)
        # Force in N, extension in mm -> need to convert mm to m
        if len(forces) >= 2:
            ext_m = extensions / 1000.0  # mm to m
            self.properties.energy_to_break = float(np.trapz(forces, ext_m))
        
        # Energy to yield
        if self.properties.strain_at_yield > 0:
            strain_pct = strains * 100
            yield_idx = np.argmin(np.abs(strain_pct - self.properties.strain_at_yield))
            if yield_idx > 0:
                ext_m = extensions[:yield_idx+1] / 1000.0
                self.properties.energy_to_yield = float(np.trapz(forces[:yield_idx+1], ext_m))
        
        # Resilience (energy per unit volume up to yield point)
        # This is area under stress-strain curve to yield point
        if self.properties.strain_at_yield > 0:
            strain_pct = strains * 100
            yield_idx = np.argmin(np.abs(strain_pct - self.properties.strain_at_yield))
            if yield_idx > 0:
                # Strain as ratio (not %), stress in MPa
                self.properties.resilience = float(np.trapz(
                    stresses[:yield_idx+1], 
                    strains[:yield_idx+1]
                ))
    
    def _calculate_break_values(self, forces, extensions, stresses, strains):
        """Calculate values at break."""
        # Assume last point is break point
        self.properties.force_at_break = float(forces[-1])
        self.properties.break_stress = float(stresses[-1])
        self.properties.extension_at_break = float(extensions[-1])
        self.properties.strain_at_break = float(strains[-1] * 100)  # Convert to %
        
        # Find extension at yield
        if self.properties.strain_at_yield > 0:
            strain_pct = strains * 100
            yield_idx = np.argmin(np.abs(strain_pct - self.properties.strain_at_yield))
            self.properties.extension_at_yield = float(extensions[yield_idx])
    
    def _calculate_true_values(self, true_stresses, true_strains):
        """Calculate true stress/strain values."""
        if true_stresses and len(true_stresses) > 0:
            max_idx = np.argmax(true_stresses)
            self.properties.true_stress_at_uts = float(true_stresses[max_idx])
            self.properties.true_strain_at_break = float(true_strains[-1])
    
    @staticmethod
    def classify_failure(forces: List[float], stresses: List[float]) -> FailureType:
        """Classify failure type based on curve characteristics."""
        if not forces or len(forces) < 10:
            return FailureType.UNKNOWN
        
        forces = np.array(forces)
        stresses = np.array(stresses)
        
        max_idx = np.argmax(forces)
        max_force = forces[max_idx]
        final_force = forces[-1]
        
        # Calculate strain at failure indicators
        force_drop = (max_force - final_force) / max_force if max_force > 0 else 0
        points_after_peak = len(forces) - max_idx
        
        # Brittle: sudden drop, little plastic deformation
        if force_drop > 0.9 and points_after_peak < len(forces) * 0.1:
            return FailureType.BRITTLE
        
        # Ductile: gradual drop, significant plastic deformation
        if force_drop > 0.5 and points_after_peak > len(forces) * 0.2:
            return FailureType.DUCTILE
        
        # Necking: visible plateau before drop
        if max_idx > len(forces) * 0.3:
            # Look for plateau region
            plateau_region = forces[int(max_idx*0.8):max_idx]
            if len(plateau_region) > 5:
                variation = np.std(plateau_region) / np.mean(plateau_region)
                if variation < 0.05:  # Less than 5% variation
                    return FailureType.NECKING
        
        # No clear break
        if force_drop < 0.3:
            return FailureType.NO_BREAK
        
        return FailureType.DUCTILE


class ResultsWindow:
    """Professional results display window."""
    
    def __init__(self):
        self.window_tag = "results_window"
        self.analyzer = ResultsAnalyzer()
        self.properties = MechanicalProperties()
        self.config: Optional[TestConfiguration] = None
        self.test_data: Optional[TestData] = None
        self.on_export: Optional[Callable] = None
    
    def show(self, data: TestData, config: TestConfiguration):
        """Show results window with analyzed data."""
        self.test_data = data
        self.config = config
        
        # Debug
        print(f"[ResultsWindow] Data points: {len(data.forces) if data.forces else 0}")
        print(f"[ResultsWindow] Forces: {data.forces[:5] if data.forces else 'empty'}...")
        print(f"[ResultsWindow] Stresses: {data.stresses[:5] if data.stresses else 'empty'}...")
        
        # Analyze data
        self.properties = self.analyzer.analyze(data, config)
        
        # Debug properties
        print(f"[ResultsWindow] UTS: {self.properties.ultimate_tensile_strength}")
        print(f"[ResultsWindow] Modulus: {self.properties.youngs_modulus}")
        print(f"[ResultsWindow] Max Force: {self.properties.max_force}")
        
        # Classify failure
        failure_type = ResultsAnalyzer.classify_failure(data.forces, data.stresses)
        
        if dpg.does_item_exist(self.window_tag):
            dpg.delete_item(self.window_tag)
        
        self._create_window(failure_type, data)
        dpg.show_item(self.window_tag)
    
    def hide(self):
        """Hide results window."""
        if dpg.does_item_exist(self.window_tag):
            dpg.hide_item(self.window_tag)
    
    def _create_window(self, failure_type: FailureType, data: TestData):
        """Create the results window."""
        with dpg.window(
            label="Test Results - Mechanical Properties",
            tag=self.window_tag,
            width=750,
            height=600,
            show=False,
            modal=True,
            no_collapse=True,
            pos=(137, 0)
        ):
            # Tab bar for different views
            with dpg.tab_bar():
                self._create_properties_tab()
                self._create_failure_tab(failure_type)
                self._create_compliance_tab()
                self._create_summary_tab(data)
            
            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Export CSV", width=100, callback=self._on_export_csv)
                dpg.add_button(label="Export Excel", width=100, callback=self._on_export_excel)
                dpg.add_button(label="Export PDF", width=100, callback=self._on_export_pdf)
                dpg.add_spacer(width=100)
                dpg.add_button(label="Close", width=100, callback=self.hide)
    
    def _create_properties_tab(self):
        """Create mechanical properties tab."""
        with dpg.tab(label="Properties"):
            dpg.add_spacer(height=10)
            
            # Strength properties
            self._section_header("Strength Properties")
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True):
                dpg.add_table_column(label="Property", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Symbol", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Value", width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label="Unit", width_fixed=True, init_width_or_weight=80)
                
                self._property_row("Ultimate Tensile Strength", "σ_UTS", 
                                  f"{self.properties.ultimate_tensile_strength:.2f}", "MPa")
                self._property_row("Yield Strength (Rp0.2)", "σ_y", 
                                  f"{self.properties.yield_strength_offset:.2f}", "MPa")
                self._property_row("Break Stress", "σ_b", 
                                  f"{self.properties.break_stress:.2f}", "MPa")
                self._property_row("Maximum Force", "F_max", 
                                  f"{self.properties.max_force:.2f}", "N")
                self._property_row("Force at Yield", "F_y", 
                                  f"{self.properties.force_at_yield:.2f}", "N")
                self._property_row("Force at Break", "F_b", 
                                  f"{self.properties.force_at_break:.2f}", "N")
            
            dpg.add_spacer(height=15)
            
            # Modulus properties
            self._section_header("Elastic Properties")
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True):
                dpg.add_table_column(label="Property", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Symbol", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Value", width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label="Unit", width_fixed=True, init_width_or_weight=80)
                
                self._property_row("Young's Modulus", "E", 
                                  f"{self.properties.youngs_modulus:.1f}", "MPa")
                self._property_row("Modulus R²", "R²", 
                                  f"{self.properties.modulus_r_squared:.4f}", "-")
                self._property_row("Secant Modulus", "E_s", 
                                  f"{self.properties.secant_modulus:.1f}", "MPa")
            
            dpg.add_spacer(height=15)
            
            # Strain/Extension properties
            self._section_header("Deformation Properties")
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True):
                dpg.add_table_column(label="Property", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Symbol", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Value", width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label="Unit", width_fixed=True, init_width_or_weight=80)
                
                self._property_row("Elongation at Break", "ε_b", 
                                  f"{self.properties.strain_at_break:.2f}", "%")
                self._property_row("Strain at Yield", "ε_y", 
                                  f"{self.properties.strain_at_yield:.2f}", "%")
                self._property_row("Strain at UTS", "ε_UTS", 
                                  f"{self.properties.strain_at_uts:.2f}", "%")
                self._property_row("Extension at Break", "ΔL_b", 
                                  f"{self.properties.extension_at_break:.3f}", "mm")
                self._property_row("Extension at Yield", "ΔL_y", 
                                  f"{self.properties.extension_at_yield:.3f}", "mm")
            
            dpg.add_spacer(height=15)
            
            # Energy properties
            self._section_header("Energy Properties")
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True):
                dpg.add_table_column(label="Property", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Symbol", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Value", width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label="Unit", width_fixed=True, init_width_or_weight=80)
                
                self._property_row("Energy to Break", "U_b", 
                                  f"{self.properties.energy_to_break:.4f}", "J")
                self._property_row("Energy to Yield", "U_y", 
                                  f"{self.properties.energy_to_yield:.4f}", "J")
                self._property_row("Resilience", "U_r", 
                                  f"{self.properties.resilience:.4f}", "MJ/m³")
    
    def _create_failure_tab(self, failure_type: FailureType):
        """Create failure analysis tab."""
        with dpg.tab(label="Failure Analysis"):
            dpg.add_spacer(height=10)
            
            self._section_header("Failure Classification")
            
            with dpg.group(horizontal=True):
                dpg.add_text("Failure Type:", color=COLORS['text_dim'])
                dpg.add_text(failure_type.value, color=COLORS['accent'])
            
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Break Location:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=[e.value for e in BreakLocation],
                    default_value=BreakLocation.UNKNOWN.value,
                    width=200,
                    tag="result_break_location"
                )
            
            dpg.add_spacer(height=15)
            
            self._section_header("Failure Characteristics")
            
            # Calculate characteristics
            if self.test_data and self.test_data.forces:
                forces = np.array(self.test_data.forces)
                max_idx = np.argmax(forces)
                max_force = forces[max_idx]
                final_force = forces[-1]
                force_drop = (max_force - final_force) / max_force * 100 if max_force > 0 else 0
                points_after_peak = len(forces) - max_idx
                
                with dpg.table(header_row=False, borders_innerV=False):
                    dpg.add_table_column(width_fixed=True, init_width_or_weight=200)
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("Force drop at break:", color=COLORS['text_dim'])
                        dpg.add_text(f"{force_drop:.1f}%", color=COLORS['accent'])
                    
                    with dpg.table_row():
                        dpg.add_text("Points after peak:", color=COLORS['text_dim'])
                        dpg.add_text(f"{points_after_peak}", color=COLORS['accent'])
                    
                    with dpg.table_row():
                        dpg.add_text("Peak position:", color=COLORS['text_dim'])
                        dpg.add_text(f"{max_idx * 100 / len(forces):.1f}% through test", color=COLORS['accent'])
            
            dpg.add_spacer(height=15)
            
            self._section_header("Operator Notes")
            dpg.add_input_text(
                width=-1, height=80,
                multiline=True,
                tag="result_operator_notes",
                hint="Enter observations about failure mode, specimen condition, etc."
            )
    
    def _create_compliance_tab(self):
        """Create compliance/pass-fail tab."""
        with dpg.tab(label="Compliance"):
            dpg.add_spacer(height=10)
            
            self._section_header("Pass/Fail Criteria")
            
            # Editable criteria
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True):
                dpg.add_table_column(label="Property", width_fixed=True, init_width_or_weight=180)
                dpg.add_table_column(label="Min", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Actual", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Max", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Status", width_fixed=True, init_width_or_weight=80)
                
                # UTS criteria
                with dpg.table_row():
                    dpg.add_text("UTS (MPa)")
                    dpg.add_input_float(default_value=0, width=80, tag="crit_uts_min", step=0)
                    dpg.add_text(f"{self.properties.ultimate_tensile_strength:.2f}", color=COLORS['accent'])
                    dpg.add_input_float(default_value=999, width=80, tag="crit_uts_max", step=0)
                    dpg.add_text("PASS", color=COLORS['pass'], tag="crit_uts_status")
                
                # Elongation criteria
                with dpg.table_row():
                    dpg.add_text("Elongation (%)")
                    dpg.add_input_float(default_value=0, width=80, tag="crit_elong_min", step=0)
                    dpg.add_text(f"{self.properties.strain_at_break:.2f}", color=COLORS['accent'])
                    dpg.add_input_float(default_value=999, width=80, tag="crit_elong_max", step=0)
                    dpg.add_text("PASS", color=COLORS['pass'], tag="crit_elong_status")
                
                # Modulus criteria
                with dpg.table_row():
                    dpg.add_text("Young's Modulus (MPa)")
                    dpg.add_input_float(default_value=0, width=80, tag="crit_mod_min", step=0)
                    dpg.add_text(f"{self.properties.youngs_modulus:.1f}", color=COLORS['accent'])
                    dpg.add_input_float(default_value=99999, width=80, tag="crit_mod_max", step=0)
                    dpg.add_text("PASS", color=COLORS['pass'], tag="crit_mod_status")
            
            dpg.add_spacer(height=10)
            dpg.add_button(label="Evaluate Criteria", callback=self._evaluate_criteria)
            
            dpg.add_spacer(height=20)
            
            self._section_header("Overall Result")
            with dpg.group(horizontal=True):
                dpg.add_text("Overall Status:", color=COLORS['text_dim'])
                dpg.add_text("PASS", color=COLORS['pass'], tag="overall_pass_fail")
            
            dpg.add_spacer(height=15)
            
            self._section_header("Standard Compliance")
            if self.config:
                dpg.add_text(f"Test Standard: {self.config.metadata.test_standard.value}", 
                            color=COLORS['text_dim'])
            dpg.add_text("Note: Compliance with specific standards requires", color=COLORS['text_dim'])
            dpg.add_text("verification of specimen geometry, test speed, and", color=COLORS['text_dim'])
            dpg.add_text("environmental conditions per standard requirements.", color=COLORS['text_dim'])
    
    def _create_summary_tab(self, data: TestData):
        """Create summary tab."""
        with dpg.tab(label="Summary"):
            dpg.add_spacer(height=10)
            
            self._section_header("Test Information")
            
            with dpg.table(header_row=False, borders_innerV=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column()
                
                if self.config:
                    with dpg.table_row():
                        dpg.add_text("Sample ID:", color=COLORS['text_dim'])
                        dpg.add_text(self.config.metadata.sample_id or "N/A", color=COLORS['accent'])
                    
                    with dpg.table_row():
                        dpg.add_text("Material:", color=COLORS['text_dim'])
                        dpg.add_text(self.config.metadata.material_name or "N/A", color=COLORS['accent'])
                    
                    with dpg.table_row():
                        dpg.add_text("Operator:", color=COLORS['text_dim'])
                        dpg.add_text(self.config.metadata.operator_name or "N/A", color=COLORS['accent'])
                    
                    with dpg.table_row():
                        dpg.add_text("Standard:", color=COLORS['text_dim'])
                        dpg.add_text(self.config.metadata.test_standard.value, color=COLORS['accent'])
                
                with dpg.table_row():
                    dpg.add_text("Data Points:", color=COLORS['text_dim'])
                    dpg.add_text(str(len(data.forces)), color=COLORS['accent'])
                
                with dpg.table_row():
                    dpg.add_text("Test Duration:", color=COLORS['text_dim'])
                    duration = data.times[-1] if data.times else 0
                    dpg.add_text(f"{duration:.1f} s", color=COLORS['accent'])
            
            dpg.add_spacer(height=15)
            
            self._section_header("Key Results")
            
            with dpg.table(header_row=False, borders_innerV=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column()
                
                results = [
                    ("Ultimate Tensile Strength", f"{self.properties.ultimate_tensile_strength:.2f} MPa"),
                    ("Yield Strength (Rp0.2)", f"{self.properties.yield_strength_offset:.2f} MPa"),
                    ("Young's Modulus", f"{self.properties.youngs_modulus:.1f} MPa"),
                    ("Elongation at Break", f"{self.properties.strain_at_break:.2f} %"),
                    ("Maximum Force", f"{self.properties.max_force:.2f} N"),
                    ("Energy to Break", f"{self.properties.energy_to_break:.4f} J"),
                ]
                
                for label, value in results:
                    with dpg.table_row():
                        dpg.add_text(f"{label}:", color=COLORS['text_dim'])
                        dpg.add_text(value, color=COLORS['accent'])
    
    def _section_header(self, text: str):
        """Create a section header."""
        dpg.add_text(text, color=COLORS['header'])
        dpg.add_separator()
        dpg.add_spacer(height=5)
    
    def _property_row(self, name: str, symbol: str, value: str, unit: str):
        """Add a property row to a table."""
        with dpg.table_row():
            dpg.add_text(name)
            dpg.add_text(symbol, color=COLORS['text_dim'])
            dpg.add_text(value, color=COLORS['accent'])
            dpg.add_text(unit, color=COLORS['text_dim'])
    
    def _evaluate_criteria(self):
        """Evaluate pass/fail criteria."""
        all_pass = True
        
        # UTS
        uts_min = dpg.get_value("crit_uts_min")
        uts_max = dpg.get_value("crit_uts_max")
        uts_pass = uts_min <= self.properties.ultimate_tensile_strength <= uts_max
        dpg.set_value("crit_uts_status", "PASS" if uts_pass else "FAIL")
        dpg.configure_item("crit_uts_status", color=COLORS['pass'] if uts_pass else COLORS['fail'])
        all_pass = all_pass and uts_pass
        
        # Elongation
        elong_min = dpg.get_value("crit_elong_min")
        elong_max = dpg.get_value("crit_elong_max")
        elong_pass = elong_min <= self.properties.strain_at_break <= elong_max
        dpg.set_value("crit_elong_status", "PASS" if elong_pass else "FAIL")
        dpg.configure_item("crit_elong_status", color=COLORS['pass'] if elong_pass else COLORS['fail'])
        all_pass = all_pass and elong_pass
        
        # Modulus
        mod_min = dpg.get_value("crit_mod_min")
        mod_max = dpg.get_value("crit_mod_max")
        mod_pass = mod_min <= self.properties.youngs_modulus <= mod_max
        dpg.set_value("crit_mod_status", "PASS" if mod_pass else "FAIL")
        dpg.configure_item("crit_mod_status", color=COLORS['pass'] if mod_pass else COLORS['fail'])
        all_pass = all_pass and mod_pass
        
        # Overall
        dpg.set_value("overall_pass_fail", "PASS" if all_pass else "FAIL")
        dpg.configure_item("overall_pass_fail", color=COLORS['pass'] if all_pass else COLORS['fail'])
    
    def _on_export_csv(self):
        """Export to CSV."""
        if self.on_export:
            self.on_export("csv", self.properties, self.test_data, self.config)
    
    def _on_export_excel(self):
        """Export to Excel."""
        if self.on_export:
            self.on_export("excel", self.properties, self.test_data, self.config)
    
    def _on_export_pdf(self):
        """Export to PDF."""
        if self.on_export:
            self.on_export("pdf", self.properties, self.test_data, self.config)
    
    def get_properties(self) -> MechanicalProperties:
        """Get calculated properties."""
        return self.properties
