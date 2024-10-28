from eolearn.core import (
    FeatureType,
    SaveTask,
    linearly_connect_tasks,
    EOWorkflow,
    EOExecutor,
)
from eolearn.io import SentinelHubInputTask
from sentinelhub import DataCollection, SHConfig

def prepare_dl_workflow(
    out_dir: str,
    config: SHConfig,
    data_collection: DataCollection = DataCollection.SENTINEL2_L1C,
    bands: list[str] = None,
    resolution: int = 10,
    maxcc: float = 0.8,
):
    # size?
    input_task = SentinelHubInputTask(
        data_collection=data_collection,
        bands=bands,
        bands_feature=(FeatureType.DATA, "data"),
        additional_data=[(FeatureType.MASK, "dataMask")],  # cloud mask
        maxcc=maxcc,
        resolution=resolution,
        config=config,  # important since we are using sentinel-dl, alternatively save ID and secret to default profile
    )

    save_task = SaveTask(out_dir)

    workflow_nodes = linearly_connect_tasks(input_task, save_task)
    workflow = EOWorkflow(workflow_nodes)

    node_map = {"input": workflow_nodes[0], "save": workflow_nodes[1]}

    return workflow, node_map


def execute_flow(
    workflow: EOWorkflow,
    node_map: dict,
    bbox_list: list,
    num_workers: int,
    time_interval: tuple,
):
    execution_args = []

    # TODO - naming convention?
    for idx, bbox in enumerate(bbox_list):
        execution_args.append(
            {
                node_map["input"]: {"bbox": bbox, "time_interval": time_interval},
                node_map["save"]: {"eopatch_folder": f"patch_{idx}"},
            }
        )
        if idx == 0:
            break

    executor = EOExecutor(workflow, execution_args, save_logs=True, logs_folder="./log")
    executor.run(workers=num_workers)

    executor.make_report()

    failed_ids = executor.get_failed_executions()
    if failed_ids:
        raise RuntimeError(
            f"Execution failed EOPatches with IDs:\n{failed_ids}\n"
            f"For more info check report at {executor.get_report_path()}"
        )
