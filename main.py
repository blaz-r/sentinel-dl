from sentinelhub import DataCollection, SHConfig

from util.workflows import prepare_dl_workflow, execute_flow
from util.region import prepare_slo_chunks
from util.time import get_last_two_timestamps


def main() -> None:
    resolution = 10
    patch_size = 512
    collection = DataCollection.SENTINEL2_L1C
    config = SHConfig("sentinel-dl")
    _, bbox_list = prepare_slo_chunks(resolution=resolution, patch_size=patch_size)
    workflow, node_map = prepare_dl_workflow(
        out_dir="./patches",
        config=config,
        resolution=resolution,
        data_collection=collection,
    )

    # TODO
    time_of_interest = ()

    execute_flow(
        workflow=workflow,
        node_map=node_map,
        bbox_list=bbox_list,
        num_workers=4,
        time_interval=time_of_interest,
    )
