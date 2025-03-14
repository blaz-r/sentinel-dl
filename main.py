import argparse
from datetime import datetime
from pathlib import Path

from sentinelhub import DataCollection, SHConfig, MosaickingOrder

from util.workflows import prepare_workflow, execute_flow
from util.region import validate_data_exists, prepare_chunks
from util.time import get_last_two_timestamps, get_last_month_span


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--date", required=True, type=str, help="Date of interest in format: d.m.Y."
    )
    parser.add_argument(
        "--geojson_path",
        type=str,
        default="data/svn_border.geojson",
        help="Path to geojson used. Default is data/svn_border.geojson",
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        default="./patches",
        help="Root dir of where patches will be saved.",
    )
    parser.add_argument(
        "--resolution",
        required=False,
        type=int,
        default=10,
        help="Sentinel sample resolution (Default is 10m)",
    )
    parser.add_argument(
        "--patch_size",
        required=False,
        type=int,
        default=512,
        help="Output patch pixel resolution (Default is 512px)",
    )
    parser.add_argument(
        "--maxcc",
        required=False,
        type=float,
        default=0.2,
        help="Max cloud coverage ratio (Default is 0.2)",
    )
    parser.add_argument(
        "--mosaicking_order",
        required=False,
        type=MosaickingOrder,
        default=MosaickingOrder.LEAST_CC,
        help="Mosaicking order to asemble single image (Default is LEAST_CC - least cloud coverage)",
    )
    parser.add_argument(
        "--num_workers",
        required=False,
        type=int,
        default=8,
        help="Number of processes (default is 8)",
    )

    return parser


def main() -> None:
    args = get_parser().parse_args()

    resolution = args.resolution
    start_date = args.date

    collection = DataCollection.SENTINEL2_L2A

    # load from config file
    config = SHConfig("sentinel-dl")

    geojson_path = Path(args.geojson_path)

    # prepare Slovenia map and chunk it into patches of resolution*patch_size m^2
    _, bbox_list = prepare_chunks(
        geojson_path=geojson_path, resolution=resolution, patch_size=args.patch_size
    )

    dir_name = start_date.replace(".", "-")
    # prepare workflow
    workflow, node_map = prepare_workflow(
        out_dir=f"{args.save_dir}/{dir_name}",
        config=config,
        resolution=resolution,
        data_collection=collection,
        maxcc=args.maxcc,
    )

    # get interval [date - month, date]
    time_of_interest = get_last_month_span(start_date)

    # check that data exist for given interval and cloud coverage, raise exception if not
    validate_data_exists(
        bbox_list,
        interval=time_of_interest,
        collection=collection,
        config=config,
        maxcc=args.maxcc,
    )

    # execute workflow downloading in parallel with given setup
    execute_flow(
        workflow=workflow,
        node_map=node_map,
        bbox_list=bbox_list,
        num_workers=args.num_workers,
        time_interval=time_of_interest,
    )


if __name__ == "__main__":
    main()
