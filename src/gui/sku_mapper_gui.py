"""
SKU Mapper GUI Application
Provides a graphical interface for the SKU Mapper functionality.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar,
    QComboBox, QTableWidget, QTableWidgetItem, QTabWidget,
    QGroupBox, QFormLayout, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pandas as pd

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent.parent
sys.path.append(str(src_dir))

from src.data_management.sku_mapper import SkuMapper

class MappingWorker(QThread):
    """Worker thread for processing SKU mapping."""
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, mapper, data_file, sku_column, marketplace_column=None):
        super().__init__()
        self.mapper = mapper
        self.data_file = data_file
        self.sku_column = sku_column
        self.marketplace_column = marketplace_column
    
    def run(self):
        try:
            # Process data
            processed_data = self.mapper.process_inventory_data(
                self.data_file,
                self.sku_column,
                self.marketplace_column
            )
            self.finished.emit(processed_data)
        except Exception as e:
            self.error.emit(str(e))

class InventoryImpactWorker(QThread):
    """Worker thread for calculating inventory impact."""
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)
    
    def __init__(self, mapper, data, quantity_column, warehouse_column=None):
        super().__init__()
        self.mapper = mapper
        self.data = data
        self.quantity_column = quantity_column
        self.warehouse_column = warehouse_column
    
    def run(self):
        try:
            impact_data = self.mapper.calculate_inventory_impact(
                self.data,
                self.quantity_column,
                self.warehouse_column
            )
            self.finished.emit(impact_data)
        except Exception as e:
            self.error.emit(str(e))

class SkuMapperGUI(QMainWindow):
    """Main GUI window for the SKU Mapper application."""
    
    def __init__(self):
        super().__init__()
        self.mapper = None
        self.processed_data = None
        self.impact_data = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('SKU Mapper')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create SKU Mapping tab
        mapping_tab = QWidget()
        mapping_layout = QVBoxLayout(mapping_tab)
        
        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QFormLayout()
        
        self.mapping_file_btn = QPushButton("Select Mapping File")
        self.mapping_file_btn.clicked.connect(self.select_mapping_file)
        file_layout.addRow("Mapping File:", self.mapping_file_btn)
        
        self.data_file_btn = QPushButton("Select Data File")
        self.data_file_btn.clicked.connect(self.select_data_file)
        file_layout.addRow("Data File:", self.data_file_btn)
        
        file_group.setLayout(file_layout)
        mapping_layout.addWidget(file_group)
        
        # Column selection group
        column_group = QGroupBox("Column Selection")
        column_layout = QFormLayout()
        
        self.sku_column_combo = QComboBox()
        self.marketplace_column_combo = QComboBox()
        self.quantity_column_combo = QComboBox()
        self.warehouse_column_combo = QComboBox()
        
        column_layout.addRow("SKU Column:", self.sku_column_combo)
        column_layout.addRow("Marketplace Column:", self.marketplace_column_combo)
        column_layout.addRow("Quantity Column:", self.quantity_column_combo)
        column_layout.addRow("Warehouse Column:", self.warehouse_column_combo)
        
        column_group.setLayout(column_layout)
        mapping_layout.addWidget(column_group)
        
        # Process button
        self.process_btn = QPushButton("Process Data")
        self.process_btn.clicked.connect(self.process_data)
        mapping_layout.addWidget(self.process_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        mapping_layout.addWidget(self.progress_bar)
        
        # Results table
        self.results_table = QTableWidget()
        mapping_layout.addWidget(self.results_table)
        
        # Add mapping tab
        tabs.addTab(mapping_tab, "SKU Mapping")
        
        # Create Inventory Impact tab
        impact_tab = QWidget()
        impact_layout = QVBoxLayout(impact_tab)
        
        # Impact settings group
        impact_group = QGroupBox("Impact Settings")
        impact_settings_layout = QFormLayout()
        
        self.low_stock_threshold = QSpinBox()
        self.low_stock_threshold.setRange(0, 1000)
        self.low_stock_threshold.setValue(10)
        impact_settings_layout.addRow("Low Stock Threshold:", self.low_stock_threshold)
        
        self.capacity_threshold = QSpinBox()
        self.capacity_threshold.setRange(0, 10000)
        self.capacity_threshold.setValue(500)
        impact_settings_layout.addRow("Capacity Threshold:", self.capacity_threshold)
        
        impact_group.setLayout(impact_settings_layout)
        impact_layout.addWidget(impact_group)
        
        # Calculate impact button
        self.calculate_impact_btn = QPushButton("Calculate Impact")
        self.calculate_impact_btn.clicked.connect(self.calculate_impact)
        impact_layout.addWidget(self.calculate_impact_btn)
        
        # Impact results table
        self.impact_table = QTableWidget()
        impact_layout.addWidget(self.impact_table)
        
        # Add impact tab
        tabs.addTab(impact_tab, "Inventory Impact")
        
        # Export button
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self.export_results)
        layout.addWidget(self.export_btn)
    
    def select_mapping_file(self):
        """Handle mapping file selection."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mapping File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        if file_name:
            self.mapping_file_btn.setText(os.path.basename(file_name))
            self.mapper = SkuMapper(file_name)
    
    def select_data_file(self):
        """Handle data file selection."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        if file_name:
            self.data_file_btn.setText(os.path.basename(file_name))
            self.load_column_names(file_name)
    
    def load_column_names(self, file_name):
        """Load column names from the data file."""
        try:
            if file_name.endswith('.csv'):
                df = pd.read_csv(file_name)
            else:
                df = pd.read_excel(file_name)
            
            columns = df.columns.tolist()
            
            # Update combo boxes
            for combo in [self.sku_column_combo, self.marketplace_column_combo,
                         self.quantity_column_combo, self.warehouse_column_combo]:
                combo.clear()
                combo.addItems([''] + columns)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def process_data(self):
        """Process the data using the SKU mapper."""
        if not self.mapper:
            QMessageBox.warning(self, "Warning", "Please select a mapping file first")
            return
        
        if not self.data_file_btn.text() or self.data_file_btn.text() == "Select Data File":
            QMessageBox.warning(self, "Warning", "Please select a data file first")
            return
        
        if not self.sku_column_combo.currentText():
            QMessageBox.warning(self, "Warning", "Please select a SKU column")
            return
        
        # Create and start worker thread
        self.worker = MappingWorker(
            self.mapper,
            self.data_file_btn.text(),
            self.sku_column_combo.currentText(),
            self.marketplace_column_combo.currentText() or None
        )
        self.worker.finished.connect(self.handle_processed_data)
        self.worker.error.connect(self.handle_error)
        self.worker.start()
        
        self.process_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
    
    def handle_processed_data(self, data):
        """Handle processed data from worker thread."""
        self.processed_data = data
        self.display_results(data)
        self.process_btn.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        # Enable impact calculation
        self.calculate_impact_btn.setEnabled(True)
    
    def handle_error(self, error_msg):
        """Handle error from worker thread."""
        QMessageBox.critical(self, "Error", error_msg)
        self.process_btn.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
    
    def display_results(self, data):
        """Display results in the table."""
        self.results_table.setRowCount(len(data))
        self.results_table.setColumnCount(len(data.columns))
        self.results_table.setHorizontalHeaderLabels(data.columns)
        
        for i, row in enumerate(data.itertuples()):
            for j, value in enumerate(row[1:]):
                item = QTableWidgetItem(str(value))
                self.results_table.setItem(i, j, item)
        
        self.results_table.resizeColumnsToContents()
    
    def calculate_impact(self):
        """Calculate inventory impact."""
        if self.processed_data is None:
            QMessageBox.warning(self, "Warning", "Please process data first")
            return
        
        if not self.quantity_column_combo.currentText():
            QMessageBox.warning(self, "Warning", "Please select a quantity column")
            return
        
        # Create and start worker thread
        self.impact_worker = InventoryImpactWorker(
            self.mapper,
            self.processed_data,
            self.quantity_column_combo.currentText(),
            self.warehouse_column_combo.currentText() or None
        )
        self.impact_worker.finished.connect(self.handle_impact_data)
        self.impact_worker.error.connect(self.handle_error)
        self.impact_worker.start()
        
        self.calculate_impact_btn.setEnabled(False)
    
    def handle_impact_data(self, data):
        """Handle impact data from worker thread."""
        self.impact_data = data
        self.display_impact_results(data)
        self.calculate_impact_btn.setEnabled(True)
    
    def display_impact_results(self, data):
        """Display impact results in the table."""
        self.impact_table.setRowCount(len(data))
        self.impact_table.setColumnCount(len(data.columns))
        self.impact_table.setHorizontalHeaderLabels(data.columns)
        
        for i, row in enumerate(data.itertuples()):
            for j, value in enumerate(row[1:]):
                item = QTableWidgetItem(str(value))
                self.impact_table.setItem(i, j, item)
        
        self.impact_table.resizeColumnsToContents()
    
    def export_results(self):
        """Export results to file."""
        if self.processed_data is None:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        
        if file_name:
            try:
                if file_name.endswith('.csv'):
                    self.processed_data.to_csv(file_name, index=False)
                else:
                    self.processed_data.to_excel(file_name, index=False)
                QMessageBox.information(self, "Success", "Data exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exporting data: {str(e)}")

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = SkuMapperGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 