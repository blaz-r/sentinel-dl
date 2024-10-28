from pathlib import Path
import geopandas as gpd
from matplotlib import pyplot as plt
from sentinelhub import UtmZoneSplitter
import numpy as np
from shapely import Polygon


def prepare_slo_shape() -> gpd.geoseries.GeoSeries:
    """
    Load Slovenia border geojson and add 512m buffer around it.

    Returns:
        (GeoSeries) shape of Slovenia border.
    """
    slo = gpd.read_file(Path("data/svn_border.geojson"))
    # add 512m buffer around the border
    slo = slo.buffer(512)
    return slo


def prepare_slo_chunks(resolution=10, patch_size=512):
    # TODO check how resolution works exactly
    #assert patch_size % resolution == 0, "Patch size must be divisible by resolution."

    slo = prepare_slo_shape()

    # bboxes with 5120m sides, to get
    bbox_splitter = UtmZoneSplitter([slo.geometry.values[0]], slo.crs, 5120)

    bbox_list = np.array(bbox_splitter.get_bbox_list())
    info_list = np.array(bbox_splitter.get_info_list())

    geometry = [Polygon(bbox.get_polygon()) for bbox in bbox_list]
    idxs = [info["index"] for info in info_list]
    idxs_x = [info["index_x"] for info in info_list]
    idxs_y = [info["index_y"] for info in info_list]

    bbox_gdf = gpd.GeoDataFrame({"index": idxs, "index_x": idxs_x, "index_y": idxs_y}, crs=slo.crs,
                                geometry=geometry)

    return bbox_gdf

