"""
Core ConverterAI2GIS - Refactored from original functions.

OPTIMIZED VERSION (v2):
- Fixes high memory usage by lazy-loading float32/scaled arrays.
- Optimizes create_polygons_from_bins (CPU).
- [REVERTED] create_centerline now uses skimage.skeletonize
  (thay vì cv2.ximgproc.thinning) để đảm bảo độ chính xác của skeleton.
"""
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.crs import CRS as RasterioCRS
from rasterio.transform import Affine
from shapely.geometry import shape, Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import unary_union, linemerge
import cv2
import warnings
import logging
from typing import List, Union, Optional, Tuple
from .types import BBox, AttributeDict, Keypoint, Connection

from skimage.morphology import skeletonize

from .converter import GeoAIConverter

from ._utils import _fill_holes, _gaussian_smooth, _trace_skeleton_paths, _build_lines

# Setup logger
logger = logging.getLogger(__name__)

class ConverterAI2GIS:
    """
        Manages the workflow for converting AI results into GIS formats.

        This class acts as the primary interface for transforming results
        from AI models (typically in pixel coordinates) into georeferenced
        GIS vector formats (GeoDataFrames).

        How it works:
        1. It loads raster data (GeoTIFF or NumPy array) ONCE to establish
        the georeferencing context (CRS - Coordinate Reference System
        and Affine Transform).
        2. It reuses this context for various conversion methods based on the
        same source image (e.g., creating both polygons and centerlines
        from the same mask file with only one file read).

        This class optimizes memory usage by avoiding repeated file reads
        and provides a clear, high-level API for common AI-to-GIS tasks.

        Attributes:
            converter (GeoAIConverter): The low-level converter object that
                handles coordinate transformations.
            crs (RasterioCRS): The Coordinate Reference System loaded from the
                file/array.
            transform (Affine): The Affine Transform parameters loaded from the
                file/array.
            data_raw (np.ndarray): The raw pixel data (band 1) loaded from the
                file/array, retaining its original data type (e.g., uint8).
            nodata (Optional[Union[int, float]]): The NoData value of the raster.
            meta (dict): The metadata of the original raster.

        Usage:

        Method 1: Initialize from a GeoTIFF file (Common use):
            >>> workflow = ConverterAI2GIS("path/to/reference_image.tif")

        Method 2: Initialize from an in-memory NumPy array (for complex pipelines):
            >>> data = np.array(...)
            >>> crs = rasterio.crs.CRS.from_epsg(32648)
            >>> transform = rasterio.transform.from_origin(...)
            >>> workflow = ConverterAI2GIS.from_array(data, crs, transform)
    """

    def __init__(self, geotiff_path: str):
        """
                Initializes the ConverterAI2GIS from a GeoTIFF file path.

                This method reads the metadata (CRS, Transform) and the pixel data
                (band 1) from the provided GeoTIFF. This data is then stored
                within the instance to be reused for various processing tasks.

                Args:
                    geotiff_path (str): The path to the reference GeoTIFF file.
                        This file can be the original image (e.g., RGB, NDVI) or
                        a mask file (e.g., segmentation results).

                Raises:
                    FileNotFoundError: If the file at `geotiff_path` does not exist.
                    rasterio.errors.RasterioIOError: If the file is not a valid
                        raster format that Rasterio can read.
                    Exception: For other errors during metadata or pixel data reading.
            """
        logger.info("Initializing ConverterAI2GIS with file: %s", geotiff_path)
        self.geotiff_path = geotiff_path

        try:
            # Initialize converter FROM FILE PATH (to get CRS/Transform)
            self.converter = GeoAIConverter(geotiff_path=self.geotiff_path)
            self.crs = self.converter.crs
            self.transform = self.converter.transform
            logger.debug("Successfully loaded CRS and Transform from file.")
        except Exception as e:
            logger.error("Failed to initialize GeoAIConverter from file: %s", e, exc_info=True)
            raise

        try:
            # Load raster data ONCE FROM FILE PATH
            with rasterio.open(geotiff_path) as src:
                self._load_raster_data(src) # Call internal helper to load data
            logger.debug("Successfully loaded raster data (band 1) from file.")
        except Exception as e:
            logger.error("Failed to read raster data from file: %s", e, exc_info=True)
            raise

    @classmethod
    def from_array(
        cls,
        data_array: np.ndarray,
        crs: RasterioCRS,
        transform: Affine,
        nodata: Optional[Union[int, float]] = None,
        meta: Optional[dict] = None,
        scale: float = 1.0,
        offset: float = 0.0
    ):
        """
        Creates a ConverterAI2GIS instance from an in-memory NumPy array.

        This class method acts as an alternative constructor. It is designed
        for workflows where the raster data already exists in memory
        (e.g., as the result of a previous computation) and does not
        need to be read from a file.

        Args:
            data_array (np.ndarray): The NumPy array containing the raster
                data (band 1).
            crs (rasterio.crs.CRS): The Coordinate Reference System of the data.
            transform (rasterio.Affine): The Affine transform of the data.
            nodata (Optional[Union[int, float]]): The NoData value, if any.
                Defaults to None.
            meta (Optional[dict]): Optional raster metadata dictionary.
                If not provided, a basic one will be generated automatically.
                Defaults to None.
            scale (float): The scale factor to apply to `data_array`
                (used for the `data_scaled` property). Defaults to 1.0.
            offset (float): The offset value to apply to `data_array`
                (used for the `data_scaled` property). Defaults to 0.0.

        Returns:
            ConverterAI2GIS: A new, initialized instance of the
                ConverterAI2GIS class.
        
        Raises:
            Exception: If the `GeoAIConverter` fails to initialize
                (e.g., invalid CRS or transform).
        """
        logger.info("Initializing ConverterAI2GIS from in-memory array...")
        
        # 1. Create an "empty" instance without calling __init__
        instance = cls.__new__(cls)
        instance.geotiff_path = None # Mark as not created from a file

        # 2. Directly assign CRS and Transform
        instance.crs = crs
        instance.transform = transform

        # 3. Initialize GeoAIConverter DIRECTLY with CRS/Transform
        try:
            instance.converter = GeoAIConverter(crs=crs, transform=transform)
            logger.debug("GeoAIConverter initialized (from array) successfully.")
        except Exception as e:
            logger.error("Failed to initialize GeoAIConverter (from array): %s", e, exc_info=True)
            raise

        # 4. Assign raster data and metadata
        instance.nodata = nodata
        if meta:
            instance.meta = meta.copy()
        else:
            # Create basic meta if not provided
            instance.meta = {
                'driver': 'MEM', 'dtype': str(data_array.dtype),
                'nodata': nodata, 'width': data_array.shape[1],
                'height': data_array.shape[0], 'count': 1,
                'crs': crs, 'transform': transform,
            }
        # Call internal helper to process data_array
        instance._process_loaded_data(data_array, scale, offset)
        logger.debug("Assigned and processed raster data (from array) successfully.")

        return instance

    # --- INTERNAL METHODS FOR DATA LOADING/PROCESSING ---
    def _load_raster_data(self, src: rasterio.DatasetReader):
        """(Internal) Reads and processes raster data from an opened dataset."""
        self.meta = src.meta.copy()
        self.nodata = src.nodata
        data = src.read(1)

        scale = src.scales[0] if src.scales and len(src.scales) > 0 else 1.0
        offset = src.offsets[0] if src.offsets and len(src.offsets) > 0 else 0.0

        self._process_loaded_data(data, scale, offset)

