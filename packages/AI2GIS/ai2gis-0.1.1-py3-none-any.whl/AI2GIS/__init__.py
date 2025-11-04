# (Inside file AI2GIS/__init__.py)

"""
Public API for the AI2GIS Library (OOP version).
"""

# Import core data types
from .types import (
    BBox,
    AttributeDict,
    Keypoint,
    Connection,
    CarbonDataDict,
    CarbonPolygonInput
)

# Import I/O utility functions (for saving files)
from .io import (
    save_geojson,
    save_topojson,
    save_shapefile,
    save_gpkg,
    save_csv
)

# Import main classes
from .converter import GeoAIConverter
# Assume the new class is located in 'process_src.py'
from .process_src import ConverterAI2GIS 

# __all__ defines the public API when using "from AI2GIS import *"
__all__ = [
    # Data Types
    "BBox", "AttributeDict", "Keypoint", "Connection",
    "CarbonDataDict", "CarbonPolygonInput",

    # I/O Functions
    "save_geojson", "save_topojson", "save_shapefile",
    "save_gpkg", "save_csv",

    # Core Classes
    "GeoAIConverter",
    "ConverterAI2GIS"
]
