"""
Defines common data type hints used throughout the library.
"""
from typing import Any, Dict, List, Union, Tuple, Set

# --- Type Definitions ---
BBox = List[Union[int, float]]              # [xmin, ymin, xmax, ymax]
AttributeDict = Dict[str, Any]
Keypoint = List[Union[int, float]]
Connection = Tuple[int, int]
CarbonDataDict = Dict[str, Union[int, float]]
CarbonPolygonInput = List[Dict[str, Any]]
PixelCoord = Tuple[int, int]
