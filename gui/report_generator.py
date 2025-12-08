#!/usr/bin/env python3
"""
Report Generator Module

Generates professional test reports in PDF, Excel, and other formats.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np

# PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, HRFlowable
    )
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.charts.legends import Legend
    from reportlab.graphics.widgets.markers import makeMarker
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Excel generation
import pandas as pd

# For plot export
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from config_model import TestConfiguration
from results_analyzer import MechanicalProperties, ResultsAnalyzer


@dataclass
class ReportConfig:
    """Report generation configuration."""
    include_logo: bool = True
    logo_path: str = ""
    company_name: str = "Tensile Test Laboratory"
    company_address: str = ""
    include_raw_data: bool = False
    include_plots: bool = True
    include_notes: bool = True
    include_signature: bool = True
    page_size: str = "A4"  # "A4" or "Letter"
    language: str = "en"


class ReportGenerator:
    """
    Generates professional test reports in various formats.
    """
    
    def __init__(self, config: TestConfiguration, results: MechanicalProperties,
                 analyzer: ResultsAnalyzer, report_config: ReportConfig = None):
        """
        Initialize report generator.
        
        Args:
            config: Test configuration
            results: Calculated mechanical properties
            analyzer: Results analyzer with test data
            report_config: Report generation settings
        """
        self.config = config
        self.results = results
        self.analyzer = analyzer
        self.report_config = report_config or ReportConfig()
        
    def generate_pdf(self, filepath: str) -> bool:
        """
        Generate PDF test report.
        
        Args:
            filepath: Output PDF file path
            
        Returns:
            True if successful
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab not installed. Run: pip install reportlab")
        
        # Set page size
        page_size = A4 if self.report_config.page_size == "A4" else letter
        
        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6
        )
        
        # Header
        story.append(Paragraph(self.report_config.company_name, title_style))
        story.append(Paragraph("TENSILE TEST REPORT", title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Spacer(1, 12))
        
        # Test Information
        story.append(Paragraph("Test Information", heading_style))
        test_info = [
            ["Parameter", "Value"],
            ["Test Standard", self.config.metadata.test_standard.value],
            ["Sample ID", self.config.metadata.sample_id or "-"],
            ["Batch ID", self.config.metadata.batch_id or "-"],
            ["Operator", self.config.metadata.operator_name or "-"],
            ["Customer", self.config.metadata.customer_name or "-"],
            ["Project", self.config.metadata.project_name or "-"],
            ["Test Date", self.config.metadata.test_date.strftime("%Y-%m-%d %H:%M")],
            ["Material", f"{self.config.metadata.material_type.value} - {self.config.metadata.material_name}"],
        ]
        story.append(self._create_table(test_info))
        story.append(Spacer(1, 12))
        
        # Specimen Information
        story.append(Paragraph("Specimen Geometry", heading_style))
        specimen_info = [
            ["Parameter", "Value", "Unit"],
            ["Gauge Length", f"{self.config.specimen.gauge_length:.2f}", "mm"],
            ["Thickness", f"{self.config.specimen.thickness:.3f}", "mm"],
            ["Width", f"{self.config.specimen.width:.3f}", "mm"],
            ["Cross-Section Area", f"{self.config.specimen.cross_section_area:.4f}", "mm²"],
            ["Shape", self.config.specimen.shape.value, ""],
        ]
        story.append(self._create_table(specimen_info))
        story.append(Spacer(1, 12))
        
        # Test Results
        story.append(Paragraph("Test Results", heading_style))
        results_data = [
            ["Property", "Value", "Unit"],
            ["Ultimate Tensile Strength (UTS)", f"{self.results.ultimate_tensile_strength:.2f}", "MPa"],
            ["Yield Strength (Rp0.2)", f"{self.results.yield_strength_offset:.2f}", "MPa"],
            ["Young's Modulus (E)", f"{self.results.youngs_modulus:.0f}", "MPa"],
            ["Elongation at Break", f"{self.results.elongation_at_break:.2f}", "%"],
            ["Maximum Force", f"{self.results.max_force:.2f}", "N"],
            ["Force at Break", f"{self.results.force_at_break:.2f}", "N"],
            ["Extension at Break", f"{self.results.extension_at_break:.3f}", "mm"],
            ["Energy to Break", f"{self.results.energy_to_break:.3f}", "J"],
            ["Failure Type", self.results.failure_type.value, ""],
        ]
        story.append(self._create_table(results_data))
        story.append(Spacer(1, 12))
        
        # Quality Information
        story.append(Paragraph("Quality Assessment", heading_style))
        quality_info = [
            ["Parameter", "Value"],
            ["Test Valid", "Yes" if self.results.is_valid_test else "No"],
            ["Modulus R²", f"{self.results.modulus_r_squared:.4f}"],
            ["Notes", self.results.validity_notes or "-"],
        ]
        story.append(self._create_table(quality_info))
        story.append(Spacer(1, 12))
        
        # Plot (if matplotlib available)
        if self.report_config.include_plots and MATPLOTLIB_AVAILABLE:
            plot_path = filepath.replace('.pdf', '_plot.png')
            if self._generate_plot(plot_path):
                story.append(Paragraph("Stress-Strain Curve", heading_style))
                img = Image(plot_path, width=160*mm, height=100*mm)
                story.append(img)
                story.append(Spacer(1, 12))
        
        # Notes
        if self.report_config.include_notes and self.config.metadata.notes:
            story.append(Paragraph("Notes", heading_style))
            story.append(Paragraph(self.config.metadata.notes, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Signature
        if self.report_config.include_signature:
            story.append(Spacer(1, 30))
            sig_data = [
                ["Tested By:", "_" * 30, "Date:", "_" * 20],
                ["Approved By:", "_" * 30, "Date:", "_" * 20],
            ]
            sig_table = Table(sig_data, colWidths=[25*mm, 60*mm, 15*mm, 40*mm])
            sig_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            story.append(sig_table)
        
        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        footer_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Tensile Tester v2.0"
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=8, textColor=colors.grey)))
        
        # Build PDF
        doc.build(story)
        
        # Clean up temp plot
        if MATPLOTLIB_AVAILABLE:
            plot_path = filepath.replace('.pdf', '_plot.png')
            if os.path.exists(plot_path):
                os.remove(plot_path)
        
        return True
    
    def _create_table(self, data: List[List[str]]):
        """Create a formatted table."""
        table = Table(data)
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        
        # Alternate row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.Color(0.9, 0.9, 0.9))
        
        table.setStyle(style)
        return table
    
    def _generate_plot(self, filepath: str) -> bool:
        """Generate stress-strain plot image."""
        if not MATPLOTLIB_AVAILABLE:
            return False
        
        try:
            strain, stress = self.analyzer.get_stress_strain_data()
            
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Main curve
            ax.plot(strain * 100, stress, 'b-', linewidth=1.5, label='Stress-Strain')
            
            # Mark key points
            # UTS
            uts_idx = np.argmax(stress)
            ax.plot(strain[uts_idx] * 100, stress[uts_idx], 'ro', markersize=8, label=f'UTS: {stress[uts_idx]:.1f} MPa')
            
            # Yield point (if found)
            if self.results.yield_strength_offset > 0:
                ax.plot(self.results.strain_at_yield * 100, self.results.yield_strength_offset, 
                       'g^', markersize=8, label=f'Yield: {self.results.yield_strength_offset:.1f} MPa')
            
            # Modulus line
            if self.results.youngs_modulus > 0:
                x_mod = np.array([0, 0.5])
                y_mod = self.results.youngs_modulus * x_mod / 100
                ax.plot(x_mod, y_mod, 'k--', alpha=0.5, label=f'E = {self.results.youngs_modulus:.0f} MPa')
            
            ax.set_xlabel('Strain (%)', fontsize=11)
            ax.set_ylabel('Stress (MPa)', fontsize=11)
            ax.set_title('Engineering Stress-Strain Curve', fontsize=12)
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"Plot generation error: {e}")
            return False
    
    def generate_excel(self, filepath: str) -> bool:
        """
        Generate comprehensive Excel report with multiple sheets.
        
        Args:
            filepath: Output Excel file path
            
        Returns:
            True if successful
        """
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Test Information
            test_info = {
                'Parameter': [
                    'Test Standard', 'Sample ID', 'Batch ID', 'Operator',
                    'Customer', 'Project', 'Test Date', 'Material Type',
                    'Material Name', 'Gauge Length (mm)', 'Thickness (mm)',
                    'Width (mm)', 'Cross-Section Area (mm²)', 'Specimen Shape',
                    'Temperature (°C)', 'Humidity (%RH)'
                ],
                'Value': [
                    self.config.metadata.test_standard.value,
                    self.config.metadata.sample_id,
                    self.config.metadata.batch_id,
                    self.config.metadata.operator_name,
                    self.config.metadata.customer_name,
                    self.config.metadata.project_name,
                    self.config.metadata.test_date.strftime("%Y-%m-%d %H:%M:%S"),
                    self.config.metadata.material_type.value,
                    self.config.metadata.material_name,
                    self.config.specimen.gauge_length,
                    self.config.specimen.thickness,
                    self.config.specimen.width,
                    self.config.specimen.cross_section_area,
                    self.config.specimen.shape.value,
                    self.config.environment.temperature,
                    self.config.environment.humidity
                ]
            }
            pd.DataFrame(test_info).to_excel(writer, sheet_name='Test Info', index=False)
            
            # Sheet 2: Results Summary
            results_data = {
                'Property': [
                    'Ultimate Tensile Strength (UTS)',
                    'Yield Strength (Rp0.2)',
                    "Young's Modulus (E)",
                    'Elongation at Break',
                    'Strain at Yield',
                    'Strain at UTS',
                    'Uniform Elongation',
                    'Maximum Force',
                    'Force at Yield',
                    'Force at Break',
                    'Extension at Break',
                    'Energy to Yield',
                    'Energy to UTS',
                    'Energy to Break (Toughness)',
                    'True Stress at UTS',
                    'True Strain at UTS',
                    'Failure Type',
                    'Break Location',
                    'Modulus R²',
                    'Test Valid',
                    'Notes'
                ],
                'Value': [
                    self.results.ultimate_tensile_strength,
                    self.results.yield_strength_offset,
                    self.results.youngs_modulus,
                    self.results.elongation_at_break,
                    self.results.strain_at_yield * 100,
                    self.results.strain_at_uts * 100,
                    self.results.uniform_elongation,
                    self.results.max_force,
                    self.results.force_at_yield,
                    self.results.force_at_break,
                    self.results.extension_at_break,
                    self.results.energy_to_yield,
                    self.results.energy_to_uts,
                    self.results.energy_to_break,
                    self.results.true_stress_at_uts,
                    self.results.true_strain_at_uts,
                    self.results.failure_type.value,
                    self.results.break_location.value,
                    self.results.modulus_r_squared,
                    'Yes' if self.results.is_valid_test else 'No',
                    self.results.validity_notes
                ],
                'Unit': [
                    'MPa', 'MPa', 'MPa', '%', '%', '%', '%',
                    'N', 'N', 'N', 'mm', 'J', 'J', 'J',
                    'MPa', '', '', '', '', '', ''
                ]
            }
            pd.DataFrame(results_data).to_excel(writer, sheet_name='Results', index=False)
            
            # Sheet 3: Raw Data
            raw_data = {
                'Time (s)': self.analyzer.time_data,
                'Force (N)': self.analyzer.force_data,
                'Extension (mm)': self.analyzer.extension_data,
                'Displacement (mm)': self.analyzer.displacement_data,
                'Stress (MPa)': self.analyzer.stress_data,
                'Strain': self.analyzer.strain_data,
                'Strain (%)': [s * 100 for s in self.analyzer.strain_data]
            }
            pd.DataFrame(raw_data).to_excel(writer, sheet_name='Raw Data', index=False)
            
            # Sheet 4: True Stress-Strain
            true_strain, true_stress = self.analyzer.get_true_stress_strain_data()
            true_data = {
                'True Strain': true_strain.tolist(),
                'True Stress (MPa)': true_stress.tolist()
            }
            pd.DataFrame(true_data).to_excel(writer, sheet_name='True Stress-Strain', index=False)
        
        return True
    
    def generate_csv(self, filepath: str) -> bool:
        """
        Generate CSV file with raw test data.
        
        Args:
            filepath: Output CSV file path
            
        Returns:
            True if successful
        """
        data = {
            'Time (s)': self.analyzer.time_data,
            'Force (N)': self.analyzer.force_data,
            'Extension (mm)': self.analyzer.extension_data,
            'Displacement (mm)': self.analyzer.displacement_data,
            'Stress (MPa)': self.analyzer.stress_data,
            'Strain': self.analyzer.strain_data,
            'Strain (%)': [s * 100 for s in self.analyzer.strain_data]
        }
        pd.DataFrame(data).to_csv(filepath, index=False)
        return True
    
    def generate_json(self, filepath: str) -> bool:
        """
        Generate JSON file for LIMS/API integration.
        
        Args:
            filepath: Output JSON file path
            
        Returns:
            True if successful
        """
        import json
        
        output = {
            "metadata": {
                "test_standard": self.config.metadata.test_standard.name,
                "sample_id": self.config.metadata.sample_id,
                "batch_id": self.config.metadata.batch_id,
                "operator": self.config.metadata.operator_name,
                "customer": self.config.metadata.customer_name,
                "project": self.config.metadata.project_name,
                "test_date": self.config.metadata.test_date.isoformat(),
                "material_type": self.config.metadata.material_type.name,
                "material_name": self.config.metadata.material_name
            },
            "specimen": {
                "gauge_length_mm": self.config.specimen.gauge_length,
                "thickness_mm": self.config.specimen.thickness,
                "width_mm": self.config.specimen.width,
                "cross_section_area_mm2": self.config.specimen.cross_section_area,
                "shape": self.config.specimen.shape.name
            },
            "results": {
                "ultimate_tensile_strength_mpa": self.results.ultimate_tensile_strength,
                "yield_strength_mpa": self.results.yield_strength_offset,
                "youngs_modulus_mpa": self.results.youngs_modulus,
                "elongation_at_break_percent": self.results.elongation_at_break,
                "max_force_n": self.results.max_force,
                "force_at_break_n": self.results.force_at_break,
                "energy_to_break_j": self.results.energy_to_break,
                "failure_type": self.results.failure_type.name,
                "test_valid": self.results.is_valid_test,
                "modulus_r_squared": self.results.modulus_r_squared
            },
            "data_points": len(self.analyzer.data),
            "generated": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        return True
    
    def generate_xml(self, filepath: str) -> bool:
        """
        Generate XML file for ERP/MES integration.
        
        Args:
            filepath: Output XML file path
            
        Returns:
            True if successful
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        root = ET.Element("TensileTestReport")
        root.set("version", "1.0")
        root.set("generated", datetime.now().isoformat())
        
        # Metadata
        metadata = ET.SubElement(root, "Metadata")
        ET.SubElement(metadata, "TestStandard").text = self.config.metadata.test_standard.name
        ET.SubElement(metadata, "SampleID").text = self.config.metadata.sample_id
        ET.SubElement(metadata, "BatchID").text = self.config.metadata.batch_id
        ET.SubElement(metadata, "Operator").text = self.config.metadata.operator_name
        ET.SubElement(metadata, "TestDate").text = self.config.metadata.test_date.isoformat()
        
        # Specimen
        specimen = ET.SubElement(root, "Specimen")
        ET.SubElement(specimen, "GaugeLength", unit="mm").text = str(self.config.specimen.gauge_length)
        ET.SubElement(specimen, "Thickness", unit="mm").text = str(self.config.specimen.thickness)
        ET.SubElement(specimen, "Width", unit="mm").text = str(self.config.specimen.width)
        ET.SubElement(specimen, "CrossSectionArea", unit="mm2").text = str(self.config.specimen.cross_section_area)
        
        # Results
        results = ET.SubElement(root, "Results")
        ET.SubElement(results, "UltimateTensileStrength", unit="MPa").text = f"{self.results.ultimate_tensile_strength:.2f}"
        ET.SubElement(results, "YieldStrength", unit="MPa").text = f"{self.results.yield_strength_offset:.2f}"
        ET.SubElement(results, "YoungsModulus", unit="MPa").text = f"{self.results.youngs_modulus:.0f}"
        ET.SubElement(results, "ElongationAtBreak", unit="percent").text = f"{self.results.elongation_at_break:.2f}"
        ET.SubElement(results, "MaxForce", unit="N").text = f"{self.results.max_force:.2f}"
        ET.SubElement(results, "EnergyToBreak", unit="J").text = f"{self.results.energy_to_break:.3f}"
        ET.SubElement(results, "FailureType").text = self.results.failure_type.name
        ET.SubElement(results, "TestValid").text = str(self.results.is_valid_test).lower()
        
        # Pretty print
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(filepath, 'w') as f:
            f.write(xml_str)
        
        return True
