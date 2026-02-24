"""
Suitability analysis for multi-criteria evaluation.
"""

import numpy as np
import rasterio
from rasterio.enums import Resampling


class SuitabilityAnalysis:
    """Perform multi-criteria suitability analysis using weighted overlay."""

    def __init__(self):
        self.criteria = []
        self.weights = []
        self.meta = None

    # -------------------------------------------------
    # Add Criterion
    # -------------------------------------------------

    def add_criterion(self, raster_path, weight):
        """
        Add a suitability criterion.

        Args:
            raster_path: Path to raster layer.
            weight: Weight for this criterion (0-1).
        """

        if weight < 0:
            raise ValueError("Weight must be positive.")

        self.criteria.append(raster_path)
        self.weights.append(weight)

    # -------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------

    def _normalize_weights(self):
        total = sum(self.weights)
        if total == 0:
            raise ValueError("Sum of weights cannot be zero.")
        self.weights = [w / total for w in self.weights]

    def _read_raster(self, path, reference_meta=None):
        with rasterio.open(path) as src:
            data = src.read(1)

            # Save metadata from first raster
            if reference_meta is None:
                self.meta = src.meta.copy()
                return data

            # Reproject/resample if mismatch
            if (
                src.crs != reference_meta["crs"]
                or src.transform != reference_meta["transform"]
                or src.shape != (reference_meta["height"], reference_meta["width"])
            ):
                data = src.read(
                    1,
                    out_shape=(
                        reference_meta["height"],
                        reference_meta["width"],
                    ),
                    resampling=Resampling.bilinear,
                )

            return data

    # -------------------------------------------------
    # Main Calculation
    # -------------------------------------------------

    def calculate(self, normalize_output=True):
        """
        Calculate suitability index using weighted sum.

        Returns:
            Suitability array (normalized 0–100 if selected)
        """

        if len(self.criteria) == 0:
            raise ValueError("No criteria added.")

        if len(self.criteria) != len(self.weights):
            raise ValueError("Criteria and weights mismatch.")

        self._normalize_weights()

        suitability = None

        for idx, raster_path in enumerate(self.criteria):

            data = self._read_raster(raster_path, self.meta)

            # Replace nodata with 0
            data = np.nan_to_num(data)

            weighted = data * self.weights[idx]

            if suitability is None:
                suitability = weighted
            else:
                suitability += weighted

        # Normalize output to 0-100
        if normalize_output:
            min_val = np.min(suitability)
            max_val = np.max(suitability)

            if max_val - min_val > 0:
                suitability = (suitability - min_val) / (max_val - min_val)
                suitability = suitability * 100

        return suitability

    # -------------------------------------------------
    # Save Output
    # -------------------------------------------------

    def save(self, output_path, suitability_array):
        """Save suitability raster to file."""

        if self.meta is None:
            raise RuntimeError("No reference metadata found.")

        with rasterio.open(output_path, "w", **self.meta) as dst:
            dst.write(suitability_array.astype(rasterio.float32), 1)