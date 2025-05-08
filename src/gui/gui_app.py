#!/usr/bin/env python3
"""
SKU Mapper GUI Application
Main entry point for the SKU Mapper GUI application.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent.parent
sys.path.append(str(src_dir))

from src.gui.sku_mapper_gui import main

if __name__ == "__main__":
    main() 