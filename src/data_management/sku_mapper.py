"""
SKU Mapper Module
Handles SKU to MSKU mapping and data cleaning operations.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from enum import Enum
import os
import re
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging
log_file = 'logs/sku_mapper.log'
rotating_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InventoryType(Enum):
    """Enum for different types of inventory items."""
    PRODUCT = "product"
    COMBO = "combo"
    PACKAGING = "packaging"
    COMPONENT = "component"

class Warehouse(Enum):
    """Enum for different warehouse locations."""
    MAIN = "main"
    FBA = "fba"
    FBM = "fbm"
    THIRD_PARTY = "third_party"

class SkuMapper:
    """Class for handling SKU to MSKU mapping and data cleaning."""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize the SKU Mapper.
        
        Args:
            mapping_file (str, optional): Path to the mapping file (CSV/Excel)
        """
        self.mappings: Dict[str, Dict] = {}
        self.unknown_skus: List[str] = []
        self.error_log: List[Dict] = []
        
        if mapping_file:
            self.load_mappings(mapping_file)
    
    def load_mappings(self, file_path: str) -> bool:
        """
        Load SKU mappings from a file.
        
        Args:
            file_path (str): Path to the mapping file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            # Validate required columns
            required_cols = ['SKU', 'MSKU', 'Type']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Missing required columns: {required_cols}")
            
            # Process mappings
            for _, row in df.iterrows():
                sku = str(row['SKU']).strip()
                self.mappings[sku] = {
                    'msku': str(row['MSKU']).strip(),
                    'type': row['Type'],
                    'marketplace': row.get('Marketplace', ''),
                    'components': row.get('Components', ''),
                    'packaging': row.get('Packaging', ''),
                    'warehouse': row.get('Warehouse', '')
                }
            
            logger.info(f"Loaded {len(self.mappings)} SKU mappings")
            return True
            
        except Exception as e:
            logger.error(f"Error loading mappings: {str(e)}")
            self.error_log.append({
                'operation': 'load_mappings',
                'error': str(e)
            })
            return False
    
    def validate_sku_format(self, sku: str, pattern: str = r'^[A-Za-z0-9_-]+$') -> bool:
        """Validate SKU format using a regex pattern."""
        return bool(re.match(pattern, str(sku)))
    
    def process_inventory_data(self, 
                             data: Union[pd.DataFrame, str],
                             sku_column: str = 'SKU',
                             marketplace_column: Optional[str] = None) -> pd.DataFrame:
        """
        Process inventory data by mapping SKUs to MSKUs.
        
        Args:
            data (Union[pd.DataFrame, str]): DataFrame or path to data file
            sku_column (str): Name of the SKU column
            marketplace_column (str, optional): Name of the marketplace column
            
        Returns:
            pd.DataFrame: Processed data with MSKU mappings
        """
        try:
            # Load data if string path provided
            if isinstance(data, str):
                if data.endswith('.csv'):
                    data = pd.read_csv(data)
                elif data.endswith(('.xlsx', '.xls')):
                    data = pd.read_excel(data)
                else:
                    raise ValueError("Unsupported file format")
            
            # Create copy of data
            processed_data = data.copy()
            
            # Add MSKU column
            processed_data['MSKU'] = processed_data[sku_column].map(
                lambda x: self.mappings.get(str(x).strip(), {}).get('msku', '')
            )
            
            # Add inventory type
            processed_data['Inventory_Type'] = processed_data[sku_column].map(
                lambda x: self.mappings.get(str(x).strip(), {}).get('type', '')
            )
            
            # Validate SKU format and flag invalid SKUs
            processed_data['SKU_Valid'] = processed_data[sku_column].map(self.validate_sku_format)
            invalid_skus = processed_data.loc[~processed_data['SKU_Valid'], sku_column].unique().tolist()
            if invalid_skus:
                logger.warning(f"Found {len(invalid_skus)} invalid SKU formats: {invalid_skus}")
                self.error_log.append({
                    'operation': 'process_inventory_data',
                    'error': f'Invalid SKU formats: {invalid_skus}'
                })
            
            # Track unknown SKUs
            unknown_mask = processed_data['MSKU'] == ''
            self.unknown_skus.extend(
                processed_data.loc[unknown_mask, sku_column].unique().tolist()
            )
            
            # Log processing results
            logger.info(f"Processed {len(processed_data)} records")
            if self.unknown_skus:
                logger.warning(f"Found {len(self.unknown_skus)} unknown SKUs")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            self.error_log.append({
                'operation': 'process_inventory_data',
                'error': str(e)
            })
            raise
    
    def calculate_inventory_impact(self,
                                 data: pd.DataFrame,
                                 quantity_column: str = 'Quantity',
                                 warehouse_column: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate inventory impact for each SKU/MSKU.
        
        Args:
            data (pd.DataFrame): Processed inventory data
            quantity_column (str): Name of the quantity column
            warehouse_column (str, optional): Name of the warehouse column
            
        Returns:
            pd.DataFrame: Inventory impact calculations
        """
        try:
            # Group by MSKU and calculate totals
            impact_data = data.groupby('MSKU').agg({
                quantity_column: 'sum',
                'Inventory_Type': 'first'
            }).reset_index()
            
            # Add warehouse information if available
            if warehouse_column and warehouse_column in data.columns:
                warehouse_impact = data.groupby(['MSKU', warehouse_column])[quantity_column].sum().reset_index()
                impact_data = impact_data.merge(
                    warehouse_impact,
                    on='MSKU',
                    how='left'
                )
            
            return impact_data
            
        except Exception as e:
            logger.error(f"Error calculating inventory impact: {str(e)}")
            self.error_log.append({
                'operation': 'calculate_inventory_impact',
                'error': str(e)
            })
            raise
    
    def get_unknown_skus(self) -> List[str]:
        """Get list of unknown SKUs."""
        return list(set(self.unknown_skus))
    
    def get_error_log(self) -> List[Dict]:
        """Get error log."""
        return self.error_log
    
    def export_processed_data(self,
                            data: pd.DataFrame,
                            output_path: str,
                            format: str = 'csv') -> bool:
        """
        Export processed data to file.
        
        Args:
            data (pd.DataFrame): Processed data to export
            output_path (str): Path to save the file
            format (str): Output format ('csv' or 'excel')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if format.lower() == 'csv':
                data.to_csv(output_path, index=False)
            elif format.lower() == 'excel':
                data.to_excel(output_path, index=False)
            else:
                raise ValueError("Unsupported export format")
            
            logger.info(f"Exported data to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            self.error_log.append({
                'operation': 'export_processed_data',
                'error': str(e)
            })
            return False 