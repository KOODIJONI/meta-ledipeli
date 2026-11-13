import argparse

from config import DEFAULT_CONFIG_PATH


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Game engine launcher")
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the JSON configuration file",
    )
    parser.add_argument(
        "--list-games",
        action="store_true",
        help="Display the configured available games and exit",
    )
    return parser.parse_args(argv)
