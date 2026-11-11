#!/usr/bin/env python3

import argparse
import os

from config import DEFAULT_CONFIG_PATH


def parse_args(argv=None):
    """Parse command line arguments for the hand tracker."""
    parser = argparse.ArgumentParser(description="Run the hand tracker recognizer.")
    parser.add_argument(
        "-c",
        "--config",
        default=os.environ.get("HAND_TRACKER_CONFIG", str(DEFAULT_CONFIG_PATH)),
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Override the config and print extra debug diagnostics.",
    )
    return parser.parse_args(argv)
