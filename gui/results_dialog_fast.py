#!/usr/bin/env python3
"""
Fast Results Dialog

Optimized post-test results display using:
- Pre-calculated numpy arrays (no conversion overhead)
- Downsampled plots (max 500 points for smooth rendering)
- Lazy tab loading (only load when viewed)
- No table widget (use text display instead)
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QWidget, QPushButton, QLabel, QGroupBox,
    QFileDialog, QMessageBox, QTextEdit, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import pyqtgraph as pg
import numpy as np

from config_model import TestConfiguration
from results_analyzer import MechanicalProperties, ResultsAnalyzer


def downsample(x, y, max_points=500):
    """Downsample data to max_points using LTTB-like algorithm."""
    n = len(x)
    if n <= max_points:
        return x, y
    
    # Simple uniform downsampling with key point preservation
    step = n // max_points
    indices = list(range(0, n, step))
    
    # Always include max force point
    max_idx = int(np.argmax(y))
    if max_idx not in indices:
        indices.append(max_idx)
    
    # Always include last point
    if n - 1 not in indices:
        indices.append(n - 1)
    
    indices = sorted(set(indices))
    return x[indices], y[indices]


class FastResultsDialog(QDialog):
    """Fast dialog for viewing test results."""
    
    def __init__(self, config: TestConfiguration, results: MechanicalProperties,
                 stress: np.ndarray, strain: np.ndarray, force: np.ndarray, 
                 extension: np.ndarray, time: np.ndarray, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.results = results
        
        # Store pre-converted numpy arrays
        self.stress = stress
        self.strain = strain
        self.force = force
        self.extension = extension
        self.time = time
        
        # Lazy loading flags
        self._graphs_loaded = False
        self._data_loaded = False
        
        self.setWindowTitle("Test Results")
        self.setMinimumSize(900, 600)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header - simple labels
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        c = self.config
        header_layout.addWidget(QLabel(f"<b>Sample:</b> {c.metadata.sample_id or '-'}"))
        header_layout.addWidget(QLabel(f"<b>Material:</b> {c.metadata.material_name or c.metadata.material_type.value}"))
        header_layout.addWidget(QLabel(f"<b>Points:</b> {len(self.force)}"))
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Tab widget with lazy loading
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Summary tab - loads immediately (fast)
        self.tabs.addTab(self._create_summary_tab(), "📊 Results")
        
        # Graphs tab - lazy load
        self.graphs_widget = QWidget()
        self.tabs.addTab(self.graphs_widget, "📈 Graphs")
        
        # Data tab - lazy load
        self.data_widget = QWidget()
        self.tabs.addTab(self.data_widget, "🔢 Data")
        
        # Export tab
        self.tabs.addTab(self._create_export_tab(), "💾 Export")
        
        layout.addWidget(self.tabs)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    
    def _on_tab_changed(self, index):
        """Lazy load tabs when first viewed."""
        if index == 1 and not self._graphs_loaded:
            self._load_graphs_tab()
            self._graphs_loaded = True
        elif index == 2 and not self._data_loaded:
            self._load_data_tab()
            self._data_loaded = True
    
    def _create_summary_tab(self) -> QWidget:
        """Create summary tab with key results - fast, no heavy operations."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left - Results
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        r = self.results
        
        # Primary results
        primary = QGroupBox("Strength Properties")
        primary_layout = QGridLayout(primary)
        self._add_result_row(primary_layout, 0, "Ultimate Tensile Strength", f"{r.ultimate_tensile_strength:.2f}", "MPa")
        self._add_result_row(primary_layout, 1, "Yield Strength (Rp0.2)", f"{r.yield_strength_offset:.2f}", "MPa")
        self._add_result_row(primary_layout, 2, "Young's Modulus", f"{r.youngs_modulus:.0f}", "MPa")
        self._add_result_row(primary_layout, 3, "Elongation at Break", f"{r.elongation_at_break:.2f}", "%")
        left_layout.addWidget(primary)
        
        # Force values
        forces = QGroupBox("Force Values")
        forces_layout = QGridLayout(forces)
        self._add_result_row(forces_layout, 0, "Maximum Force", f"{r.max_force:.2f}", "N")
        self._add_result_row(forces_layout, 1, "Force at Yield", f"{r.force_at_yield:.2f}", "N")
        self._add_result_row(forces_layout, 2, "Force at Break", f"{r.force_at_break:.2f}", "N")
        left_layout.addWidget(forces)
        
        # Energy
        energy = QGroupBox("Energy")
        energy_layout = QGridLayout(energy)
        self._add_result_row(energy_layout, 0, "Energy to Break", f"{r.energy_to_break:.4f}", "J")
        self._add_result_row(energy_layout, 1, "Modulus R²", f"{r.modulus_r_squared:.4f}", "")
        left_layout.addWidget(energy)
        
        left_layout.addStretch()
        layout.addWidget(left)
        
        # Right - Quick plot (downsampled)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        plot = pg.PlotWidget()
        plot.setBackground('#1a1a1a')
        plot.setTitle("Stress-Strain Curve", color='w', size='12pt')
        plot.setLabel('left', 'Stress', units='MPa', color='w')
        plot.setLabel('bottom', 'Strain', units='%', color='w')
        plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Downsample for fast plotting
        strain_ds, stress_ds = downsample(self.strain * 100, self.stress, max_points=300)
        plot.plot(strain_ds, stress_ds, pen=pg.mkPen('#4fc3f7', width=2))
        
        # Mark UTS
        uts_idx = np.argmax(self.stress)
        plot.plot([self.strain[uts_idx] * 100], [self.stress[uts_idx]], 
                  pen=None, symbol='o', symbolBrush='#f44336', symbolSize=10)
        
        right_layout.addWidget(plot)
        layout.addWidget(right)
        
        return widget
    
    def _add_result_row(self, layout, row, label, value, unit):
        """Add a result row to grid layout."""
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #aaa;")
        layout.addWidget(lbl, row, 0)
        
        val = QLabel(f"<b>{value}</b>")
        val.setStyleSheet("color: #4fc3f7; font-size: 14px;")
        val.setAlignment(Qt.AlignRight)
        layout.addWidget(val, row, 1)
        
        if unit:
            u = QLabel(unit)
            u.setStyleSheet("color: #888;")
            layout.addWidget(u, row, 2)
    
    def _load_graphs_tab(self):
        """Load graphs tab content (lazy)."""
        layout = QGridLayout(self.graphs_widget)
        
        # Downsample all data once
        strain_ds, stress_ds = downsample(self.strain * 100, self.stress, 400)
        ext_ds, force_ds = downsample(self.extension, self.force, 400)
        time_ds, force_t_ds = downsample(self.time, self.force, 400)
        _, stress_t_ds = downsample(self.time, self.stress, 400)
        
        # Stress-Strain
        p1 = pg.PlotWidget()
        p1.setBackground('#1a1a1a')
        p1.setTitle("Stress vs Strain", color='w')
        p1.setLabel('left', 'Stress (MPa)', color='w')
        p1.setLabel('bottom', 'Strain (%)', color='w')
        p1.showGrid(x=True, y=True, alpha=0.3)
        p1.plot(strain_ds, stress_ds, pen=pg.mkPen('#4fc3f7', width=2))
        layout.addWidget(p1, 0, 0)
        
        # Force-Extension
        p2 = pg.PlotWidget()
        p2.setBackground('#1a1a1a')
        p2.setTitle("Force vs Extension", color='w')
        p2.setLabel('left', 'Force (N)', color='w')
        p2.setLabel('bottom', 'Extension (mm)', color='w')
        p2.showGrid(x=True, y=True, alpha=0.3)
        p2.plot(ext_ds, force_ds, pen=pg.mkPen('#81c784', width=2))
        layout.addWidget(p2, 0, 1)
        
        # Force vs Time
        p3 = pg.PlotWidget()
        p3.setBackground('#1a1a1a')
        p3.setTitle("Force vs Time", color='w')
        p3.setLabel('left', 'Force (N)', color='w')
        p3.setLabel('bottom', 'Time (s)', color='w')
        p3.showGrid(x=True, y=True, alpha=0.3)
        p3.plot(time_ds, force_t_ds, pen=pg.mkPen('#ffb74d', width=2))
        layout.addWidget(p3, 1, 0)
        
        # Stress vs Time
        p4 = pg.PlotWidget()
        p4.setBackground('#1a1a1a')
        p4.setTitle("Stress vs Time", color='w')
        p4.setLabel('left', 'Stress (MPa)', color='w')
        p4.setLabel('bottom', 'Time (s)', color='w')
        p4.showGrid(x=True, y=True, alpha=0.3)
        p4.plot(time_ds, stress_t_ds, pen=pg.mkPen('#f48fb1', width=2))
        layout.addWidget(p4, 1, 1)
    
    def _load_data_tab(self):
        """Load data tab content (lazy) - use text display instead of table."""
        layout = QVBoxLayout(self.data_widget)
        
        # Stats
        stats = QLabel(f"<b>Total Data Points:</b> {len(self.force)} | "
                      f"<b>Duration:</b> {self.time[-1]:.1f}s | "
                      f"<b>Sample Rate:</b> ~{len(self.force)/self.time[-1]:.0f} Hz")
        layout.addWidget(stats)
        
        # Data preview as text (MUCH faster than QTableWidget)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 9))
        text.setStyleSheet("background-color: #1a1a1a; color: #ddd;")
        
        # Build text content
        lines = ["Time(s)    Force(N)   Ext(mm)    Stress(MPa)  Strain(%)"]
        lines.append("-" * 60)
        
        n = len(self.force)
        # Show first 100 and last 100
        for i in range(min(100, n)):
            lines.append(f"{self.time[i]:8.3f}  {self.force[i]:9.2f}  {self.extension[i]:9.4f}  "
                        f"{self.stress[i]:10.3f}  {self.strain[i]*100:9.4f}")
        
        if n > 200:
            lines.append(f"\n... {n - 200} rows hidden (full data in export) ...\n")
            
            for i in range(n - 100, n):
                lines.append(f"{self.time[i]:8.3f}  {self.force[i]:9.2f}  {self.extension[i]:9.4f}  "
                            f"{self.stress[i]:10.3f}  {self.strain[i]*100:9.4f}")
        
        text.setPlainText("\n".join(lines))
        layout.addWidget(text)
    
    def _create_export_tab(self) -> QWidget:
        """Create export options tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export buttons
        group = QGroupBox("Export Options")
        group_layout = QGridLayout(group)
        
        btn_excel = QPushButton("📊 Export Excel")
        btn_excel.setMinimumHeight(50)
        btn_excel.clicked.connect(lambda: self._export("excel"))
        group_layout.addWidget(btn_excel, 0, 0)
        group_layout.addWidget(QLabel("Complete report with all sheets"), 0, 1)
        
        btn_csv = QPushButton("📄 Export CSV")
        btn_csv.setMinimumHeight(50)
        btn_csv.clicked.connect(lambda: self._export("csv"))
        group_layout.addWidget(btn_csv, 1, 0)
        group_layout.addWidget(QLabel("Raw data for other software"), 1, 1)
        
        btn_json = QPushButton("🔗 Export JSON")
        btn_json.setMinimumHeight(50)
        btn_json.clicked.connect(lambda: self._export("json"))
        group_layout.addWidget(btn_json, 2, 0)
        group_layout.addWidget(QLabel("Structured data for APIs"), 2, 1)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _export(self, format_type: str):
        """Export results."""
        from datetime import datetime
        import pandas as pd
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample = self.config.metadata.sample_id or "test"
        
        filters = {
            "excel": ("Excel (*.xlsx)", f"{sample}_{timestamp}.xlsx"),
            "csv": ("CSV (*.csv)", f"{sample}_{timestamp}.csv"),
            "json": ("JSON (*.json)", f"{sample}_{timestamp}.json"),
        }
        
        file_filter, default_name = filters[format_type]
        filepath, _ = QFileDialog.getSaveFileName(self, "Export", default_name, file_filter)
        
        if not filepath:
            return
        
        try:
            r = self.results
            c = self.config
            
            if format_type == "csv":
                # Fast CSV export
                df = pd.DataFrame({
                    'Time (s)': self.time,
                    'Force (N)': self.force,
                    'Extension (mm)': self.extension,
                    'Stress (MPa)': self.stress,
                    'Strain (%)': self.strain * 100
                })
                df.to_csv(filepath, index=False)
                
            elif format_type == "excel":
                df_data = pd.DataFrame({
                    'Time (s)': self.time,
                    'Force (N)': self.force,
                    'Extension (mm)': self.extension,
                    'Stress (MPa)': self.stress,
                    'Strain (%)': self.strain * 100
                })
                df_results = pd.DataFrame({
                    'Property': ['UTS (MPa)', 'Yield Strength (MPa)', "Young's Modulus (MPa)",
                                'Elongation (%)', 'Max Force (N)', 'Energy to Break (J)'],
                    'Value': [r.ultimate_tensile_strength, r.yield_strength_offset,
                             r.youngs_modulus, r.elongation_at_break, r.max_force, r.energy_to_break]
                })
                with pd.ExcelWriter(filepath) as writer:
                    df_results.to_excel(writer, sheet_name='Results', index=False)
                    df_data.to_excel(writer, sheet_name='Data', index=False)
                    
            elif format_type == "json":
                import json
                data = {
                    'sample_id': c.metadata.sample_id,
                    'results': {
                        'uts': r.ultimate_tensile_strength,
                        'yield_strength': r.yield_strength_offset,
                        'youngs_modulus': r.youngs_modulus,
                        'elongation': r.elongation_at_break,
                        'max_force': r.max_force,
                        'energy': r.energy_to_break
                    },
                    'data_points': len(self.force)
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            
            QMessageBox.information(self, "Export", f"Exported to {filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")


# Wrapper function to create dialog with pre-processed data
def show_fast_results(config: TestConfiguration, analyzer: ResultsAnalyzer, parent=None):
    """Show fast results dialog with pre-processed numpy arrays."""
    # Pre-convert to numpy arrays ONCE
    stress = np.array(analyzer.stress_data)
    strain = np.array(analyzer.strain_data)
    force = np.array(analyzer.force_data)
    extension = np.array(analyzer.extension_data)
    time = np.array(analyzer.time_data)
    
    # Get results
    results = analyzer.calculate_results()
    
    dialog = FastResultsDialog(config, results, stress, strain, force, extension, time, parent)
    return dialog.exec_()
