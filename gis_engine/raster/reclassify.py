"""
Raster reclassification operations.
"""

import numpy as np
import rasterio


class Reclassify:
    """Reclassify raster values into new categories."""

    def __init__(self, raster):
        """
        Args:
            raster: Input raster array OR raster file path.
        """

        self.meta = None

        if isinstance(raster, str):
            with rasterio.open(raster) as src:
                self.raster = src.read(1)
                self.meta = src.meta.copy()
                self.nodata = src.nodata
        elif isinstance(raster, np.ndarray):
            self.raster = raster
            self.nodata = None
        else:
            raise TypeError("Raster must be a file path or numpy array.")

        self.raster = np.array(self.raster)

    # --------------------------------------------------
    # Apply Reclassification Rules
    # --------------------------------------------------

    def apply_rules(self, classification_rules, default_value=0):
        """
        Apply reclassification rules.

        Args:
            classification_rules:
                List of tuples:
                [(min, max, new_value), ...]

            default_value:
                Value assigned if no rule matches.

        Returns:
            Reclassified raster (numpy array)
        """

        result = np.full_like(self.raster, default_value, dtype=np.float32)

        for rule in classification_rules:
            min_val, max_val, new_val = rule

            mask = (self.raster >= min_val) & (self.raster <= max_val)
            result[mask] = new_val

        # Preserve nodata if exists
        if self.nodata is not None:
            result[self.raster == self.nodata] = self.nodata

        return result

    # --------------------------------------------------
    # Exact Value Mapping (Optional)
    # --------------------------------------------------

    def apply_value_map(self, value_map):
        """
        Reclassify exact values.

        Args:
            value_map: dict {old_value: new_value}

        Returns:
            Reclassified raster
        """

        result = self.raster.copy()

        for old_val, new_val in value_map.items():
            result[self.raster == old_val] = new_val

        return result

    # --------------------------------------------------
    # Save Output
    # --------------------------------------------------

    def save(self, output_path, array):
        """Save reclassified raster."""

        if self.meta is None:
            raise RuntimeError("No metadata available for saving.")

        with rasterio.open(output_path, "w", **self.meta) as dst:
            dst.write(array.astype(rasterio.float32), 1)