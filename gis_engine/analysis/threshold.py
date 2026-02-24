"""
Thresholding and classification operations.
"""

import numpy as np
import rasterio


class Threshold:
    """Apply thresholds to raster data for classification."""

    def __init__(self, raster):
        """
        Initialize threshold operation.

        Args:
            raster: Input raster array OR raster file path.
        """
        self.meta = None

        if isinstance(raster, str):
            with rasterio.open(raster) as src:
                self.raster = src.read(1)
                self.meta = src.meta.copy()
        elif isinstance(raster, np.ndarray):
            self.raster = raster
        else:
            raise TypeError("Raster must be a file path or numpy array.")

        self.raster = np.nan_to_num(self.raster)

    # ---------------------------------------------------
    # Binary Threshold
    # ---------------------------------------------------

    def apply_threshold(self, min_value, max_value):
        """
        Apply binary threshold.

        Returns:
            Binary raster (1 = within range, 0 = outside)
        """

        if min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value.")

        result = np.where(
            (self.raster >= min_value) & (self.raster <= max_value),
            1,
            0
        )

        return result

    # ---------------------------------------------------
    # Multi-Class Classification
    # ---------------------------------------------------

    def classify(self, class_ranges):
        """
        Multi-class classification.

        Args:
            class_ranges: List of tuples
                          [(min, max, class_value), ...]

        Returns:
            Classified raster
        """

        classified = np.zeros_like(self.raster)

        for min_val, max_val, class_val in class_ranges:
            mask = (self.raster >= min_val) & (self.raster <= max_val)
            classified[mask] = class_val

        return classified

    # ---------------------------------------------------
    # Save Output
    # ---------------------------------------------------

    def save(self, output_path, array):
        """Save result to raster file."""

        if self.meta is None:
            raise RuntimeError("No metadata available for saving.")

        with rasterio.open(output_path, "w", **self.meta) as dst:
            dst.write(array.astype(rasterio.float32), 1)