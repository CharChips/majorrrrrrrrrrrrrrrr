"""
Spatial overlay operations.
"""

import geopandas as gpd


class Overlay:
    """Perform spatial overlays between layers."""

    def __init__(self, layer1: gpd.GeoDataFrame, layer2: gpd.GeoDataFrame):
        """
        Initialize overlay operation.

        Args:
            layer1: First GeoDataFrame.
            layer2: Second GeoDataFrame.
        """

        if not isinstance(layer1, gpd.GeoDataFrame) or not isinstance(layer2, gpd.GeoDataFrame):
            raise TypeError("Both layers must be GeoDataFrame objects.")

        self.layer1 = layer1.copy()
        self.layer2 = layer2.copy()

        self._validate_crs()
        self._clean_geometries()

    # -----------------------------
    # Internal Utilities
    # -----------------------------

    def _validate_crs(self):
        """Ensure both layers share same CRS."""
        if self.layer1.crs != self.layer2.crs:
            print("CRS mismatch detected. Reprojecting layer2 to layer1 CRS.")
            self.layer2 = self.layer2.to_crs(self.layer1.crs)

    def _clean_geometries(self):
        """Fix invalid geometries."""
        self.layer1 = self.layer1[self.layer1.is_valid]
        self.layer2 = self.layer2[self.layer2.is_valid]

    # -----------------------------
    # Overlay Operations
    # -----------------------------

    def intersection(self):
        """Compute spatial intersection."""
        try:
            result = gpd.overlay(self.layer1, self.layer2, how="intersection")
            return result
        except Exception as e:
            raise RuntimeError(f"Intersection failed: {e}")

    def union(self):
        """Compute spatial union."""
        try:
            result = gpd.overlay(self.layer1, self.layer2, how="union")
            return result
        except Exception as e:
            raise RuntimeError(f"Union failed: {e}")

    def difference(self):
        """Compute spatial difference (layer1 - layer2)."""
        try:
            result = gpd.overlay(self.layer1, self.layer2, how="difference")
            return result
        except Exception as e:
            raise RuntimeError(f"Difference failed: {e}")