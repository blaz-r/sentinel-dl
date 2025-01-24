from pathlib import Path
import geopandas as gpd
from sentinelhub import UtmZoneSplitter, BBox, DataCollection, SHConfig
import numpy as np
from sentinelhub.api.catalog import get_available_timestamps
from shapely import Polygon
from tqdm import tqdm


def prepare_shape(path: Path, buffer: int | None = None) -> gpd.geoseries.GeoSeries:
    """
    Load area of interest polygon geojson and add 512m buffer around it.

    Args:
        path (Path): path to shapefile (geojson)
        buffer (int | None): buffer around polygon geojson

    Returns:
        (GeoSeries) shape of polygon.
    """
    geo = gpd.read_file(path)
    # in case the crs in file is not projective
    geo = geo.to_crs(epsg="32633")
    if buffer is not None:
        # add specified buffer
        geo = geo.buffer(buffer)
    return geo


def prepare_chunks(
    geojson_path: Path, resolution=10, patch_size=512, fixed_meter_patch_size=None, shape_buffer: int | None = None
) -> tuple[gpd.GeoDataFrame, np.ndarray]:
    """
    Prepare bbox chunks of Slovenia for given resolution and patch_size.

    If resolution and patch_size are used the size of bbox side is calculated as resolution * patch_size, meaning that
    path resolution stays the same, but patch will contain different amount of meters covered.

    If you want to have a fixed content (in meters covered) use fixed_meter_patch_size and set it to meters.
    Be careful as with this option the resolution of image in pixels is then dependent on Sentinel sampling resolution
    which is later set in workflow.

    Examples:
        >>> prepare_slo_chunks(path, resolution=10, patch_size=512)   # covers 5120 x 5120 m^2 region

        >>> prepare_slo_chunks(path, resolution=20, patch_size=512)   # covers 10240 x 10240 m^2 region

        # resolution and patch_size ignored
        >>> prepare_slo_chunks(path, fixed_meter_patch_size=5120)     # covers 5120 x 5120 m^2 region

    Args:
        geojson_path (Path): path to geojson file used for region of interest
        resolution: resolution of single pixel in meters
        patch_size: final patch resolution in pixels
        fixed_meter_patch_size (Optional): if you want to specify fixed size of patch in meters
        shape_buffer (int | None): buffer size that is padded to shape we are processing. If none, use patch_size.

    Returns:
        dataframe with polygons and indices + list of bboxes.
    """
    if shape_buffer is None:
        shape_buffer = patch_size
    shape = prepare_shape(geojson_path, buffer=shape_buffer)

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
    bbox_splitter = UtmZoneSplitter([shape.geometry.values[0]], shape.crs, meter_size)

    bbox_list = np.array(bbox_splitter.get_bbox_list())
    info_list = np.array(bbox_splitter.get_info_list())

    geometry = [Polygon(bbox.get_polygon()) for bbox in bbox_list]
    idxs = [info["index"] for info in info_list]
    idxs_x = [info["index_x"] for info in info_list]
    idxs_y = [info["index_y"] for info in info_list]

    bbox_gdf = gpd.GeoDataFrame(
        {"index": idxs, "index_x": idxs_x, "index_y": idxs_y},
        crs=shape.crs,
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
        bboxes: list of regions of interest
        interval: time of interest
        collection: data type used
        config: sentinel hub config
        maxcc: maximum cloud coverage ratio

    Returns:
        None
    """
    nodata_ids = []

    print(
        f"Verifying that data exists for given interval {interval} and cloud coverage of {maxcc}."
    )
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
