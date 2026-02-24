"""
Coordinate Reference System (CRS) management.
"""

import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import CRS


class CRSManager:
    """Manage coordinate reference systems and transformations."""

    def __init__(self):
        self.source_crs = None
        self.target_crs = None

    # --------------------------------------------------
    # Set CRS
    # --------------------------------------------------

    def set_crs(self, crs):
        """
        Set source CRS.

        Args:
            crs: CRS string (e.g., 'EPSG:4326') or WKT
        """
        try:
            self.source_crs = CRS.from_user_input(crs)
        except Exception:
            raise ValueError(f"Invalid CRS: {crs}")

    # --------------------------------------------------
    # Reproject Data
    # --------------------------------------------------

    def reproject(self, data, target_crs):
        """
        Reproject vector or raster data.

        Args:
            data: GeoDataFrame OR raster file path
            target_crs: Target CRS string

        Returns:
            Reprojected data
        """

        self.target_crs = CRS.from_user_input(target_crs)

        # --------------------------
        # VECTOR DATA
        # --------------------------
        if isinstance(data, gpd.GeoDataFrame):
            if data.crs is None:
                raise ValueError("Input GeoDataFrame has no CRS defined.")

            return data.to_crs(self.target_crs)

        # --------------------------
        # RASTER DATA
        # --------------------------
        elif isinstance(data, str):
            with rasterio.open(data) as src:

                transform, width, height = calculate_default_transform(
                    src.crs,
                    self.target_crs,
                    src.width,
                    src.height,
                    *src.bounds
                )

                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': self.target_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })

                destination = rasterio.io.MemoryFile().open(**kwargs)

                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(destination, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=self.target_crs,
                        resampling=Resampling.bilinear
                    )

                return destination

        else:
            raise TypeError("Unsupported data type for reprojection.")

    # --------------------------------------------------
    # CRS Information
    # --------------------------------------------------

    def get_crs_info(self, crs):
        """
        Get CRS metadata.

        Args:
            crs: CRS string or EPSG code

        Returns:
            Dictionary with CRS info
        """
        crs_obj = CRS.from_user_input(crs)

        return {
            "name": crs_obj.name,
            "epsg": crs_obj.to_epsg(),
            "is_projected": crs_obj.is_projected,
            "is_geographic": crs_obj.is_geographic,
            "axis_info": [axis.name for axis in crs_obj.axis_info],
            "area_of_use": crs_obj.area_of_use.name
        }