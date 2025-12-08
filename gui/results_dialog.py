#!/usr/bin/env python3
"""
Results Dialog

Post-test results display and export dialog.
Shows all mechanical properties and export options.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QTabWidget, QWidget, QPushButton, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox, QTextEdit, QCheckBox, QFrame,
    QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

import pyqtgraph as pg
import numpy as np

from config_model import TestConfiguration
from results_analyzer import MechanicalProperties, ResultsAnalyzer, FailureType, BreakLocation
from report_generator import ReportGenerator, ReportConfig


class ResultsDialog(QDialog):
    """Dialog for viewing and exporting test results."""
    
    def __init__(self, config: TestConfiguration, results: MechanicalProperties,
                 analyzer: ResultsAnalyzer, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.results = results
        self.analyzer = analyzer
        
        self.setWindowTitle("Test Results")
        self.setMinimumSize(1000, 700)
        
        self._create_ui()
        self._populate_results()
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header with test info
        header = QGroupBox("Test Information")
        header_layout = QHBoxLayout(header)
        
        info_labels = [
            f"Sample: {self.config.metadata.sample_id or '-'}",
            f"Standard: {self.config.metadata.test_standard.value.split(' - ')[0]}",
            f"Material: {self.config.metadata.material_name or self.config.metadata.material_type.value}",
            f"Date: {self.config.metadata.test_date.strftime('%Y-%m-%d %H:%M')}",
        ]
        for text in info_labels:
            lbl = QLabel(text)
            lbl.setStyleSheet("padding: 5px;")
            header_layout.addWidget(lbl)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_summary_tab(), "📊 Summary")
        self.tabs.addTab(self._create_properties_tab(), "📋 Properties")
        self.tabs.addTab(self._create_graphs_tab(), "📈 Graphs")
        self.tabs.addTab(self._create_data_tab(), "🔢 Data")
        self.tabs.addTab(self._create_export_tab(), "💾 Export")
        
        layout.addWidget(self.tabs)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    
    def _create_summary_tab(self) -> QWidget:
        """Create summary tab with key results."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left side - Key values
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        # Primary results
        primary_group = QGroupBox("Primary Results")
        primary_layout = QGridLayout(primary_group)
        
        self.uts_label = self._create_result_display(
            "Ultimate Tensile Strength", "0.00", "MPa", primary_layout, 0
        )
        self.yield_label = self._create_result_display(
            "Yield Strength (Rp0.2)", "0.00", "MPa", primary_layout, 1
        )
        self.modulus_label = self._create_result_display(
            "Young's Modulus", "0", "MPa", primary_layout, 2
        )
        self.elongation_label = self._create_result_display(
            "Elongation at Break", "0.00", "%", primary_layout, 3
        )
        
        left_layout.addWidget(primary_group)
        
        # Force results
        force_group = QGroupBox("Force Values")
        force_layout = QGridLayout(force_group)
        
        self.max_force_label = self._create_result_display(
            "Maximum Force", "0.00", "N", force_layout, 0
        )
        self.yield_force_label = self._create_result_display(
            "Force at Yield", "0.00", "N", force_layout, 1
        )
        self.break_force_label = self._create_result_display(
            "Force at Break", "0.00", "N", force_layout, 2
        )
        
        left_layout.addWidget(force_group)
        
        # Energy results
        energy_group = QGroupBox("Energy Values")
        energy_layout = QGridLayout(energy_group)
        
        self.energy_break_label = self._create_result_display(
            "Energy to Break", "0.000", "J", energy_layout, 0
        )
        self.energy_yield_label = self._create_result_display(
            "Energy to Yield", "0.000", "J", energy_layout, 1
        )
        
        left_layout.addWidget(energy_group)
        left_layout.addStretch()
        
        layout.addWidget(left)
        
        # Right side - Plot
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        # Stress-strain plot
        self.summary_plot = pg.PlotWidget()
        self.summary_plot.setBackground('#1a1a1a')
        self.summary_plot.setTitle("Stress-Strain Curve", color='w')
        self.summary_plot.setLabel('left', 'Stress', units='MPa', color='w')
        self.summary_plot.setLabel('bottom', 'Strain', units='%', color='w')
        self.summary_plot.showGrid(x=True, y=True, alpha=0.3)
        
        right_layout.addWidget(self.summary_plot)
        
        # Validity indicator
        validity_group = QGroupBox("Test Quality")
        validity_layout = QFormLayout(validity_group)
        
        self.validity_label = QLabel()
        validity_layout.addRow("Status:", self.validity_label)
        
        self.r2_label = QLabel()
        validity_layout.addRow("Modulus R²:", self.r2_label)
        
        self.failure_label = QLabel()
        validity_layout.addRow("Failure Type:", self.failure_label)
        
        self.notes_label = QLabel()
        self.notes_label.setWordWrap(True)
        validity_layout.addRow("Notes:", self.notes_label)
        
        right_layout.addWidget(validity_group)
        
        layout.addWidget(right)
        layout.setStretch(0, 1)
        layout.setStretch(1, 2)
        
        return widget
    
    def _create_result_display(self, label: str, value: str, unit: str,
                                layout: QGridLayout, row: int) -> QLabel:
        """Create a result display row."""
        layout.addWidget(QLabel(label + ":"), row, 0)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4fc3f7;")
        value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(value_label, row, 1)
        
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #888;")
        layout.addWidget(unit_label, row, 2)
        
        return value_label
    
    def _create_properties_tab(self) -> QWidget:
        """Create detailed properties tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Properties table
        self.props_table = QTableWidget()
        self.props_table.setColumnCount(3)
        self.props_table.setHorizontalHeaderLabels(["Property", "Value", "Unit"])
        self.props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.props_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.props_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.props_table)
        
        return widget
    
    def _create_graphs_tab(self) -> QWidget:
        """Create graphs tab with multiple plots."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Stress-Strain plot
        self.stress_strain_plot = pg.PlotWidget()
        self.stress_strain_plot.setBackground('#1a1a1a')
        self.stress_strain_plot.setTitle("Stress vs Strain", color='w')
        self.stress_strain_plot.setLabel('left', 'Stress', units='MPa', color='w')
        self.stress_strain_plot.setLabel('bottom', 'Strain', units='%', color='w')
        self.stress_strain_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.stress_strain_plot, 0, 0)
        
        # Force-Extension plot
        self.force_ext_plot = pg.PlotWidget()
        self.force_ext_plot.setBackground('#1a1a1a')
        self.force_ext_plot.setTitle("Force vs Extension", color='w')
        self.force_ext_plot.setLabel('left', 'Force', units='N', color='w')
        self.force_ext_plot.setLabel('bottom', 'Extension', units='mm', color='w')
        self.force_ext_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.force_ext_plot, 0, 1)
        
        # True Stress-Strain plot
        self.true_ss_plot = pg.PlotWidget()
        self.true_ss_plot.setBackground('#1a1a1a')
        self.true_ss_plot.setTitle("True Stress vs True Strain", color='w')
        self.true_ss_plot.setLabel('left', 'True Stress', units='MPa', color='w')
        self.true_ss_plot.setLabel('bottom', 'True Strain', color='w')
        self.true_ss_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.true_ss_plot, 1, 0)
        
        # Time plots
        self.time_plot = pg.PlotWidget()
        self.time_plot.setBackground('#1a1a1a')
        self.time_plot.setTitle("Force & Stress vs Time", color='w')
        self.time_plot.setLabel('left', 'Value', color='w')
        self.time_plot.setLabel('bottom', 'Time', units='s', color='w')
        self.time_plot.showGrid(x=True, y=True, alpha=0.3)
        self.time_plot.addLegend()
        layout.addWidget(self.time_plot, 1, 1)
        
        return widget
    
    def _create_data_tab(self) -> QWidget:
        """Create raw data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels([
            "Time (s)", "Force (N)", "Extension (mm)", "Displacement (mm)",
            "Stress (MPa)", "Strain", "Strain (%)"
        ])
        self.data_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.data_table)
        
        # Data stats
        stats_layout = QHBoxLayout()
        self.data_points_label = QLabel("Data Points: 0")
        stats_layout.addWidget(self.data_points_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        return widget
    
    def _create_export_tab(self) -> QWidget:
        """Create export options tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export formats
        formats_group = QGroupBox("Export Formats")
        formats_layout = QGridLayout(formats_group)
        
        # Excel
        excel_btn = QPushButton("📊 Export to Excel (.xlsx)")
        excel_btn.setMinimumHeight(50)
        excel_btn.clicked.connect(lambda: self._export("excel"))
        formats_layout.addWidget(excel_btn, 0, 0)
        
        excel_desc = QLabel("Complete report with Test Info, Results, and Raw Data sheets")
        excel_desc.setStyleSheet("color: #888;")
        formats_layout.addWidget(excel_desc, 0, 1)
        
        # CSV
        csv_btn = QPushButton("📄 Export to CSV (.csv)")
        csv_btn.setMinimumHeight(50)
        csv_btn.clicked.connect(lambda: self._export("csv"))
        formats_layout.addWidget(csv_btn, 1, 0)
        
        csv_desc = QLabel("Raw test data for import into other software")
        csv_desc.setStyleSheet("color: #888;")
        formats_layout.addWidget(csv_desc, 1, 1)
        
        # PDF
        pdf_btn = QPushButton("📑 Export to PDF (.pdf)")
        pdf_btn.setMinimumHeight(50)
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        formats_layout.addWidget(pdf_btn, 2, 0)
        
        pdf_desc = QLabel("Professional test report with plots and results table")
        pdf_desc.setStyleSheet("color: #888;")
        formats_layout.addWidget(pdf_desc, 2, 1)
        
        # JSON
        json_btn = QPushButton("🔗 Export to JSON (.json)")
        json_btn.setMinimumHeight(50)
        json_btn.clicked.connect(lambda: self._export("json"))
        formats_layout.addWidget(json_btn, 3, 0)
        
        json_desc = QLabel("Structured data for LIMS/API integration")
        json_desc.setStyleSheet("color: #888;")
        formats_layout.addWidget(json_desc, 3, 1)
        
        # XML
        xml_btn = QPushButton("📦 Export to XML (.xml)")
        xml_btn.setMinimumHeight(50)
        xml_btn.clicked.connect(lambda: self._export("xml"))
        formats_layout.addWidget(xml_btn, 4, 0)
        
        xml_desc = QLabel("Structured data for ERP/MES integration")
        xml_desc.setStyleSheet("color: #888;")
        formats_layout.addWidget(xml_desc, 4, 1)
        
        layout.addWidget(formats_group)
        
        # Export all
        all_group = QGroupBox("Batch Export")
        all_layout = QVBoxLayout(all_group)
        
        all_btn = QPushButton("💾 Export All Formats")
        all_btn.setMinimumHeight(50)
        all_btn.clicked.connect(self._export_all)
        all_layout.addWidget(all_btn)
        
        all_desc = QLabel("Export to all formats at once (Excel, CSV, PDF, JSON, XML)")
        all_desc.setStyleSheet("color: #888;")
        all_layout.addWidget(all_desc)
        
        layout.addWidget(all_group)
        layout.addStretch()
        
        return widget
    
    def _populate_results(self):
        """Populate all results displays."""
        r = self.results
        
        # Summary tab
        self.uts_label.setText(f"{r.ultimate_tensile_strength:.2f}")
        self.yield_label.setText(f"{r.yield_strength_offset:.2f}")
        self.modulus_label.setText(f"{r.youngs_modulus:.0f}")
        self.elongation_label.setText(f"{r.elongation_at_break:.2f}")
        
        self.max_force_label.setText(f"{r.max_force:.2f}")
        self.yield_force_label.setText(f"{r.force_at_yield:.2f}")
        self.break_force_label.setText(f"{r.force_at_break:.2f}")
        
        self.energy_break_label.setText(f"{r.energy_to_break:.3f}")
        self.energy_yield_label.setText(f"{r.energy_to_yield:.3f}")
        
        # Validity
        if r.is_valid_test:
            self.validity_label.setText("✅ VALID")
            self.validity_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self.validity_label.setText("⚠️ INVALID")
            self.validity_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
        self.r2_label.setText(f"{r.modulus_r_squared:.4f}")
        self.failure_label.setText(r.failure_type.value)
        self.notes_label.setText(r.validity_notes or "None")
        
        # Summary plot
        strain, stress = self.analyzer.get_stress_strain_data()
        self.summary_plot.plot(strain * 100, stress, pen=pg.mkPen('#4fc3f7', width=2))
        
        # Mark UTS
        uts_idx = np.argmax(stress)
        self.summary_plot.plot([strain[uts_idx] * 100], [stress[uts_idx]], 
                               pen=None, symbol='o', symbolBrush='r', symbolSize=10)
        
        # Properties table
        properties = [
            ("Ultimate Tensile Strength", f"{r.ultimate_tensile_strength:.2f}", "MPa"),
            ("Yield Strength (Rp0.2)", f"{r.yield_strength_offset:.2f}", "MPa"),
            ("Young's Modulus", f"{r.youngs_modulus:.0f}", "MPa"),
            ("Elongation at Break", f"{r.elongation_at_break:.2f}", "%"),
            ("Strain at Yield", f"{r.strain_at_yield * 100:.3f}", "%"),
            ("Strain at UTS", f"{r.strain_at_uts * 100:.3f}", "%"),
            ("Uniform Elongation", f"{r.uniform_elongation:.2f}", "%"),
            ("Maximum Force", f"{r.max_force:.2f}", "N"),
            ("Force at Yield", f"{r.force_at_yield:.2f}", "N"),
            ("Force at Break", f"{r.force_at_break:.2f}", "N"),
            ("Extension at Yield", f"{r.extension_at_yield:.3f}", "mm"),
            ("Extension at UTS", f"{r.extension_at_uts:.3f}", "mm"),
            ("Extension at Break", f"{r.extension_at_break:.3f}", "mm"),
            ("Energy to Yield", f"{r.energy_to_yield:.4f}", "J"),
            ("Energy to UTS", f"{r.energy_to_uts:.4f}", "J"),
            ("Energy to Break", f"{r.energy_to_break:.4f}", "J"),
            ("True Stress at UTS", f"{r.true_stress_at_uts:.2f}", "MPa"),
            ("True Strain at UTS", f"{r.true_strain_at_uts:.4f}", ""),
            ("Failure Type", r.failure_type.value, ""),
            ("Break Location", r.break_location.value, ""),
            ("Modulus R²", f"{r.modulus_r_squared:.4f}", ""),
        ]
        
        self.props_table.setRowCount(len(properties))
        for i, (prop, value, unit) in enumerate(properties):
            self.props_table.setItem(i, 0, QTableWidgetItem(prop))
            self.props_table.setItem(i, 1, QTableWidgetItem(value))
            self.props_table.setItem(i, 2, QTableWidgetItem(unit))
        
        # Graphs
        # Stress-Strain
        self.stress_strain_plot.plot(strain * 100, stress, pen=pg.mkPen('#4fc3f7', width=2))
        
        # Force-Extension
        extension, force = self.analyzer.get_force_extension_data()
        self.force_ext_plot.plot(extension, force, pen=pg.mkPen('#81c784', width=2))
        
        # True Stress-Strain
        true_strain, true_stress = self.analyzer.get_true_stress_strain_data()
        self.true_ss_plot.plot(true_strain, true_stress, pen=pg.mkPen('#ffb74d', width=2))
        
        # Time plots
        time = np.array(self.analyzer.time_data)
        self.time_plot.plot(time, force, pen=pg.mkPen('#4fc3f7', width=1.5), name='Force (N)')
        self.time_plot.plot(time, stress * 10, pen=pg.mkPen('#f48fb1', width=1.5), name='Stress x10 (MPa)')
        
        # Data table - limit to first/last 500 rows for performance
        data = self.analyzer.data
        total_points = len(data)
        
        # Sample data if too many points
        if total_points > 1000:
            # Show first 500 and last 500
            display_data = data[:500] + data[-500:]
            show_gap = True
        else:
            display_data = data
            show_gap = False
        
        self.data_table.setUpdatesEnabled(False)  # Disable updates for speed
        self.data_table.setRowCount(len(display_data) + (1 if show_gap else 0))
        
        for i, d in enumerate(display_data[:500] if show_gap else display_data):
            self.data_table.setItem(i, 0, QTableWidgetItem(f"{d.time:.3f}"))
            self.data_table.setItem(i, 1, QTableWidgetItem(f"{d.force:.2f}"))
            self.data_table.setItem(i, 2, QTableWidgetItem(f"{d.extension:.4f}"))
            self.data_table.setItem(i, 3, QTableWidgetItem(f"{d.displacement:.4f}"))
            self.data_table.setItem(i, 4, QTableWidgetItem(f"{d.stress:.3f}"))
            self.data_table.setItem(i, 5, QTableWidgetItem(f"{d.strain:.6f}"))
            self.data_table.setItem(i, 6, QTableWidgetItem(f"{d.strain * 100:.4f}"))
        
        if show_gap:
            # Add gap indicator row
            gap_row = 500
            gap_text = f"... {total_points - 1000} rows hidden ..."
            self.data_table.setItem(gap_row, 0, QTableWidgetItem(gap_text))
            for col in range(1, 7):
                self.data_table.setItem(gap_row, col, QTableWidgetItem(""))
            
            # Add last 500 rows
            for i, d in enumerate(display_data[500:]):
                row = 501 + i
                self.data_table.setItem(row, 0, QTableWidgetItem(f"{d.time:.3f}"))
                self.data_table.setItem(row, 1, QTableWidgetItem(f"{d.force:.2f}"))
                self.data_table.setItem(row, 2, QTableWidgetItem(f"{d.extension:.4f}"))
                self.data_table.setItem(row, 3, QTableWidgetItem(f"{d.displacement:.4f}"))
                self.data_table.setItem(row, 4, QTableWidgetItem(f"{d.stress:.3f}"))
                self.data_table.setItem(row, 5, QTableWidgetItem(f"{d.strain:.6f}"))
                self.data_table.setItem(row, 6, QTableWidgetItem(f"{d.strain * 100:.4f}"))
        
        self.data_table.setUpdatesEnabled(True)  # Re-enable updates
        self.data_points_label.setText(f"Data Points: {total_points}" + 
                                        (f" (showing {len(display_data)})" if show_gap else ""))
    
    def _export(self, format_type: str):
        """Export results in specified format."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample = self.config.metadata.sample_id or "test"
        
        filters = {
            "excel": ("Excel Files (*.xlsx)", f"{sample}_{timestamp}.xlsx"),
            "csv": ("CSV Files (*.csv)", f"{sample}_{timestamp}.csv"),
            "pdf": ("PDF Files (*.pdf)", f"{sample}_{timestamp}.pdf"),
            "json": ("JSON Files (*.json)", f"{sample}_{timestamp}.json"),
            "xml": ("XML Files (*.xml)", f"{sample}_{timestamp}.xml"),
        }
        
        file_filter, default_name = filters.get(format_type, ("All Files (*)", "export"))
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Export to {format_type.upper()}", default_name, file_filter
        )
        
        if not filepath:
            return
        
        try:
            generator = ReportGenerator(self.config, self.results, self.analyzer)
            
            if format_type == "excel":
                generator.generate_excel(filepath)
            elif format_type == "csv":
                generator.generate_csv(filepath)
            elif format_type == "pdf":
                generator.generate_pdf(filepath)
            elif format_type == "json":
                generator.generate_json(filepath)
            elif format_type == "xml":
                generator.generate_xml(filepath)
            
            QMessageBox.information(self, "Export Complete", f"Results exported to:\n{filepath}")
            
        except ImportError as e:
            QMessageBox.warning(self, "Missing Dependency", 
                              f"Required package not installed:\n{str(e)}\n\n"
                              "Install with: pip install reportlab matplotlib")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")
    
    def _export_all(self):
        """Export to all formats."""
        from datetime import datetime
        import os
        
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if not folder:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample = self.config.metadata.sample_id or "test"
        base_name = f"{sample}_{timestamp}"
        
        try:
            generator = ReportGenerator(self.config, self.results, self.analyzer)
            
            # Export all formats
            generator.generate_excel(os.path.join(folder, f"{base_name}.xlsx"))
            generator.generate_csv(os.path.join(folder, f"{base_name}.csv"))
            generator.generate_json(os.path.join(folder, f"{base_name}.json"))
            generator.generate_xml(os.path.join(folder, f"{base_name}.xml"))
            
            try:
                generator.generate_pdf(os.path.join(folder, f"{base_name}.pdf"))
            except ImportError:
                pass  # PDF requires optional reportlab
            
            QMessageBox.information(self, "Export Complete", 
                                   f"All formats exported to:\n{folder}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")
