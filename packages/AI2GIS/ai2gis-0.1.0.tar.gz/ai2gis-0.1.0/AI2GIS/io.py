"""
Utility functions for saving GeoDataFrames to various GIS file formats.
"""
import geopandas as gpd
import json
import topojson as tp
import warnings # Keep warnings import for save_shapefile (which logs)
from pathlib import Path
from typing import Union, Optional
import logging 

# --- [ADD] Setup logger for this file ---
logger = logging.getLogger(__name__)
# ------------------------------------------

def save_geojson(
    gdf: gpd.GeoDataFrame,
    output_path: Union[str, Path],
    coordinate_precision: int = 8
):
    """Saves a GeoDataFrame to a GeoJSON file.

    Args:
        gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
        output_path (Union[str, Path]): The output GeoJSON file path.
        coordinate_precision (int, optional): The number of decimal places
                                            for coordinates. Defaults to 8.
    """
    try:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        gdf.to_file(
            out_path, 
            driver='GeoJSON', 
            COORDINATE_PRECISION=coordinate_precision
        )
        # [LOG] Replaced print with logger.info
        logger.info("Successfully saved %s features to '%s'.", len(gdf), out_path)
    except Exception as e:
        # [LOG] Replaced print with logger.error
        logger.error(
            "Error saving GeoJSON file '%s': %s", output_path, e,
            exc_info=True # Also log the traceback
        )
        raise e

def save_topojson(
    gdf: gpd.GeoDataFrame,
    output_path: Union[str, Path],
    object_name: str = "layers",
    prequantize: bool = True
):
    """Saves a GeoDataFrame to a TopoJSON file.

    TopoJSON is a compressed format, efficient for web use.
    It is recommended to reproject the GDF to EPSG:4326 before saving.

    Args:
        gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
        output_path (Union[str, Path]): The output TopoJSON file path.
        object_name (str, optional): The name of the object (layer)
                                    inside the TopoJSON file.
        prequantize (bool, optional): Toggles quantization
                                    (helps reduce file size).
    """
    try:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if gdf.crs and gdf.crs.to_epsg() != 4326:
            # [LOG] Replaced warnings.warn with logger.warning
            logger.warning(
                "GeoDataFrame is in CRS %s. "
                "It is recommended to reproject to EPSG:4326 before saving TopoJSON.",
                gdf.crs.to_string()
            )
        
        topo = tp.Topology(gdf, object_name=object_name, prequantize=prequantize)
        topo_dict = topo.to_dict()
        
        if gdf.crs is not None:
            topo_dict["crs"] = {"type": "name", "properties": {"name": str(gdf.crs)}}
            
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(topo_dict, f, ensure_ascii=False, separators=(",", ":"))
            
        # [LOG] Replaced print with logger.info
        logger.info("Successfully saved TopoJSON to '%s'.", out_path)
    except Exception as e:
        # [LOG] Replaced print with logger.error
        logger.error(
            "Error saving TopoJSON file '%s': %s", output_path, e,
            exc_info=True
        )
        raise e

def save_shapefile(
    gdf: gpd.GeoDataFrame,
    output_path: Union[str, Path]
):
    """Saves a GeoDataFrame to an ESRI Shapefile (.shp).
    
    Warning: Shapefiles have a 10-character limit for column names.
    GeoPandas will automatically truncate column names (and raise a warning).

    Args:
        gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
        output_path (Union[str, Path]): The output .shp file path.
    """
    try:
        out_path = Path(output_path)
        
        if out_path.suffix.lower() != ".shp":
            new_name = out_path.with_suffix(".shp").name
            # [LOG] Replaced warnings.warn with logger.warning
            logger.warning(
                "File extension is not .shp. Automatically changing to: %s", new_name
            )
            out_path = out_path.with_suffix(".shp")
            
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Suppress Fiona/GeoPandas warnings about column names > 10 chars,
        # as we have already warned the user in the docstring.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="geopandas")
            gdf.to_file(out_path, driver="ESRI Shapefile")
            
        # [LOG] Replaced print with logger.info
        logger.info("Successfully saved %s features to '%s'.", len(gdf), out_path)
        
    except Exception as e:
        # [LOG] Replaced print with logger.error
        logger.error(
            "Error saving Shapefile '%s': %s", output_path, e,
            exc_info=True
        )
        raise e

def save_gpkg(
    gdf: gpd.GeoDataFrame,
    output_path: Union[str, Path],
    layer_name: str = "main"
):
    """Saves a GeoDataFrame to a GeoPackage (.gpkg) file.
    
    This is the modern, flexible format recommended to replace Shapefiles.

    Args:
        gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
        output_path (Union[str, Path]): The output .gpkg file path.
        layer_name (str, optional): The name of the layer inside the GeoPackage.
    """
    try:
        out_path = Path(output_path)
        
        if out_path.suffix.lower() != ".gpkg":
            new_name = out_path.with_suffix(".gpkg").name
            # [LOG] Replaced warnings.warn with logger.warning
            logger.warning(
                "File extension is not .gpkg. Automatically changing to: %s", new_name
            )
            out_path = out_path.with_suffix(".gpkg")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        gdf.to_file(out_path, driver="GPKG", layer=layer_name)
        # [LOG] Replaced print with logger.info
        logger.info(
            "Successfully saved %s features (layer='%s') to '%s'.",
            len(gdf), layer_name, out_path
        )
        
    except Exception as e:
        # [LOG] Replaced print with logger.error
        logger.error(
            "Error saving GeoPackage file '%s': %s", output_path, e,
            exc_info=True
        )
        raise e

def save_csv(
    gdf: gpd.GeoDataFrame,
    output_path: Union[str, Path],
    include_wkt: bool = True
):
    """Saves a GeoDataFrame to a CSV file.
    
    Args:
        gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
        output_path (Union[str, Path]): The output CSV file path.
        include_wkt (bool, optional): If True (default), the 'geometry'
            column will be converted to WKT (Well-Known Text).
            If False, the 'geometry' column will be dropped.
    """
    try:
        out_path = Path(output_path)
        
        if out_path.suffix.lower() != ".csv":
            new_name = out_path.with_suffix(".csv").name
            # [LOG] Replaced warnings.warn with logger.warning
            logger.warning(
                "File extension is not .csv. Automatically changing to: %s", new_name
            )
            out_path = out_path.with_suffix(".csv")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        if include_wkt:
            # GDF.to_csv() automatically converts the 'geometry' column to WKT
            gdf.to_csv(out_path, index=False)
            # [LOG] Replaced print with logger.info
            logger.info(
                "Successfully saved %s features (with WKT) to '%s'.",
                len(gdf), out_path
            )
        else:
            # Save CSV without geometry information
            gdf_no_geom = gdf.drop(columns='geometry', errors='ignore')
            gdf_no_geom.to_csv(out_path, index=False)
            # [LOG] Replaced print with logger.info
            logger.info(
                "Successfully saved %s features (without geometry) to '%s'.",
                len(gdf), out_path
            )
            
    except Exception as e:
        # [LOG] Replaced print with logger.error
        logger.error(
            "Error saving CSV file '%s': %s", output_path, e,
            exc_info=True
        )
        raise e