"""
DEM (Digital Elevation Model) processing.
"""

import rasterio
import numpy as np


class DEMProcessor:
    """Processor for Digital Elevation Model operations."""

    def __init__(self, dem_path):
        """
        Args:
            dem_path: Path to the DEM raster file.
        """
        self.dem_path = dem_path
        self.dataset = None
        self.array = None
        self.meta = None

    # --------------------------------------------------
    # Load DEM
    # --------------------------------------------------

    def load(self):
        """
        Load DEM data into memory.

        Returns:
            DEM array (numpy)
        """
        self.dataset = rasterio.open(self.dem_path)
        self.array = self.dataset.read(1)
        self.meta = self.dataset.meta.copy()

        # Replace nodata with NaN
        if self.meta.get("nodata") is not None:
            self.array = np.where(
                self.array == self.meta["nodata"],
                np.nan,
                self.array
            )

        return self.array

    # --------------------------------------------------
    # Get Geographic Bounds
    # --------------------------------------------------

    def get_bounds(self):
        """
        Get DEM geographic bounds.

        Returns:
            Dictionary containing bounding box coordinates.
        """
        if self.dataset is None:
            raise RuntimeError("DEM not loaded. Call load() first.")

        bounds = self.dataset.bounds

        return {
            "left": bounds.left,
            "right": bounds.right,
            "top": bounds.top,
            "bottom": bounds.bottom
        }

    # --------------------------------------------------
    # Additional Useful Methods
    # --------------------------------------------------

    def get_crs(self):
        """Return coordinate reference system."""
        if self.dataset is None:
            raise RuntimeError("DEM not loaded.")
        return self.dataset.crs

    def get_resolution(self):
        """Return pixel resolution."""
        if self.dataset is None:
            raise RuntimeError("DEM not loaded.")
        return self.dataset.res

    def get_shape(self):
        """Return raster shape."""
        if self.dataset is None:
            raise RuntimeError("DEM not loaded.")
        return self.array.shape

    def close(self):
        """Close dataset properly."""
        if self.dataset is not None:
            self.dataset.close()