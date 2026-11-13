# main.py
from config import get_fps, get_initial_game, load_config
from games.test_game.test_game import MatrixGame
from games.tetris.tetris import Tetris
from parse_arg import parse_args


def select_game(config):
    startup = config.get("startup", {})
    available_games = startup.get("available_games", ["tetris"])
    initial_game = get_initial_game(config)

    if initial_game in available_games and initial_game == "tetris":
        return Tetris(config=config)

    if initial_game in available_games and initial_game in {"test_game", "matrix_game"}:
        return MatrixGame(config=config)

    if "test_game" in available_games or "matrix_game" in available_games:
        return MatrixGame(config=config)

    raise ValueError(f"No supported game available in config: {available_games}")


if __name__ == "__main__":
    args = parse_args()

    try:
        config = load_config(args.config)

        if args.list_games:
            available = config.get("startup", {}).get("available_games", ["tetris"])
            print("Available games:", ", ".join(available))
        else:
            game = select_game(config)
            game.run(fps=get_fps(config))

    except Exception as e:
        print(f"[ERROR] {e}")