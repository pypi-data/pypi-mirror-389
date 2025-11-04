"""
(Internal) Utility functions for the AI2GIS library.

This module contains:
- High-performance computation functions using Numba and OpenCV (for Centerline extraction)
- Common helper functions such as fill_holes() and gaussian_smooth().

Note: This file is for internal use only and not part of the public API.
"""
import numpy as np
import cv2
import numba
from numba import jit
from rasterio.transform import Affine
from shapely.geometry import LineString, Polygon, MultiPolygon
from typing import List, Tuple, Set, Union, TYPE_CHECKING
import warnings
import logging


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    PixelCoord = Tuple[int, int]
else:
    PixelCoord = Tuple[int, int]


def _fill_holes(geom: Union[Polygon, MultiPolygon]) -> Union[Polygon, MultiPolygon]:
    """(Internal) Remove interior holes from a Polygon or MultiPolygon."""
    if geom.geom_type == "Polygon":
        return Polygon(geom.exterior)
    elif geom.geom_type == "MultiPolygon":
        return MultiPolygon([Polygon(p.exterior) for p in geom.geoms])
    return geom


def _gaussian_smooth(img: np.ndarray, ksize: int = 31, sigma: float = 3) -> np.ndarray:
    """(Internal) Apply Gaussian smoothing to an image while ignoring NaN values."""
    img_copy = img.copy().astype(np.float32)
    nan_mask = np.isnan(img_copy)

    if ksize % 2 == 0:
        logger.warning("Gaussian kernel size %s is even, incrementing to %s.", ksize, ksize + 1)
        ksize += 1

    img_filled = np.nan_to_num(img_copy, nan=0.0)
    valid_mask = (~nan_mask).astype(np.float32)
    blurred_sum = cv2.GaussianBlur(img_filled, (ksize, ksize), sigma)
    blurred_weight = cv2.GaussianBlur(valid_mask, (ksize, ksize), sigma)

    smoothed = np.divide(blurred_sum, blurred_weight,
                         out=np.zeros_like(blurred_sum), where=blurred_weight > 0)

    smoothed[nan_mask] = np.nan
    return smoothed


NEIGHBORS8_ARRAY = np.array([
    [-1, -1], [-1, 0], [-1, 1],
    [ 0, -1],          [ 0, 1],
    [ 1, -1], [ 1, 0], [ 1, 1]
], dtype=np.int32)


def _pixel_centers_to_xy(
    transform: Affine, 
    rr: np.ndarray, 
    cc: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Convert pixel (row, col) coordinates to geographic (x, y) coordinates at the pixel centers."""
    xs, ys = transform * (cc + 0.5, rr + 0.5)
    return xs, ys


@jit(nopython=True)
def _get_neighbors(mask: np.ndarray, r: int, c: int) -> List[Tuple[int, int]]:
    """(JIT-compiled) Get 8-connected neighboring pixels with a 'True' value."""
    H, W = mask.shape
    neighbors = []
    for i in range(NEIGHBORS8_ARRAY.shape[0]):
        dr = NEIGHBORS8_ARRAY[i, 0]
        dc = NEIGHBORS8_ARRAY[i, 1]
        rr, cc = r + dr, c + dc
        if 0 <= rr < H and 0 <= cc < W and mask[rr, cc]:
            neighbors.append((rr, cc))
    return neighbors


@jit(nopython=True)
def _trace_path(
    mask: np.ndarray,
    start: Tuple[int, int],
    endpoints: Set[Tuple[int, int]],
    junctions: Set[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    """(JIT-compiled) Trace along a skeleton path starting from 'start' until a junction or endpoint is reached."""
    path = [start]
    cur = start
    prev = (-1, -1)
    while True:
        nbrs = _get_neighbors(mask, *cur)
        nxt = None
        for n in nbrs:
            if n != prev:
                nxt = n
                break
        if nxt is None:
            break
        prev, cur = cur, nxt
        path.append(cur)
        if cur in endpoints or cur in junctions:
            break
    return path


@jit(nopython=True)
def _trace_loop_path(
    mask: np.ndarray,
    start_node: Tuple[int, int],
    endpoints: Set[Tuple[int, int]],
    junctions: Set[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    """
    (JIT-compiled) Trace along a closed loop starting from 'start_node'
    until returning to the start or reaching a junction.
    """
    path = [start_node]
    cur = start_node
    prev = (-1, -1)

    while True:
        nbrs = _get_neighbors(mask, *cur)

        nxt = None
        for n in nbrs:
            if n != prev:
                nxt = n
                break

        if nxt is None:
            break

        prev, cur = cur, nxt

        if cur == start_node:
            break

        path.append(cur)

        if cur in endpoints or cur in junctions:
            break

    return path


def _compute_degree(img: np.ndarray) -> np.ndarray:
    """Compute the 'degree' (number of connected neighbors) for each skeleton pixel."""
    K = np.ones((3, 3), dtype=np.uint8)
    s = cv2.filter2D(img.astype(np.uint8), ddepth=cv2.CV_16S,
                     kernel=K, borderType=cv2.BORDER_CONSTANT)
    deg = (s - img).astype(np.int16)
    return deg


def _build_lines(paths: List[List[Tuple[int, int]]], transform: Affine) -> List[LineString]:
    """Convert a list of traced pixel paths into geographic LineStrings."""
    lines = []
    for path in paths:
        if len(path) < 2:
            continue

        rr = np.asarray([p[0] for p in path], dtype=np.float64)
        cc = np.asarray([p[1] for p in path], dtype=np.float64)
        xs, ys = _pixel_centers_to_xy(transform, rr, cc)
        coords = list(zip(xs.tolist(), ys.tolist()))

        if len(coords) >= 2:
            lines.append(LineString(coords))
    return lines


def _trace_skeleton_paths(skel: np.ndarray) -> List[List[Tuple[int, int]]]:
    """[CORE LOGIC] Trace all continuous paths in a binary skeleton image."""
    mask = skel.astype(bool)
    if not mask.any():
        return []

    logger.debug("Computing pixel degree (neighbor count) for skeleton...")
    deg = _compute_degree(mask.astype(np.uint8))
    coords = np.argwhere(mask)

    endpoints = {(int(r), int(c)) for r, c in coords if deg[r, c] == 1}
    junctions = {(int(r), int(c)) for r, c in coords if deg[r, c] >= 3}
    visited = set()
    paths = []

    logger.debug("Stage 1: Tracing from %s endpoints...", len(endpoints))
    for s in list(endpoints):
        if s in visited:
            continue
        path = _trace_path(mask, s, endpoints, junctions)
        for p in path:
            visited.add(p)
        if len(path) >= 2:
            paths.append(path)

    logger.debug("-> Stage 1 complete: Found %s paths from endpoints.", len(paths))

    loop_candidates = {(int(r), int(c)) for r, c in coords
                       if deg[r, c] == 2 and (int(r), int(c)) not in visited}

    logger.debug("Stage 2: Processing %s loop candidates...", len(loop_candidates))

    count = 0
    total_loops = len(loop_candidates)

    while loop_candidates:
        s = loop_candidates.pop()
        if s in visited:
            continue

        count += 1
        if count % 1000 == 0:
            logger.debug(
                "-> Stage 2: Processing loops... %s/%s (remaining %s candidates)",
                count, total_loops, len(loop_candidates)
            )

        path = _trace_loop_path(mask, s, endpoints, junctions)

        for p in path:
            visited.add(p)
            loop_candidates.discard(p)

        if len(path) >= 2:
            paths.append(path)

    logger.debug("-> Stage 2 complete: Found %s total paths.", len(paths))
    return paths
