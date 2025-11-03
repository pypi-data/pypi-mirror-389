# AI2GIS

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

### Conversion Methods:

* **`create_polygons()`**: Converts a binary mask (raster) into vector polygons. (Used for Instance/Semantic Segmentation).
* **`create_centerline()`**: Extracts a centerline from linear masks (e.g., rivers, roads).
* **`create_polygons_from_bins()`**: Classifies a continuous-value raster (like NDVI or a carbon heatmap) according to specified bins and converts each class into polygons.
* **`create_polygons_from_bboxes()`**: Converts a list of Bounding Boxes (in pixel coordinates) into georeferenced polygons.
* **`create_points_from_coords()`**: Converts a list of Keypoints (in pixel coordinates) into georeferenced points.
* **`create_network_from_skeleton()`**: Creates a network (Nodes and Edges) from a list of keypoints and the connections between them.

## 🚀 Installation

1.  Clone this repository to your machine:
    ```bash
    git clone [https://gitlab.ctgroupvietnam.com/ctuav-data-ai/gis-conversion.git](https://gitlab.ctgroupvietnam.com/ctuav-data-ai/gis-conversion.git)
    cd gis-conversion
    ```

2.  Install the library (recommending "editable" mode `-e` for development):
    ```bash
    pip install -e .
    ```

This command will automatically read the `pyproject.toml` file and install all necessary dependencies (like `geopandas`, `rasterio`, `fiona`, etc.).

## 📖 Quick Start

Here are the two most common use cases.

### Scenario 1: Convert a Mask (Numpy array) to Polygons

Let's say you have a GeoTIFF file that is a mask (e.g., `water_mask.tif`) and you want to vectorize the objects within it.

```python
import rasterio
from AI2GIS import ConverterAI2GIS, save_geojson

# 1. Read the data from the GeoTIFF file
with rasterio.open("path/to/your/water_mask.tif") as src:
    data_mask = src.read(1)
    crs = src.crs
    transform = src.transform
    nodata = src.nodata
    meta = src.meta

# 2. Initialize the Converter from an array
# (Ideal when you already have the data in memory)
try:
    workflow = ConverterAI2GIS.from_array(
        data_array=data_mask,
        crs=crs,
        transform=transform,
        nodata=nodata,
        meta=meta
    )

    # 3. Run the conversion
    # min_area_pixels: removes small noise polygons
    # simplify_tolerance: smooths (simplifies) the polygon borders
    gdf = workflow.create_polygons(min_area_pixels=50, simplify_tolerance=0.5)

    # 4. Save the result
    if not gdf.empty:
        save_geojson(gdf, "output/water_polygons.geojson")
        print(f"Saved {len(gdf)} polygons!")
    else:
        print("No objects were found.")

except Exception as e:
    print(f"Conversion failed: {e}")