# --- RAM OPTIMIZATION: Lazy loading ---
    def _process_loaded_data(self, data_array: np.ndarray, scale: float, offset: float):
        """(Internal) Processes the loaded NumPy array."""
        # DO NOT cast to float32! Keep the original dtype (e.g., uint8)
        self.data_raw = data_array 
        self.scale = scale
        self.offset = offset

        # These properties will be "lazy loaded" when needed
        self._data_raw_nan = None
        self._data_scaled = None

    @property
    def data_raw_nan(self) -> np.ndarray:
        """Lazy-loads a float32 version of raw data with NaNs."""
        if self._data_raw_nan is None:
            logger.debug("Lazy-loading data_raw_nan (float32 with NaN)...")
            
            # Only cast to float32 WHEN NEEDED
            data_float = self.data_raw.astype(np.float32) 
            
            # Handle nodata
            if self.nodata is not None and not np.isnan(self.nodata):
                data_float[np.isclose(data_float, self.nodata)] = np.nan
            
            # Handle Inf/NaN (if any) from the source
            data_float[~np.isfinite(data_float)] = np.nan
            self._data_raw_nan = data_float
            
        return self._data_raw_nan

    @property
    def data_scaled(self) -> np.ndarray:
        """Lazy-loads the scaled float32 data."""
        if self._data_scaled is None:
            logger.debug("Lazy-loading data_scaled (applying scale/offset)...")
            
            # The data_raw_nan property will automatically handle the creation
            # of the first float32 copy (if needed)
            self._data_scaled = (self.data_raw_nan * self.scale) + self.offset
            
        return self._data_scaled
    def create_polygons(
        self,
        connectivity: int = 4,
        min_area_pixels: int = 0,
        simplify_tolerance: float = 0.0,
    ) -> gpd.GeoDataFrame:
        """
        Vectorizes the loaded raster mask (`self.data_raw`) into Polygons.

        This method is ideal for converting results from semantic or
        instance segmentation, where `self.data_raw` is a mask array
        (e.g., a uint8 array with values 0, 1, 2...).

        It groups pixels of the same value, converts them into polygons,
        and applies optional filtering (sieving, simplification).

        Args:
            connectivity (int): Pixel connectivity (4 or 8) used to
                determine how pixels are grouped into a feature.
                Defaults to 4.
            min_area_pixels (int): A "sieve" threshold. Polygons smaller
                than this area (in *pixels*) will be removed. This is
                useful for eliminating small noise. Defaults to 0 (no filtering).
            simplify_tolerance (float): The tolerance (in CRS units,
                e.g., meters or degrees) for simplifying the polygon
                geometries. A larger value results in simpler shapes.
                Defaults to 0.0 (no simplification).

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the vectorized
                polygons, georeferenced with the source raster's CRS.
        """
        logger.info("--- Starting process: create_polygons ---")
        # Use the loaded self.converter and self.data_raw
        gdf = self.converter.from_mask(
            mask_data=self.data_raw,
            connectivity=connectivity,
            min_area_pixels=min_area_pixels,
            simplify_tolerance=simplify_tolerance
        )
        if gdf.empty:
            logger.info("Result: Empty GeoDataFrame.")
        else:
            logger.info("Vectorization complete. Found %s features.", len(gdf))
        return gdf

    def create_centerline(
        self,
        keep_value: int = 1,
        dissolve: bool = True,
        min_path_length_m: float = 0.0,
        simplify_tolerance_m: float = 0.0,
    ) -> gpd.GeoDataFrame:
        """
        Creates a LineString GeoDataFrame from the centerline
        of the raster mask (`self.data_raw`).

        This workflow is designed to extract network-like features
        (e.g., rivers, roads) from a mask file (a binary 0 and 1 image).

        Processing steps:
        1. Skeletonize the mask image to get a 1-pixel-wide representation.
        2. Trace the pixel skeleton to identify paths and junctions.
        3. Convert the pixel paths into georeferenced LineStrings.
        4. (Optional) Dissolve contiguous lines into longer features.
        5. (Optional) Prune (filter) lines that are too short (in meters).
        6. (Optional) Simplify the geometry (in meters).
        7. Return the result as a GeoDataFrame reprojected to EPSG:4326.

        Args:
            keep_value (int): The value (e.g., an ID) to assign to the 'value'
                column of the resulting LineStrings. Defaults to 1.
            dissolve (bool): If True, contiguous line segments will be
                dissolved/merged into continuous LineStrings where possible.
                Defaults to True.
            min_path_length_m (float): The minimum length threshold (in meters).
                Lines shorter than this value will be removed. Defaults to 0.0.
            simplify_tolerance_m (float): The simplification tolerance
                (in meters). Larger values result in simpler line geometries.
                Defaults to 0.0.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the extracted
                LineStrings, always reprojected to EPSG:4326.
        """
        logger.info("--- Starting process: create_centerline ---")
        skel = self.data_raw.copy().astype(np.uint8) 
        transform = self.transform
        crs = self.crs
        nodata = self.nodata

        logger.debug("Original unique pixel values: %s", np.unique(skel))

        if nodata is not None:
            skel = np.where(np.isclose(skel.astype(float), nodata), 0, skel).astype(np.uint8)

        skel_bool = (skel > 0)
        if not np.any(skel_bool):
            logger.info("Input mask is empty. Returning empty GeoDataFrame.")
            return gpd.GeoDataFrame(geometry=[], crs=crs or "EPSG:4326")

        logger.info("--- 2.5. Skeletonizing mask (Using skimage for accuracy) ---")
        skel_skeletonized = skeletonize(skel_bool)
        skel = skel_skeletonized.astype(np.uint8)
        logger.debug("Pixels after skeletonize: %s", np.sum(skel > 0))

        if not np.any(skel):
            logger.info("Mask is empty after skeletonize. Returning empty GeoDataFrame.")
            return gpd.GeoDataFrame(geometry=[], crs=crs or "EPSG:4326")

        logger.info("--- 3. Trace paths ---")
        paths = _trace_skeleton_paths(skel)
        if not paths:
            logger.info("No paths found after tracing.")
            return gpd.GeoDataFrame(geometry=[], crs=crs or "EPSG:4326")

        logger.info("--- 4. Build Lines ---")
        lines = _build_lines(paths, transform)
        if not lines:
            logger.info("No valid lines found.")
            return gpd.GeoDataFrame(geometry=[], crs=crs or "EPSG:4326")

        gdf = gpd.GeoDataFrame({"value": [keep_value]*len(lines)}, geometry=lines, crs=crs)

        logger.info("--- 5. Dissolve ---")
        if dissolve and not gdf.empty:
             try:
                 merged_geom = gdf.geometry.unary_union
                 merged_lines = linemerge(merged_geom)

                 if merged_lines.is_empty:
                     logger.info("Empty result after linemerge.")
                     gdf = gpd.GeoDataFrame(geometry=[], crs=crs)
                 elif isinstance(merged_lines, (LineString, MultiLineString)):
                     gdf = gpd.GeoDataFrame({"value": [keep_value]}, geometry=[merged_lines], crs=crs)
                     if gdf.geometry.iloc[0].geom_type == 'MultiLineString':
                          gdf = gdf.explode(index_parts=False).reset_index(drop=True)
                 elif merged_lines.geom_type == 'GeometryCollection':
                      line_components = [geom for geom in merged_lines.geoms if isinstance(geom, LineString)]
                      if line_components:
                           gdf = gpd.GeoDataFrame({"value": [keep_value]*len(line_components)}, geometry=line_components, crs=crs)
                      else:
                           logger.info("GeometryCollection contains no LineStrings.")
                           gdf = gpd.GeoDataFrame(geometry=[], crs=crs)
                 else:
                      logger.warning("Unexpected geometry type after linemerge: %s", merged_lines.geom_type)

             except Exception as merge_err:
                 logger.error("Error during dissolve/linemerge: %s", merge_err, exc_info=True)

        if gdf.empty:
             logger.info("GDF is empty after dissolve/explode step.")
             return gpd.GeoDataFrame(geometry=[], crs=crs or "EPSG:4326")

        logger.info("--- 6. Reprojecting to 3857 for metrics ---")
        try:
            gdf_m = gdf.to_crs(3857)
        except Exception as e:
            logger.warning("Could not reproject to 3857 (%s). Using original CRS '%s'.", e, gdf.crs)
            gdf_m = gdf.copy()

        logger.info("--- 7. Pruning (Filter by length) ---")
        if min_path_length_m > 0 and not gdf_m.empty:
            original_count = len(gdf_m)
            keep = gdf_m.geometry.length >= float(min_path_length_m)
            gdf = gdf[keep].reset_index(drop=True)
            gdf_m = gdf_m[keep].reset_index(drop=True)

            logger.debug("-> Pruning filter: %s / %s lines kept.", len(gdf_m), original_count)

            if gdf.empty:
                logger.info("No lines passed the pruning threshold.")
                return gpd.GeoDataFrame(geometry=[], crs=crs or "EPSG:4326")
        elif not gdf_m.empty:
             logger.debug("-> Skipping pruning. Keeping all %s lines.", len(gdf_m))

        logger.info("--- 8. Simplifying ---")
        if simplify_tolerance_m > 0.0 and not gdf_m.empty:
             try:
                 simplified_geoms_m = gdf_m.geometry.simplify(simplify_tolerance_m, preserve_topology=True)
                 gdf.geometry = gpd.GeoSeries(simplified_geoms_m, crs=gdf_m.crs).to_crs(gdf.crs).geometry

             except Exception as simplify_err:
                  logger.error("Error during simplify: %s", simplify_err)

        logger.info("--- 9. Reprojecting final to 4326 ---")
        if gdf.empty:
             return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

        try:
             gdf_final = gdf.to_crs(4326)
        except Exception as crs_err:
             logger.error("Could not reproject to 4326: %s. Returning original CRS '%s'.", crs_err, gdf.crs)
             gdf_final = gdf

        logger.info("✅ Finished create_centerline. Returning %s lines.", len(gdf_final))
        return gdf_final


    def create_polygons_from_bins(
        self,
        bins: List[float],
        labels: List[str],
        skip_labels: Optional[List[str]] = None,
        gaussian_kernel_size: int = 51,
        gaussian_sigma: float = 20.0,
        sieve_threshold: int = 300,
        simplify_tolerance: float = 1e-5,
        min_area: float = 1e-10
    ):
        """
        Classifies the (`self.data_scaled`) raster and vectorizes to Polygons.
        
        This function allows specifying certain labels to "skip"
        processing (smoothing and closing). These classes will retain
        their original (non-smoothed) values and be vectorized in their
        "raw" state.

        Args:
            bins (List[float]): The list of bin thresholds for classification.
                **Important:** The number of `bins` must always be
                `len(labels) + 1`.
                Example: `labels = ["Low", "Medium"]` (2 labels)
                requires `bins = [-1.0, 0.2, 1.0]` (3 bins).
                
            labels (List[str]): The list of class names corresponding to the
                intervals created by `bins`.
                
                **How it works (Example):**
                - `labels = ["Low", "Medium", "High"]`
                - `bins = [-1.0, 0.2, 0.6, 1.0]`
                - **This creates the classes:**
                -   `"Low"`: (Values from -1.0 to 0.2)
                -   `"Medium"`: (Values from 0.2 to 0.6)
                -   `"High"`: (Values from 0.6 to 1.0)
                
            skip_labels (Optional[List[str]]): (Optional) A list of
                label names (from `labels`) to skip processing. These classes
                will NOT be smoothed or closed, but WILL still be vectorized.
            gaussian_kernel_size (int): Kernel size for Gaussian blur.
            gaussian_sigma (float): Sigma for Gaussian blur.
            sieve_threshold (int): Sieve threshold (in pixels) to remove noise.
            simplify_tolerance (float): Simplification tolerance (in CRS units).
            min_area (float): Minimum area (in CRS units) to keep a polygon.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the final
                classified and processed polygons.
        """
        logger.info("Start process 'create_polygons_from_bins' (using skip_labels logic)")

        if not (bins and labels):
             raise ValueError("Both 'bins' and 'labels' must be provided.")
        if len(bins) != len(labels) + 1:
            raise ValueError(f"Number of 'bins' ({len(bins)}) must be 1 more than number of 'labels' ({len(labels)}).")
        
        final_bins = bins
        final_labels = labels
        
        data = self.data_scaled 
        data_raw_ref = self.data_raw_nan 
        
        logger.debug("Using data_to_classify (self.data_scaled)")
        nodata = self.nodata
        transform = self.transform
        crs = self.crs

        skip_indices = set()
        if skip_labels:
            skip_label_set = set(skip_labels)
            skip_indices = {i for i, label in enumerate(final_labels) if label in skip_label_set}

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)

            invalid_mask = np.isnan(data)
            valid_mask = ~invalid_mask

            skip_mask = np.zeros_like(data, dtype=bool)
            if np.any(valid_mask) and skip_indices:
                logger.debug("Pre-classifying data to find skip_mask...")
                temp_classified_values = np.digitize(
                    data[valid_mask], bins=final_bins[1:-1], right=True
                ).astype(np.uint8)
                
                skip_mask[valid_mask] = np.isin(temp_classified_values, list(skip_indices))
            
            valid_for_smooth = valid_mask & (~skip_mask)
            smooth_input = np.where(valid_for_smooth, data, np.nan)
            
            logger.debug(
                "Applying Gaussian smooth (Kernel=%s, Sigma=%s) to non-skipped classes.",
                gaussian_kernel_size, gaussian_sigma
            )
            
            if np.any(valid_for_smooth):
                data_smooth = _gaussian_smooth(
                    smooth_input, ksize=gaussian_kernel_size, sigma=gaussian_sigma
                )
                data = np.where(valid_for_smooth, data_smooth, data)
            else:
                logger.debug("No pixels found to smooth (all valid pixels may be skipped).")
            
            classified = np.full_like(data, fill_value=0, dtype=np.uint8)
            logger.debug("Digitizing final data...")
            
            if np.any(valid_mask):
                 digitized_values = np.digitize(
                     data[valid_mask], bins=final_bins[1:-1], right=True
                 ).astype(np.uint8)

                 max_digitized_index = np.max(digitized_values) if digitized_values.size > 0 else -1
                 if max_digitized_index >= len(final_labels):
                      logger.warning("Digitized index (%s) >= number of labels (%s). Clamping values.",
                                      max_digitized_index, len(final_labels))
                      digitized_values = np.clip(digitized_values, 0, len(final_labels) - 1)
                 
                 classified[valid_mask] = digitized_values
            else:
                 logger.warning("No valid pixels to classify.")
                 return gpd.GeoDataFrame(geometry=[], crs=crs)

            if sieve_threshold > 0:
                 logger.debug("Sieving with threshold %s pixels...", sieve_threshold)
                 classified_sieved = rasterio.features.sieve(
                     classified.astype(rasterio.uint8),
                     sieve_threshold, connectivity=8
                 ).astype(np.uint8)
            else:
                 classified_sieved = classified

            logger.debug("Applying binary closing...")
            temp_closed = classified_sieved.copy()
            processed_indices = set()
            unique_values = np.unique(classified_sieved)
            
            kernel = np.ones((5, 5), np.uint8) 

            for i in unique_values:
                 if i == 0: 
                     continue 
                 
                 if i in skip_indices:
                     logger.debug("Skipping Closing for class index %s (user request).", i)
                     continue
                 
                 if i >= len(final_labels): continue 
                 if i in processed_indices: continue
                 
                 class_mask_valid = (classified_sieved == i) & valid_mask
                 if np.any(class_mask_valid):
                      class_mask_uint8 = class_mask_valid.astype(np.uint8)
                      closed_mask = cv2.morphologyEx(
                          class_mask_uint8, 
                          cv2.MORPH_CLOSE, 
                          kernel
                      )
                      temp_closed[(closed_mask > 0) & valid_mask] = i
                      processed_indices.add(i)
            classified_sieved = temp_closed

            # 7. Polygonize
            logger.debug("Polygonizing features (Vectorizing ALL classes)...")
            polygons = []
            
            for i, label in enumerate(final_labels):
                
                class_mask = (classified_sieved == i) & valid_mask
                if not np.any(class_mask):
                    continue
                
                shapes_gen = rasterio.features.shapes(
                    classified_sieved, 
                    mask=class_mask, 
                    transform=transform
                )

                for geom_dict, val in shapes_gen:
                    if int(val) == i: 
                        geom_shape = shape(geom_dict)
                        if geom_shape.is_valid and geom_shape.area > 0:
                            polygons.append({
                                "class_val": int(val), 
                                "class_name": label, 
                                "geometry": geom_shape
                            })

            if not polygons:
                logger.info("No valid polygons found after vectorization.")
                return gpd.GeoDataFrame(geometry=[], crs=crs)

            logger.debug("Post-processing geometries...")
            gdf_poly = gpd.GeoDataFrame(polygons, crs=crs)

            if min_area > 0 and not gdf_poly.empty:
                try:
                    gdf_poly = gdf_poly[gdf_poly.geometry.area > min_area]
                except Exception as area_err:
                    logger.warning("Error filtering by min_area: %s.", area_err)

            if gdf_poly.empty:
                logger.info("GDF empty after min_area filter.")
                return gdf_poly

            gdf_poly["geometry"] = gdf_poly["geometry"].apply(_fill_holes)

            if simplify_tolerance > 0.0:
                 logger.debug("Simplifying geometry...")
                 try:
                      gdf_poly.geometry = gdf_poly.geometry.simplify(
                           simplify_tolerance, preserve_topology=True
                      )
                 except Exception as simplify_err:
                      logger.error("Error simplifying geometry: %s", simplify_err)

            gdf_poly = gdf_poly[gdf_poly.geometry.is_valid & ~gdf_poly.geometry.is_empty]

            if gdf_poly.empty:
                logger.info("GDF empty after fill/simplify/validate.")
                return gdf_poly

            logger.debug("Dissolving polygons by class...")
            try:
                if "class_val" in gdf_poly.columns and "class_name" in gdf_poly.columns:
                     gdf_poly = gdf_poly.dissolve(by=["class_val", "class_name"]).reset_index()
                     gdf_poly.geometry = gdf_poly.geometry.buffer(0)
                     gdf_poly = gdf_poly[gdf_poly.geometry.is_valid & ~gdf_poly.geometry.is_empty]
                else:
                     logger.warning("Missing 'class_val' or 'class_name' columns for dissolve.")
            except Exception as dissolve_err:
                 logger.error("Error during dissolve: %s.", dissolve_err, exc_info=True)

            if gdf_poly.empty:
                logger.info("GDF empty after dissolve.")
                return gdf_poly

            gdf_poly = gdf_poly.sort_values("class_val", ascending=True)
            
            logger.debug("Applying fix for nested polygons (original logic)...")
            fixed_geoms = []
            used_union = None
            for geom in gdf_poly.geometry:
                if used_union is None:
                    geom_diff = geom
                    used_union = geom
                else:
                    geom_diff = geom.difference(used_union)
                    used_union = unary_union([used_union, geom])
                fixed_geoms.append(geom_diff)
            
            gdf_poly.geometry = fixed_geoms
            gdf_poly = gdf_poly[~gdf_poly.geometry.is_empty].reset_index(drop=True)
            
            logger.info("Finished 'create_polygons_from_bins'. Returning %s polygons.", len(gdf_poly))
            return gdf_poly
            
    def create_polygons_from_bboxes(
        self,
        bboxes: List[BBox],
        attributes: Optional[List[AttributeDict]] = None
    ) -> gpd.GeoDataFrame:
        """
        Converts a list of pixel Bounding Boxes (bboxes) into Polygons.

        This method is designed to convert the output from Object Detection
        or OCR models.

        It uses the georeferencing context (CRS and Transform) loaded
        during the class initialization to convert pixel coordinates
        [xmin, ymin, xmax, ymax] into true georeferenced Polygons.

        Args:
            bboxes (List[BBox]): A list of bounding boxes in pixel coordinates.
                Format: [[xmin, ymin, xmax, ymax], ...].
            attributes (Optional[List[AttributeDict]]): (Optional) A list
                of dictionaries containing attribute information (e.g.,
                label, score, OCR text). Each dictionary in this list
                corresponds to a bounding box in the `bboxes` list.
                Example: [{"label": "tree", "score": 0.9}, ...].

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the Polygon geometries,
                along with any provided attribute columns.
        """
        logger.info("--- Starting process: create_polygons_from_bboxes ---")
        
        gdf = self.converter.from_bboxes(
            bboxes=bboxes,
            attributes=attributes
        )
        
        logger.info("Completed. Created %s polygons from bboxes.", len(gdf))
        return gdf

    def create_points_from_coords(
        self,
        points: List[Keypoint],
        attributes: Optional[List[AttributeDict]] = None
    ) -> gpd.GeoDataFrame:
        """
        Converts a list of pixel coordinates (Keypoints) into Points.

        This method is designed to convert results from Keypoint Detection
        or Pose Estimation models.

        It uses the georeferencing context (CRS and Transform) loaded
        during class initialization to map pixel coordinates [x, y]
        into true georeferenced Points.

        Args:
            points (List[Keypoint]): A list of pixel coordinates.
                Format: [[x1, y1], [x2, y2], ...].
            attributes (Optional[List[AttributeDict]]): (Optional) A list
                of dictionaries containing attribute information (e.g.,
                label, point type). Each dictionary in this list
                corresponds to a point in the `points` list.
                Example: [{"label": "tree_top"}, ...].

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the Point geometries,
                along with any provided attribute columns.
        """
        logger.info("--- Starting process: create_points_from_coords ---")
        
        gdf = self.converter.from_points(
            points=points,
            attributes=attributes
        )
        
        logger.info("Completed. Created %s points from coords.", len(gdf))
        return gdf

    def create_network_from_skeleton(
        self,
        keypoints: List[Keypoint],
        connections: List[Connection],
        attributes: Optional[List[AttributeDict]] = None
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Converts a graph-like Skeleton into a GIS network.

        This method is designed to convert results from graph or skeleton
        models (e.g., road network detection, 3D pose estimation), where
        the output is a set of "nodes" (keypoints) and the "edges"
        (connections) that link them.

        It uses the georeferencing context (CRS and Transform) to convert:
        1. `keypoints` (pixel coordinates) into Point geometries (network nodes).
        2. `connections` (pairs of indices) into LineString geometries
           (network edges).

        Args:
            keypoints (List[Keypoint]): A list of pixel coordinates (the nodes).
                Format: [[x1, y1], [x2, y2], ...].
            connections (List[Connection]): A list of connections (the edges).
                Each connection is a tuple (pair) of indices referencing
                the `keypoints` list. Format: [(0, 1), (1, 2), ...].
            attributes (Optional[List[AttributeDict]]): (Optional) A list
                of attribute dictionaries, one for each *connection*
                (LineString). Example: [{"road_type": "main"}, ...].

        Returns:
            Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: A tuple containing:
                - `gdf_points`: GeoDataFrame of the nodes (Points).
                - `gdf_lines`: GeoDataFrame of the edges (LineStrings).
        """
        logger.info("--- Starting process: create_network_from_skeleton ---")
        
        gdf_points, gdf_lines = self.converter.from_skeleton(
            keypoints=keypoints,
            connections=connections,
            attributes=attributes
        )
        
        logger.info("Completed. Created %s points (nodes) and %s lines (edges).",
                     len(gdf_points), len(gdf_lines))
        return gdf_points, gdf_lines