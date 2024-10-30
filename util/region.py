from pathlib import Path
import geopandas as gpd
from sentinelhub import UtmZoneSplitter, BBox, DataCollection, SHConfig
import numpy as np
from sentinelhub.api.catalog import get_available_timestamps
from shapely import Polygon
from tqdm import tqdm


def prepare_slo_shape(patch_size=512) -> gpd.geoseries.GeoSeries:
    """
    Load Slovenia border geojson and add 512m buffer around it.

    Returns:
        (GeoSeries) shape of Slovenia border.
    """
    slo = gpd.read_file(Path("data/svn_border.geojson"))
    # add 512m buffer around the border
    slo = slo.buffer(patch_size)
    return slo


def prepare_slo_chunks(
    resolution=10, patch_size=512, fixed_meter_patch_size=None
) -> tuple[gpd.GeoDataFrame, np.ndarray]:
    """
    Prepare bbox chunks of Slovenia for given resolution and patch_size.

    If resolution and patch_size are used the size of bbox side is calculated as resolution * patch_size, meaning that
    path resolution stays the same, but patch will contain different amount of meters covered.

    If you want to have a fixed content (in meters covered) use fixed_meter_patch_size and set it to meters.
    Be careful as with this option the resolution of image in pixels is then dependent on Sentinel sampling resolution
    which is later set in workflow.

    Examples:
        >>> prepare_slo_chunks(resolution=10, patch_size=512)   # covers 5120 x 5120 m^2 region

        >>> prepare_slo_chunks(resolution=20, patch_size=512)   # covers 10240 x 10240 m^2 region

        # resolution and patch_size ignored
        >>> prepare_slo_chunks(fixed_meter_patch_size=5120)     # covers 5120 x 5120 m^2 region

    Args:
        resolution: resolution of single pixel in meters
        patch_size: final patch resolution in pixels
        fixed_meter_patch_size (Optional): if you want to specify fixed size of patch in meters

    Returns:
        dataframe with polygons and indices + list of bboxes.
    """
    slo = prepare_slo_shape()

    if fixed_meter_patch_size is None:
        meter_size = patch_size * resolution
        print(f"Setting chunk sizes to {meter_size}x{meter_size} m^2.")
    else:
        print(
            f"Fixing bbox chunk size to {fixed_meter_patch_size} m, resolution and patch_size are ignored.",
            "Warning! This option might result in a different size in pixels than expected.",
        )
        meter_size = fixed_meter_patch_size

    # bboxes with sides in meter sizes, which will then result in patch resolution of patch_size in pixels
    bbox_splitter = UtmZoneSplitter([slo.geometry.values[0]], slo.crs, meter_size)

    bbox_list = np.array(bbox_splitter.get_bbox_list())
    info_list = np.array(bbox_splitter.get_info_list())

    geometry = [Polygon(bbox.get_polygon()) for bbox in bbox_list]
    idxs = [info["index"] for info in info_list]
    idxs_x = [info["index_x"] for info in info_list]
    idxs_y = [info["index_y"] for info in info_list]

    bbox_gdf = gpd.GeoDataFrame(
        {"index": idxs, "index_x": idxs_x, "index_y": idxs_y},
        crs=slo.crs,
        geometry=geometry,
    )

    return bbox_gdf, bbox_list


def validate_data_exists(
    bboxes: np.ndarray,
    interval: tuple,
    collection: DataCollection,
    config: SHConfig,
    maxcc: float,
):
    """
    Validate that data exists for given bbox, collection, interval and max cloud coverage.
    Raise exception if any patches don't have cloud coverage.

    Useful in case of high cloud coverage.

    Args:
        bbox: region of interest
        interval: time of interest
        collection: data type used
        config: sentinel hub config
        maxcc: maximum cloud coverage ratio

    Returns:
        None
    """
    nodata_ids = []

    print("Verifying that data exists for given interval and cloud coverage.")
    for i, bbox in tqdm(enumerate(bboxes), desc="Verifying", total=len(bboxes)):
        ts = get_available_timestamps(
            bbox=bbox,
            time_interval=interval,
            data_collection=collection,
            config=config,
            maxcc=maxcc,
        )
        if not ts:
            nodata_ids.append(i)

    if nodata_ids:
        msg = f"Data with maxcc of {maxcc} not available for IDs: {nodata_ids}."
        raise RuntimeError(msg)
