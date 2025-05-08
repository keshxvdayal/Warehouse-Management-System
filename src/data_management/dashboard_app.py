#!/usr/bin/env python3
"""
Inventory Management Dashboard
A Streamlit-based dashboard for managing and visualizing inventory data.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent.parent
sys.path.append(str(src_dir))

from src.data_management.dashboard import main

if __name__ == "__main__":
    main() 