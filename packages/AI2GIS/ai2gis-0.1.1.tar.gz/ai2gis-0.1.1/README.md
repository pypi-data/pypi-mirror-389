![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)

A lightweight Python library for converting results from AI (Computer Vision) models into georeferenced GIS (vector) formats.

## 🎯 The Problem & Solution

AI models (like segmentation or object detection) typically return results in **pixel-space** (pixel coordinates, binary masks). However, GIS tools (QGIS, ArcGIS) and spatial analysis libraries work in **geo-space** (geographic coordinates like latitude/longitude or UTM).

This library provides a simple workflow to "georeference" these AI results and convert them into vector formats like **GeoJSON** or **GeoPackage**, making them immediately ready for use.

## ✨ Key Features

The library revolves around the main `ConverterAI2GIS` class, which has two initialization modes:
1.  **`ConverterAI2GIS(geotiff_path=...)`**: Uses a GeoTIFF file as a geographic reference.
2.  **`ConverterAI2GIS.from_array(...)`**: Works directly with a `numpy.ndarray` and existing `crs` and `transform` information.

### Conversion Methods

- **`create_polygons()`**: Converts a binary mask (raster) into vector polygons (for segmentation tasks).
- **`create_centerline()`**: Extracts a centerline from linear masks (rivers, roads).
- **`create_polygons_from_bins()`**: Converts continuous rasters (NDVI, heatmaps) into class-based polygons.
- **`create_polygons_from_bboxes()`**: Converts AI bounding boxes (pixel coords) into georeferenced polygons.
- **`create_points_from_coords()`**: Converts AI keypoints into georeferenced points.
- **`create_network_from_skeleton()`**: Builds node-edge networks from AI skeletons (pose estimation, roads).

## 💡 Workflow Overview

1. **Initialize:** Provide a reference GeoTIFF or CRS/Transform info.
2. **Convert:** Run a conversion method (polygons, points, centerline, etc.).
3. **Save:** Export the GeoDataFrame to `.gpkg`, `.geojson`, or `.shp`.

## 🚀 Installation

```bash
git clone https://gitlab.ctgroupvietnam.com/ctuav-data-ai/gis-conversion.git
cd gis-conversion
pip install -e .
```

Dependencies (like `geopandas`, `rasterio`, `fiona`, etc.) will be installed automatically.

## 📖 Usage Examples

### Step 1: Initialization

```python
from AI2GIS import ConverterAI2GIS

# Initialize the converter with a reference GeoTIFF
# Note: the image must include valid CRS and transform metadata
workflow = ConverterAI2GIS(geotiff_path="path/to/reference_image.tif")
# Inspect the loaded Coordinate Reference System (CRS)
print("Loaded CRS:", workflow.crs)
```

### Step 2: Conversion Methods

#### 1️⃣ Create Polygons - Segmentation

```python
# Create polygons from a binary mask
# - connectivity: 4 or 8, defines pixel connectivity
# - min_area_pixels: remove small regions (in pixels)
# - simplify_tolerance: simplify geometry (pixel units)
gdf_polygons = workflow.create_polygons(connectivity=4, min_area_pixels=50, simplify_tolerance=0.5)
print(f"Created {len(gdf_polygons)} polygons")
```
<p align="center"> <img src="images_readme/segment_intance.png" width="600" alt="Convert segmentation mask to polygons"/> </p> 


#### 2️⃣ Create Centerlines

```python
# Extract centerlines from linear masks (roads/rivers)
# - dissolve: merge adjacent segments into continuous lines
# - min_path_length_m: discard segments shorter than this (meters)
# - simplify_tolerance_m: simplify lines (meters)
gdf_lines = workflow.create_centerline(dissolve=True, min_path_length_m=100.0, simplify_tolerance_m=2.0)
print(f"Created {len(gdf_lines)} dissolved centerlines")
```
<p align="center"> <img src="images_readme/segment_road.png" width="600" alt="Convert segmentation mask to polygons"/> </p> 

#### 3️⃣ Create Polygons from Bins
```python
bins = [-1.0, 0.2, 0.6, 1.0]
labels = ["Low", "Medium", "High"]
# Classify a continuous raster (e.g., NDVI) into bins and create polygons
# - bins: class thresholds (n+1 values for n classes)
# - labels: text label for each class (length = n)
# - sieve_threshold: remove small noisy regions (pixels)
# - simplify_tolerance: simplify polygons (in raster units)
gdf_zones = workflow.create_polygons_from_bins(bins=bins, labels=labels, sieve_threshold=100, simplify_tolerance=1e-5)
print(f"Created {len(gdf_zones)} NDVI zones")
```
<p align="center"> <img src="images_readme/heatmap.png" width="600" alt="Convert segmentation mask to polygons"/> </p> 


#### 4️⃣ Convert Bounding Boxes

```python
bboxes = [[100, 150, 200, 250], [500, 300, 550, 350]]
attrs = [{"label": "tree", "score": 0.95}, {"label": "car", "score": 0.88}]
# Convert bounding boxes (pixels) into georeferenced polygons
# - bbox format: [x_min, y_min, x_max, y_max] in pixel coordinates
# - attributes: optional per-object attributes
gdf_bboxes = workflow.create_polygons_from_bboxes(bboxes=bboxes, attributes=attrs)
print(f"Created {len(gdf_bboxes)} polygons from bboxes")
```

#### 5️⃣ Convert Keypoints

```python
points = [[150, 200], [525, 325]]
attrs = [{"type": "tree_top", "height_m": 15}, {"type": "tree_top", "height_m": 12}]
# Convert image pixel coordinates to georeferenced points
# - points: list of [x, y] in pixels
# - attributes: optional per-point attributes
gdf_points = workflow.create_points_from_coords(points=points, attributes=attrs)
print(f"Created {len(gdf_points)} points")
```

#### 6️⃣ Create Network Skeleton

```python
keypoints = [[100, 100], [200, 150], [150, 300]]
connections = [(0, 1), (1, 2)]
attrs = [{"type": "main_road", "lanes": 2}, {"type": "local_road", "lanes": 1}]
# Build a node-edge network from an AI-provided skeleton
# - keypoints: list of node pixel coordinates
# - connections: list of tuples (i, j) defining edges between nodes
# - attributes: optional attributes for edges/nodes
gdf_nodes, gdf_edges = workflow.create_network_from_skeleton(keypoints=keypoints, connections=connections, attributes=attrs)
print(f"Created {len(gdf_nodes)} nodes and {len(gdf_edges)} edges")
```

### Step 3: Saving Results

```python
from AI2GIS import save_gpkg, save_geojson, save_shapefile

# Save results to common GIS formats
# - GeoPackage (.gpkg): supports multiple layers, modern standard
save_gpkg(gdf_polygons, "output/buildings.gpkg", layer_name="footprints")
# - GeoJSON (.geojson): lightweight, easy to share, default WGS84
save_geojson(gdf_polygons, "output/buildings.geojson", coordinate_precision=6)
# - Shapefile (.shp): legacy format, limited field names/lengths
save_shapefile(gdf_polygons, "output/buildings.shp")
```
