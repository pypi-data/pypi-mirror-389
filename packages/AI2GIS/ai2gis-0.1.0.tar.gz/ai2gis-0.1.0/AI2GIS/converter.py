"""
Core GeoAIConverter Class.
Responsible for converting basic AI formats (BBox, Mask, Skeleton, Points)
to GeoDataFrames.
"""
import rasterio
import rasterio.features
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString, shape, mapping
from shapely.ops import unary_union
from pathlib import Path
import warnings
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Union, Tuple
import logging

# Import data types from local file
from .types import BBox, AttributeDict, Keypoint, Connection

# Setup logger
logger = logging.getLogger(__name__)

@dataclass
class GeoAIConverter:
    """
    Converts AI results (BBoxes, Masks, Skeletons, Points) to GeoDataFrames.

    Can be initialized in ONE of two ways:
    1. Provide `geotiff_path`: The class will automatically read CRS and Transform.
    2. Provide `crs` AND `transform` directly: Skips file reading.

    Attributes:
        geotiff_path (Optional[Union[str, Path]]): Path to the GeoTIFF (if using method 1).
        crs (rasterio.crs.CRS): Coordinate Reference System (read or provided).
        transform (rasterio.Affine): Affine transform (read or provided).
    
    --- (Tiếng Việt) ---
    Chuyển đổi kết quả AI (BBoxes, Masks, Skeletons, Points) sang GeoDataFrame.

    Có thể khởi tạo bằng MỘT trong hai cách:
    1. Cung cấp `geotiff_path`: Class sẽ tự động đọc CRS và Transform từ file.
    2. Cung cấp `crs` VÀ `transform` trực tiếp: Bỏ qua việc đọc file.

    Attributes:
        geotiff_path (Optional[Union[str, Path]]): Đường dẫn đến file GeoTIFF (nếu dùng cách 1).
        crs (rasterio.crs.CRS): Hệ quy chiếu (được đọc hoặc cung cấp).
        transform (rasterio.Affine): Phép biến đổi Affine (được đọc hoặc cung cấp).
    """
    geotiff_path: Optional[Union[str, Path]] = field(default=None, init=True)
    crs: Optional[rasterio.crs.CRS] = field(default=None, init=True)
    transform: Optional[rasterio.Affine] = field(default=None, init=True)

    def __post_init__(self):
        """
        Validates and loads CRS/Transform after initial parameters are assigned.
        
        --- (Tiếng Việt) ---
        Kiểm tra và tải CRS/Transform sau khi các tham số ban đầu được gán.
        """
        if self.geotiff_path and (self.crs is None or self.transform is None):
            # If path exists AND crs/transform were not provided -> Read from file
            try:
                with rasterio.open(self.geotiff_path) as src:
                    self.crs = src.crs
                    self.transform = src.transform
            except rasterio.errors.RasterioIOError as e:
                logger.error(
                    "Reference GeoTIFF file not found at '%s'.",
                    self.geotiff_path, exc_info=True
                )
                raise FileNotFoundError(f"Reference GeoTIFF file not found at: {self.geotiff_path}") from e
            except Exception as e:
                logger.error(
                    "Unknown error when reading GeoTIFF file: %s", e, exc_info=True
                )
                raise e
        elif self.crs and self.transform:
            # If crs AND transform were provided directly
            pass
        else:
            # Catch-all: Insufficient information
            raise ValueError("Must provide `geotiff_path` OR both `crs` and `transform` to initialize GeoAIConverter.")

        # Final check after logic has run
        if not self.crs or not self.transform:
             # This should not happen if logic is correct, but as a safeguard
             raise ValueError("Could not determine CRS or Transform for GeoAIConverter after initialization.")

    # --- CONVERSION METHODS (from_...) ---

    def from_bboxes(
        self,
        bboxes: List[BBox],
        attributes: Optional[List[AttributeDict]] = None
    ) -> gpd.GeoDataFrame:
        """
        Converts Bounding Boxes (pixel) to a GeoDataFrame (Polygon).

        Args:
            bboxes (List[BBox]): List of bounding boxes [xmin, ymin, xmax, ymax].
            attributes (Optional[List[AttributeDict]]): Optional list of
                dictionaries (one per bbox) to add as attributes.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame of Polygons.
            
        --- (Tiếng Việt) ---
        Chuyển đổi Bounding Boxes (pixel) sang GeoDataFrame (Polygon).

        Args:
            bboxes (List[BBox]): Danh sách bounding box [xmin, ymin, xmax, ymax].
            attributes (Optional[List[AttributeDict]]): (Tùy chọn) Danh sách
                các dictionary (một cho mỗi bbox) để thêm làm thuộc tính.

        Returns:
            gpd.GeoDataFrame: Một GeoDataFrame chứa các Polygons.
        """
        if not self.transform:
            raise ValueError("Invalid transform. GeoAIConverter initialization failed.")
        
        polygons = []
        for bbox in bboxes:
            xmin, ymin, xmax, ymax = bbox
            corners = [
                self.transform * (xmin, ymin),
                self.transform * (xmax, ymin),
                self.transform * (xmax, ymax),
                self.transform * (xmin, ymax),
            ]
            polygons.append(Polygon(corners))
        
        gdf = gpd.GeoDataFrame(geometry=polygons, crs=self.crs)
        
        if attributes:
            if len(attributes) == len(gdf):
                attr_df = gpd.pd.DataFrame(attributes)
                gdf = gpd.pd.concat([gdf, attr_df], axis=1)
            else:
                logger.warning(
                    "Number of 'attributes' (%s) does not match "
                    "number of 'bboxes' (%s). Skipping attributes.",
                    len(attributes), len(bboxes)
                )
        return gdf

    def from_mask(
        self,
        mask_data: np.ndarray,
        connectivity: int = 4,
        min_area_pixels: int = 0,
        simplify_tolerance: float = 0.0,
    ) -> gpd.GeoDataFrame:
        """
        Vectorizes, cleans, and optimizes a mask array.

        Args:
            mask_data (np.ndarray): The 2D mask array (e.g., uint8).
            connectivity (int): 4 or 8 connectivity for polygonizing.
            min_area_pixels (int): Sieve threshold to remove small polygons.
            simplify_tolerance (float): Simplification tolerance (in CRS units).

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame of Polygons, dissolved by raster value.
            
        --- (Tiếng Việt) ---
        Vector hóa, làm sạch, và tối ưu hóa một mảng mask.

        Args:
            mask_data (np.ndarray): Mảng mask 2D (ví dụ: uint8).
            connectivity (int): Kết nối 4 hoặc 8 để tạo polygon.
            min_area_pixels (int): Ngưỡng Sieve (sàng lọc) để xóa polygon nhỏ.
            simplify_tolerance (float): Dung sai đơn giản hóa (theo đơn vị CRS).

        Returns:
            gpd.GeoDataFrame: Một GeoDataFrame chứa các Polygon, đã được
                hợp nhất (dissolve) theo giá trị raster.
        """
        if not self.transform:
            raise ValueError("Invalid transform. GeoAIConverter initialization failed.")

        mask = np.asarray(mask_data)

        # --- 1. Sieve ---
        if min_area_pixels > 0:
            binary_mask = (mask > 0).astype(np.uint8)
            cleaned_mask = rasterio.features.sieve(
                binary_mask, min_area_pixels, connectivity=connectivity
            )
            mask = np.where(cleaned_mask == 1, mask, 0)

        # --- 2. Polygonize ---
        geoms_by_label = {}
        shapes_gen = rasterio.features.shapes(
            mask,
            mask=(mask > 0).astype(np.uint8),
            transform=self.transform,
            connectivity=connectivity,
        )
        for geom_dict, value in shapes_gen:
            value_int = int(value)
            if value_int == 0:
                continue

            g = shape(geom_dict)
            if not g.is_empty:
                if value_int not in geoms_by_label:
                    geoms_by_label[value_int] = []
                geoms_by_label[value_int].append(g)

        # --- 3. Post-processing ---
        processed_features = []
        for val, parts in geoms_by_label.items():
            if not parts: continue

            merged = unary_union(parts)

            if not merged.is_valid:
                try:
                    merged = merged.buffer(0)
                except Exception:
                    logger.warning("Could not fix invalid geometry for raster_val=%s", val, exc_info=False)
                    pass

            if simplify_tolerance > 0.0 and not merged.is_empty:
                merged = merged.simplify(simplify_tolerance) 

            if merged.is_empty: continue

            processed_features.append(
                {"properties": {"raster_val": val}, "geometry": mapping(merged)}
            )

        # --- 4. Create GeoDataFrame ---
        if not processed_features:
            logger.warning("No features found after processing. Returning empty GDF.")
            return gpd.GeoDataFrame(columns=["raster_val", "geometry"], crs=self.crs)

        gdf = gpd.GeoDataFrame.from_features(processed_features, crs=self.crs)
        return gdf

    def from_points(
        self,
        points: List[Keypoint],
        attributes: Optional[List[AttributeDict]] = None
    ) -> gpd.GeoDataFrame:
        """
        Converts a list of pixel coordinates to a GeoDataFrame (Point).

        Args:
            points (List[Keypoint]): List of [x, y] pixel coordinates.
            attributes (Optional[List[AttributeDict]]): Optional list of
                dictionaries (one per point) to add as attributes.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame of Points.
            
        --- (Tiếng Việt) ---
        Chuyển đổi danh sách tọa độ điểm (pixel) sang GeoDataFrame (Point).

        Args:
            points (List[Keypoint]): Danh sách tọa độ pixel [x, y].
            attributes (Optional[List[AttributeDict]]): (Tùy chọn) Danh sách
                các dictionary (một cho mỗi điểm) để thêm làm thuộc tính.

        Returns:
            gpd.GeoDataFrame: Một GeoDataFrame chứa các Points.
        """
        if not self.transform:
            raise ValueError("Invalid transform. GeoAIConverter initialization failed.")
        
        geo_points = [Point(self.transform * (x, y)) for x, y in points]
        gdf = gpd.GeoDataFrame(geometry=geo_points, crs=self.crs)
        
        if attributes:
            if len(attributes) == len(gdf):
                attr_df = gpd.pd.DataFrame(attributes)
                gdf = gpd.pd.concat([gdf, attr_df], axis=1)
            else:
                logger.warning(
                    "Number of 'attributes' (%s) does not match "
                    "number of 'points' (%s). Skipping attributes.",
                    len(attributes), len(points)
                )
        return gdf

    def from_skeleton(
        self,
        keypoints: List[Keypoint],
        connections: List[Connection],
        attributes: Optional[List[AttributeDict]] = None
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Converts Keypoints and Connections (pixel) to GDFs (Point and LineString).

        Args:
            keypoints (List[Keypoint]): List of [x, y] pixel coordinates (nodes).
            connections (List[Connection]): List of (start_idx, end_idx)
                tuples referencing the keypoints list (edges).
            attributes (Optional[List[AttributeDict]]): Optional list of
                dictionaries (one per *connection*) to add as attributes
                to the lines GDF.

        Returns:
            Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: (point_gdf, lines_gdf)
            
        --- (Tiếng Việt) ---
        Chuyển đổi Keypoints và Connections (pixel) sang GDF (Point và LineString).

        Args:
            keypoints (List[Keypoint]): Danh sách tọa độ pixel [x, y] (các nút).
            connections (List[Connection]): Danh sách các tuple (start_idx, end_idx)
                tham chiếu đến danh sách keypoints (các cạnh).
            attributes (Optional[List[AttributeDict]]): (Tùy chọn) Danh sách
                các dictionary (một cho mỗi *connection*) để thêm làm thuộc tính
                cho GDF chứa các đường (lines).

        Returns:
            Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: (point_gdf, lines_gdf)
        """
        if not self.transform:
            raise ValueError("Invalid transform. GeoAIConverter initialization failed.")

        geo_points = [Point(self.transform * (x, y)) for x, y in keypoints]
        geo_lines = []
        valid_attributes = [] if attributes else None # Init empty list if attributes are expected

        for i, (start_idx, end_idx) in enumerate(connections):
            # Check for valid indices
            if 0 <= start_idx < len(geo_points) and 0 <= end_idx < len(geo_points):
                line = LineString([geo_points[start_idx], geo_points[end_idx]])
                geo_lines.append(line)
                
                # Only add attribute if connection is valid and attributes were provided
                if attributes is not None: 
                    if i < len(attributes):
                        valid_attributes.append(attributes[i])
                    else:
                        logger.warning("Connection index %s is out of bounds for attributes (length %s).", i, len(attributes))

            else:
                logger.warning(
                    "Invalid connection indices (%s, %s) for %s keypoints. Skipping.",
                    start_idx, end_idx, len(geo_points)
                )

        point_gdf = gpd.GeoDataFrame(geometry=geo_points, crs=self.crs)
        lines_gdf = gpd.GeoDataFrame(geometry=geo_lines, crs=self.crs)

        # Only concat attributes if valid_attributes is not None
        if valid_attributes is not None:
            if len(valid_attributes) == len(lines_gdf):
                attr_df = gpd.pd.DataFrame(valid_attributes)
                attr_df.index = lines_gdf.index # Ensure index alignment
                lines_gdf = gpd.pd.concat([lines_gdf, attr_df], axis=1)
            else:
                logger.warning(
                    "Number of valid 'attributes' (%s) does not match "
                    "number of created 'connections' (%s). Attributes may be misaligned.",
                    len(valid_attributes), len(lines_gdf)
                )
                        
        return point_gdf, lines_gdf