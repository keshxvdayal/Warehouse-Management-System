#!/usr/bin/env python3
"""
SKU Mapper Application
A GUI tool for mapping SKUs to MSKUs with data validation and processing.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent.parent
sys.path.append(str(src_dir))

from src.data_management.gui import main

if __name__ == "__main__":
    main() 