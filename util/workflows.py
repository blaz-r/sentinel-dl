import numpy as np
from eolearn.core import (
    FeatureType,
    SaveTask,
    linearly_connect_tasks,
    EOWorkflow,
    EOExecutor,
)
from eolearn.io import SentinelHubInputTask
from sentinelhub import DataCollection, SHConfig, BBox, MosaickingOrder


def prepare_workflow(
    out_dir: str,
    config: SHConfig,
    data_collection: DataCollection = DataCollection.SENTINEL2_L1C,
    bands: list[str] = None,
    resolution: int = 10,
    maxcc: float = 0.8,
    single_scene: bool = True,
    mosaicking_order: MosaickingOrder = MosaickingOrder.LEAST_CC,
):
    """
    Prepare Eo-learn workflow used to download the patches.

    Args:
        out_dir: path to root dir for patch files.
        config: sentinel hub config.
        data_collection: type of data that will be downloaded.
        bands: bands to download. If set to None, all bands will be downloaded.
        resolution: resolution in meters.
        maxcc: max cloud cover ratio
        single_scene: mosaic the image into single image, based on least cloud coverage.
        mosaicking_order: order of mosaicking for single_scene image, refer to MosaickingOrder and docs for more info.

    Returns:
        workflow and dictionary containing map to input and saving node, later used to set arguments
    """
    input_task = SentinelHubInputTask(
        data_collection=data_collection,
        bands=bands,
        bands_feature=(FeatureType.DATA, "data"),
        additional_data=[(FeatureType.MASK, "dataMask")],  # cloud mask
        maxcc=maxcc,
        single_scene=single_scene,
        mosaicking_order=mosaicking_order,
        resolution=resolution,  # fix this here, since based on bbox sizes the output in pixels might not match directly.
        config=config,  # important since we are using sentinel-dl, alternatively save ID and secret to default profile
    )

    save_task = SaveTask(out_dir)

    workflow_nodes = linearly_connect_tasks(input_task, save_task)
    workflow = EOWorkflow(workflow_nodes)

    node_map = {"input": workflow_nodes[0], "save": workflow_nodes[1]}

    return workflow, node_map


def simple_idx2name(idx: int, bbox: BBox, time: tuple) -> str:
    """
    Simple formatter for patch file names to set name to patch_idx.

    Args:
        idx: index used in name
        bbox: ignored
        time: ignored

    Returns:
        string with file name
    """
    return f"patch_{idx}"


def execute_flow(
    workflow: EOWorkflow,
    bbox_list: np.ndarray,
    time_interval: list,
    node_map: dict,
    file_name_formatter: callable = simple_idx2name,
    num_workers: int = 4,
) -> None:
    """
    Execute download workflow for given bboxes.

    Args:
        workflow: download workflow
        bbox_list: list of bboxes to be downloaded
        time_interval: time interval of interest
        node_map: used to set arguments for workflow nodes
        file_name_formatter: function used to generate patch file name
        num_workers: number of processes used

    Returns:
        None
    """
    execution_args = []

    for idx, bbox in enumerate(bbox_list):
        execution_args.append(
            {
                node_map["input"]: {"bbox": bbox, "time_interval": time_interval},
                node_map["save"]: {
                    "eopatch_folder": file_name_formatter(idx, bbox, time_interval)
                },
            }
        )

    print("Starting workflow execution.")

    executor = EOExecutor(workflow, execution_args, save_logs=True, logs_folder="./log")
    executor.run(workers=num_workers)

    executor.make_report()

    failed_ids = executor.get_failed_executions()
    if failed_ids:
        raise RuntimeError(
            f"Execution failed EOPatches with IDs:\n{failed_ids}\n"
            f"For more info check report at {executor.get_report_path()}"
        )

    print("Saving successful for all patches.")
