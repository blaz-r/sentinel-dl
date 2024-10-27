from sentinelhub import SHConfig
import argparse
import traceback


def get_parser() -> argparse.ArgumentParser:
    """
    Create CLI argument parser to get SentinelHub ID and Secret.

    Returns:
        (argparse.ArgumentParser) parser for id and secret
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", required=True, type=str, help="Client ID")
    parser.add_argument("--secret", required=True, type=str, help="Client Secret")

    return parser


def main() -> None:
    """
    Configure Client ID and Client Secret to config file used by sentinelhub library. This will be used

    """
    args = get_parser().parse_args()

    config = SHConfig()
    config.sh_client_id = args.id
    config.sh_client_secret = args.secret
    try:
        config.save("sentinel-dl")
        print("Configuration successfully saved to sentinel-dl profile.")
    except Exception:
        print(f"Failed to save sentinel-dl profile: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
