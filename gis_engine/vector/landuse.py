"""
Land use analysis operations.
"""

import geopandas as gpd
import pandas as pd


class LandUseAnalysis:
    """Analyze land use classification and distribution."""

    def __init__(self, landuse_layer, class_column="landuse"):
        """
        Args:
            landuse_layer: GeoDataFrame with land use classes.
            class_column: Column containing land use category.
        """

        if not isinstance(landuse_layer, gpd.GeoDataFrame):
            raise TypeError("Input must be a GeoDataFrame.")

        if landuse_layer.crs is None:
            raise ValueError("GeoDataFrame must have a defined CRS.")

        if class_column not in landuse_layer.columns:
            raise ValueError(f"Column '{class_column}' not found in data.")

        self.landuse = landuse_layer.copy()
        self.class_column = class_column

    # --------------------------------------------------
    # Calculate Statistics
    # --------------------------------------------------

    def calculate_statistics(self):
        """
        Calculate land use area statistics.

        Returns:
            DataFrame with class, area, percentage.
        """

        # Must be projected CRS for area calculation
        if self.landuse.crs.is_geographic:
            raise ValueError(
                "Area calculation requires projected CRS (meters)."
            )

        self.landuse["area"] = self.landuse.geometry.area

        stats = (
            self.landuse
            .groupby(self.class_column)["area"]
            .sum()
            .reset_index()
        )

        total_area = stats["area"].sum()
        stats["percentage"] = (stats["area"] / total_area) * 100

        return stats.sort_values("area", ascending=False)

    # --------------------------------------------------
    # Filter by Class
    # --------------------------------------------------

    def filter_by_class(self, class_name, dissolve=False):
        """
        Filter land use by class.

        Args:
            class_name: Name of land use category.
            dissolve: Merge geometries of same class.

        Returns:
            Filtered GeoDataFrame.
        """

        filtered = self.landuse[
            self.landuse[self.class_column] == class_name
        ].copy()

        if dissolve:
            filtered = filtered.dissolve()

        return filtered