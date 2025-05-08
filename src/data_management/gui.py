import sys
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QProgressBar, QTabWidget, QGroupBox,
    QFormLayout, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from .sku_mapper import SkuMapper, InventoryType, Warehouse

class MappingWorker(QThread):
    """Worker thread for processing data to avoid GUI freezing."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)
    
    def __init__(self, mapper: SkuMapper, df: pd.DataFrame, sku_column: str, 
                 marketplace_column: str = None):
        super().__init__()
        self.mapper = mapper
        self.df = df
        self.sku_column = sku_column
        self.marketplace_column = marketplace_column
    
    def run(self):
        try:
            result = self.mapper.process_inventory_data(
                self.df, 
                self.sku_column,
                self.marketplace_column
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class InventoryImpactWorker(QThread):
    """Worker thread for calculating inventory impact."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)
    
    def __init__(self, mapper: SkuMapper, df: pd.DataFrame, 
                 quantity_column: str, warehouse_column: str = None):
        super().__init__()
        self.mapper = mapper
        self.df = df
        self.quantity_column = quantity_column
        self.warehouse_column = warehouse_column
    
    def run(self):
        try:
            result = self.mapper.calculate_inventory_impact(
                self.df,
                self.quantity_column,
                self.warehouse_column
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class SkuMapperGUI(QMainWindow):
    """Main GUI window for the SKU Mapper application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SKU Mapper & Inventory Manager")
        self.setMinimumSize(1000, 800)
        
        # Initialize variables
        self.mapper = None
        self.data = None
        self.sku_column = None
        self.marketplace_column = None
        self.quantity_column = None
        self.warehouse_column = None
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize and setup the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # SKU Mapping tab
        mapping_tab = QWidget()
        tab_widget.addTab(mapping_tab, "SKU Mapping")
        self._setup_mapping_tab(mapping_tab)
        
        # Inventory Impact tab
        inventory_tab = QWidget()
        tab_widget.addTab(inventory_tab, "Inventory Impact")
        self._setup_inventory_tab(inventory_tab)
    
    def _setup_mapping_tab(self, tab: QWidget):
        """Setup the SKU mapping tab."""
        layout = QVBoxLayout(tab)
        
        # File selection section
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout()
        
        self.mapping_btn = QPushButton("Load Mapping File")
        self.mapping_btn.clicked.connect(self._load_mapping_file)
        file_layout.addWidget(self.mapping_btn)
        
        self.data_btn = QPushButton("Load Data File")
        self.data_btn.clicked.connect(self._load_data_file)
        file_layout.addWidget(self.data_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Column selection section
        column_group = QGroupBox("Column Selection")
        column_layout = QFormLayout()
        
        self.sku_combo = QComboBox()
        self.sku_combo.currentTextChanged.connect(self._on_sku_column_selected)
        column_layout.addRow("SKU Column:", self.sku_combo)
        
        self.marketplace_combo = QComboBox()
        self.marketplace_combo.currentTextChanged.connect(self._on_marketplace_column_selected)
        column_layout.addRow("Marketplace Column:", self.marketplace_combo)
        
        column_group.setLayout(column_layout)
        layout.addWidget(column_group)
        
        # Preview table
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("Process Data")
        self.process_btn.clicked.connect(self._process_data)
        self.process_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self._export_results)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
    
    def _setup_inventory_tab(self, tab: QWidget):
        """Setup the inventory impact tab."""
        layout = QVBoxLayout(tab)
        
        # Column selection section
        column_group = QGroupBox("Column Selection")
        column_layout = QFormLayout()
        
        self.quantity_combo = QComboBox()
        self.quantity_combo.currentTextChanged.connect(self._on_quantity_column_selected)
        column_layout.addRow("Quantity Column:", self.quantity_combo)
        
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.currentTextChanged.connect(self._on_warehouse_column_selected)
        column_layout.addRow("Warehouse Column:", self.warehouse_combo)
        
        column_group.setLayout(column_layout)
        layout.addWidget(column_group)
        
        # Inventory impact table
        self.impact_table = QTableWidget()
        layout.addWidget(self.impact_table)
        
        # Progress bar
        self.impact_progress = QProgressBar()
        self.impact_progress.setVisible(False)
        layout.addWidget(self.impact_progress)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.calculate_btn = QPushButton("Calculate Impact")
        self.calculate_btn.clicked.connect(self._calculate_impact)
        self.calculate_btn.setEnabled(False)
        button_layout.addWidget(self.calculate_btn)
        
        self.export_impact_btn = QPushButton("Export Impact")
        self.export_impact_btn.clicked.connect(self._export_impact)
        self.export_impact_btn.setEnabled(False)
        button_layout.addWidget(self.export_impact_btn)
        
        layout.addLayout(button_layout)
    
    def _load_mapping_file(self):
        """Load the SKU mapping file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mapping File",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.mapper = SkuMapper(file_path)
                QMessageBox.information(self, "Success", "Mapping file loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load mapping file: {str(e)}")
    
    def _load_data_file(self):
        """Load the data file to process."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.data = pd.read_csv(file_path)
                elif file_path.endswith(('.xlsx', '.xls')):
                    self.data = pd.read_excel(file_path)
                elif file_path.endswith('.json'):
                    self.data = pd.read_json(file_path)
                
                # Update column selections
                self._update_column_combos()
                
                # Show preview
                self._update_preview()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data file: {str(e)}")
    
    def _update_column_combos(self):
        """Update all column selection comboboxes."""
        if self.data is not None:
            columns = self.data.columns
            
            # SKU Mapping tab
            self.sku_combo.clear()
            self.sku_combo.addItems(columns)
            
            self.marketplace_combo.clear()
            self.marketplace_combo.addItems([''] + list(columns))
            
            # Inventory Impact tab
            self.quantity_combo.clear()
            self.quantity_combo.addItems(columns)
            
            self.warehouse_combo.clear()
            self.warehouse_combo.addItems([''] + list(columns))
    
    def _on_sku_column_selected(self, column: str):
        """Handle SKU column selection."""
        self.sku_column = column
        self._update_process_button()
    
    def _on_marketplace_column_selected(self, column: str):
        """Handle marketplace column selection."""
        self.marketplace_column = column if column else None
        self._update_process_button()
    
    def _on_quantity_column_selected(self, column: str):
        """Handle quantity column selection."""
        self.quantity_column = column
        self._update_calculate_button()
    
    def _on_warehouse_column_selected(self, column: str):
        """Handle warehouse column selection."""
        self.warehouse_column = column if column else None
        self._update_calculate_button()
    
    def _update_process_button(self):
        """Update process button state."""
        self.process_btn.setEnabled(bool(
            self.mapper and 
            self.data is not None and 
            self.sku_column
        ))
    
    def _update_calculate_button(self):
        """Update calculate button state."""
        self.calculate_btn.setEnabled(bool(
            self.mapper and 
            self.data is not None and 
            self.quantity_column
        ))
    
    def _update_preview(self):
        """Update the preview table with current data."""
        if self.data is not None:
            self.preview_table.setRowCount(min(100, len(self.data)))
            self.preview_table.setColumnCount(len(self.data.columns))
            self.preview_table.setHorizontalHeaderLabels(self.data.columns)
            
            for i in range(min(100, len(self.data))):
                for j, col in enumerate(self.data.columns):
                    item = QTableWidgetItem(str(self.data.iloc[i, j]))
                    self.preview_table.setItem(i, j, item)
    
    def _process_data(self):
        """Process the data using the SKU mapper."""
        if not all([self.mapper, self.data is not None, self.sku_column]):
            return
        
        # Create and start worker thread
        self.worker = MappingWorker(
            self.mapper, 
            self.data, 
            self.sku_column,
            self.marketplace_column
        )
        self.worker.finished.connect(self._on_processing_finished)
        self.worker.error.connect(self._on_processing_error)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.process_btn.setEnabled(False)
        
        self.worker.start()
    
    def _calculate_impact(self):
        """Calculate inventory impact."""
        if not all([self.mapper, self.data is not None, self.quantity_column]):
            return
        
        # Create and start worker thread
        self.impact_worker = InventoryImpactWorker(
            self.mapper,
            self.data,
            self.quantity_column,
            self.warehouse_column
        )
        self.impact_worker.finished.connect(self._on_impact_finished)
        self.impact_worker.error.connect(self._on_impact_error)
        
        # Show progress
        self.impact_progress.setVisible(True)
        self.impact_progress.setRange(0, 0)  # Indeterminate progress
        self.calculate_btn.setEnabled(False)
        
        self.impact_worker.start()
    
    def _on_processing_finished(self, result: pd.DataFrame):
        """Handle completion of data processing."""
        self.data = result
        self._update_preview()
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Success",
            f"Processed {len(result)} rows successfully!"
        )
    
    def _on_processing_error(self, error_msg: str):
        """Handle processing errors."""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Processing failed: {error_msg}")
    
    def _on_impact_finished(self, result: pd.DataFrame):
        """Handle completion of impact calculation."""
        self.impact_data = result
        
        # Update impact table
        self.impact_table.setRowCount(len(result))
        self.impact_table.setColumnCount(len(result.columns))
        self.impact_table.setHorizontalHeaderLabels(result.columns)
        
        for i, (_, row) in enumerate(result.iterrows()):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.impact_table.setItem(i, j, item)
        
        self.impact_progress.setVisible(False)
        self.calculate_btn.setEnabled(True)
        self.export_impact_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Success",
            f"Calculated impact for {len(result)} items!"
        )
    
    def _on_impact_error(self, error_msg: str):
        """Handle impact calculation errors."""
        self.impact_progress.setVisible(False)
        self.calculate_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Impact calculation failed: {error_msg}")
    
    def _export_results(self):
        """Export the processed data to a file."""
        if self.data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.data.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    self.data.to_excel(file_path, index=False)
                elif file_path.endswith('.json'):
                    self.data.to_json(file_path, orient='records')
                
                QMessageBox.information(self, "Success", "Results exported successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")
    
    def _export_impact(self):
        """Export the inventory impact data to a file."""
        if not hasattr(self, 'impact_data'):
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Impact Results",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.impact_data.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    self.impact_data.to_excel(file_path, index=False)
                elif file_path.endswith('.json'):
                    self.impact_data.to_json(file_path, orient='records')
                
                QMessageBox.information(self, "Success", "Impact results exported successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export impact results: {str(e)}")

def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    window = SkuMapperGUI()
    window.show()
    sys.exit(app.exec_()) 