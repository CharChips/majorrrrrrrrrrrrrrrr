"""
OpenStreetMap (OSM) data loader.
"""

import geopandas as gpd

class OSMLoader:
    """Load and process OpenStreetMap data."""

    def __init__(self):
        self.data = None

    # --------------------------------------------------
    # Load from Bounding Box (Online)
    # --------------------------------------------------

    def load_from_bbox(self, bbox, tags):
        """
        Load OSM data from bounding box using osmnx.

        Args:
            bbox: (minx, miny, maxx, maxy)
            tags: dict of OSM tags
                  Example:
                  {"highway": True}
                  {"landuse": ["industrial", "commercial"]}

        Returns:
            GeoDataFrame
        """

        try:
            import osmnx as ox
        except ImportError:
            raise ImportError("osmnx must be installed to use this function.")

        minx, miny, maxx, maxy = bbox

        gdf = ox.features_from_bbox(
            north=maxy,
            south=miny,
            east=maxx,
            west=minx,
            tags=tags
        )

        gdf = gdf.reset_index(drop=True)

        self.data = gdf
        return gdf

    # --------------------------------------------------
    # Load from OSM File (.osm / .pbf)
    # --------------------------------------------------

    def load_from_file(self, osm_file, tags=None):
        """
        Load OSM data from file using pyrosm.
        Args:
            osm_file: Path to .osm or .pbf file
            tags: Optional tag filter
        Returns:
            GeoDataFrame
        """

        try:
            from pyrosm import OSM
        except ImportError:
            raise ImportError("pyrosm must be installed to use this function.")

        osm = OSM(osm_file)

        if tags:
            gdf = osm.get_data_by_custom_criteria(
                custom_filter=tags,
                filter_type="keep",
                keep_nodes=False,
                keep_ways=True,
                keep_relations=True
            )
        else:
            gdf = osm.get_buildings()  # default fallback

        self.data = gdf
        return gdf