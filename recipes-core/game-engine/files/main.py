
from __future__ import annotations

from config import (
    get_initial_game,
    load_config,
)
from games.test_game.test_game import MatrixGame
from games.tetris.tetris import Tetris
from parse_arg import parse_args
from game_manager import GameManager

SIMULATOR_STATE_TOPIC = "engine/simulator/config"
CAMERA_SIZE_TOPIC = "engine/camera/size"
AVAILABLE_GAMES_TOPIC = "engine/available"



# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":

    args = parse_args()

    manager = None

    try:
        config = load_config(args.config)

        if args.list_games:

            available = config.get(
                "startup",
                {},
            ).get(
                "available_games",
                ["tetris"],
            )

            print(
                "Available games:",
                ", ".join(available),
            )

        else:
            manager = GameManager(config=config)
            manager.run()

    except KeyboardInterrupt:
        print(
            "[MAIN] Keyboard interrupt received."
        )

    except Exception as exc:
        print(f"[ERROR] {exc}")
        raise

    finally:
        if manager is not None:
            manager.stop()
