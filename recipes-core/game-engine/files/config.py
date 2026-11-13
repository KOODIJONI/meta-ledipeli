from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "game_engine.json"
DEFAULT_MATRIX_CONFIG_PATH = Path("/etc/ledmatrix-driver/matrix_config.json")


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the JSON configuration for the game engine."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def get_config_value(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely read nested values from a config dictionary."""
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def get_matrix_config_path(config: dict[str, Any]) -> str:
    path = get_config_value(config, "engine", "matrix_config_path", default=str(DEFAULT_MATRIX_CONFIG_PATH))
    return str(path) if path else str(DEFAULT_MATRIX_CONFIG_PATH)


def get_matrix_size(config: dict[str, Any]) -> tuple[int, int]:
    matrix_config_path = Path(get_matrix_config_path(config))

    try:
        with matrix_config_path.open("r", encoding="utf-8") as fh:
            matrix_config = json.load(fh)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        matrix_config = None

    if isinstance(matrix_config, dict):
        try:
            tile_rows = int(matrix_config.get("tile_rows", 0))
            tile_cols = int(matrix_config.get("tile_cols", 0))
            grid_rows = int(matrix_config.get("grid_rows", 0))
            grid_cols = int(matrix_config.get("grid_cols", 0))
        except (TypeError, ValueError):
            tile_rows = tile_cols = grid_rows = grid_cols = 0

        if tile_rows > 0 and tile_cols > 0 and grid_rows > 0 and grid_cols > 0:
            return int(grid_rows * tile_rows), int(grid_cols * tile_cols)

    rows = get_config_value(config, "engine", "matrix_rows", default=8)
    cols = get_config_value(config, "engine", "matrix_cols", default=8)
    return int(rows), int(cols)


def get_window_size(config: dict[str, Any]) -> tuple[int, int]:
    width = get_config_value(config, "engine", "width", default=640)
    height = get_config_value(config, "engine", "height", default=480)
    return int(width), int(height)


def get_initial_game(config: dict[str, Any]) -> str:
    startup = config.get("startup", {})
    return str(startup.get("initial_game", "tetris")).lower()


def get_fps(config: dict[str, Any]) -> int:
    return int(get_config_value(config, "engine", "fps", default=60))


def get_hand_tracker_socket(config: dict[str, Any]) -> str:
    return str(get_config_value(config, "engine", "hand_tracker_socket", default="/tmp/hand_tracker.sock"))
