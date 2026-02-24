"""
Vector buffer operations.
"""

import geopandas as gpd


class Buffer:
    """Create buffers around vector features."""

    def __init__(self, geodataframe):
        """
        Args:
            geodataframe: Input GeoDataFrame with geometry.
        """

        if not isinstance(geodataframe, gpd.GeoDataFrame):
            raise TypeError("Input must be a GeoDataFrame.")

        if geodataframe.crs is None:
            raise ValueError("GeoDataFrame must have a defined CRS.")

        self.gdf = geodataframe.copy()

    # --------------------------------------------------
    # Main Buffer Operation
    # --------------------------------------------------

    def buffer(self, distance, dissolve=False):
        """
        Create buffers around geometries.

        Args:
            distance: Buffer distance (in CRS units).
            dissolve: Merge all buffers into single geometry.

        Returns:
            GeoDataFrame with buffered geometries.
        """

        # Warn if CRS is geographic (degrees)
        if self.gdf.crs.is_geographic:
            raise ValueError(
                "Buffer distance in degrees is unreliable. "
                "Reproject to projected CRS (e.g., UTM) before buffering."
            )

        # Fix invalid geometries
        self.gdf["geometry"] = self.gdf.geometry.buffer(0)

        buffered = self.gdf.copy()
        buffered["geometry"] = buffered.geometry.buffer(distance)

        if dissolve:
            buffered = buffered.dissolve()

        return buffered