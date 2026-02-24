"""
Slope calculation from Digital Elevation Models.
"""

import numpy as np


class SlopeCalculator:
    """Calculate slope from DEM data."""

    def __init__(self, dem_processor):
        """
        Args:
            dem_processor: DEMProcessor instance.
        """
        self.dem_processor = dem_processor

    # --------------------------------------------------
    # Main Calculation
    # --------------------------------------------------

    def calculate(self, method='horn', degrees=True):
        """
        Calculate slope from DEM.

        Args:
            method: 'horn' or 'zevenbergen-thorne'
            degrees: Return slope in degrees (default True)

        Returns:
            Slope raster (numpy array)
        """

        dem = self.dem_processor.array

        if dem is None:
            raise RuntimeError("DEM not loaded. Call dem_processor.load() first.")

        # Get pixel resolution
        xres, yres = self.dem_processor.get_resolution()

        if method == 'horn':
            dzdx, dzdy = self._horn(dem, xres, yres)
        elif method == 'zevenbergen-thorne':
            dzdx, dzdy = self._zevenbergen_thorne(dem, xres, yres)
        else:
            raise ValueError("Invalid method. Choose 'horn' or 'zevenbergen-thorne'.")

        slope = np.sqrt(dzdx**2 + dzdy**2)

        if degrees:
            slope = np.arctan(slope)
            slope = np.degrees(slope)

        return slope

    # --------------------------------------------------
    # Horn Method
    # --------------------------------------------------

    def _horn(self, dem, xres, yres):

        # Pad edges
        padded = np.pad(dem, 1, mode='edge')

        dzdx = (
            (padded[1:-1, 2:] + 2 * padded[2:, 2:] + padded[2:, 1:-1]) -
            (padded[1:-1, :-2] + 2 * padded[2:, :-2] + padded[2:, 1:-1])
        ) / (8 * xres)

        dzdy = (
            (padded[2:, 1:-1] + 2 * padded[2:, 2:] + padded[1:-1, 2:]) -
            (padded[:-2, 1:-1] + 2 * padded[:-2, 2:] + padded[1:-1, 2:])
        ) / (8 * yres)

        return dzdx, dzdy

    # --------------------------------------------------
    # Zevenbergen-Thorne Method
    # --------------------------------------------------

    def _zevenbergen_thorne(self, dem, xres, yres):

        padded = np.pad(dem, 1, mode='edge')

        dzdx = (
            padded[1:-1, 2:] - padded[1:-1, :-2]
        ) / (2 * xres)

        dzdy = (
            padded[2:, 1:-1] - padded[:-2, 1:-1]
        ) / (2 * yres)

        return dzdx, dzdy