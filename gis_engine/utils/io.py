"""
File I/O operations for various GIS formats.
"""

import os
import geopandas as gpd
import rasterio
import numpy as np


class FileIO:
    """Handle reading and writing of GIS data formats."""

    # --------------------------------------------------
    # VECTOR I/O
    # --------------------------------------------------

    @staticmethod
    def read_vector(filepath):
        """
        Read vector data (shapefile, geojson, gpkg, etc).

        Returns:
            GeoDataFrame
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Vector file not found: {filepath}")

        try:
            gdf = gpd.read_file(filepath)
            return gdf
        except Exception as e:
            raise RuntimeError(f"Failed to read vector file: {e}")

    @staticmethod
    def write_vector(geodataframe, filepath):
        """
        Write vector data to file.

        Format determined by file extension.
        """
        if not isinstance(geodataframe, gpd.GeoDataFrame):
            raise TypeError("Input must be a GeoDataFrame.")

        try:
            geodataframe.to_file(filepath)
        except Exception as e:
            raise RuntimeError(f"Failed to write vector file: {e}")

    # --------------------------------------------------
    # RASTER I/O
    # --------------------------------------------------

    @staticmethod
    def read_raster(filepath):
        """
        Read raster data.

        Returns:
            (array, metadata)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Raster file not found: {filepath}")

        try:
            with rasterio.open(filepath) as src:
                array = src.read(1)
                meta = src.meta.copy()
                nodata = src.nodata

                if nodata is not None:
                    array = np.where(array == nodata, np.nan, array)

            return array, meta

        except Exception as e:
            raise RuntimeError(f"Failed to read raster file: {e}")

    @staticmethod
    def write_raster(raster, filepath, metadata):
        """
        Write raster data.

        Args:
            raster: NumPy array
            filepath: Output path
            metadata: Raster metadata (from rasterio)
        """
        if not isinstance(raster, np.ndarray):
            raise TypeError("Raster must be a NumPy array.")

        try:
            metadata.update({
                "dtype": raster.dtype,
                "count": 1
            })

            with rasterio.open(filepath, "w", **metadata) as dst:
                dst.write(raster, 1)

        except Exception as e:
            raise RuntimeError(f"Failed to write raster file: {e}")