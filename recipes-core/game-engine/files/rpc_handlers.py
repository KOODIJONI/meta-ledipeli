# rpc_handlers.py
from __future__ import annotations


class GameRpcHandlers:
    def __init__(self, manager):
        self.manager = manager

    def register(self, mqtt_client) -> None:
        if mqtt_client is None:
            return

        handlers = {
            "game.change": self.change_game,
            "game.list": self.list_games,
            "game.status": self.status,
            "simulate_matrix": self.set_matrix_simulation,
            "simulate_input": self.set_input_simulation,
            "cycle_game": self.cycle_game,
            "matrix_brightness": self.set_matrix_brightness,
        }

        for method, handler in handlers.items():
            mqtt_client.register_rpc_handler(method, handler)

        print("[MAIN] JSON-RPC handlers registered.")


    @staticmethod
    def _coerce_enabled_flag(params) -> bool:
        if isinstance(params, dict):
            value = params.get("enabled", params.get("value", False))
        else:
            value = params

        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("true", "1", "yes", "on", "enabled"):
                return True
            if normalized in ("false", "0", "no", "off", "disabled", ""):
                return False

        raise ValueError(f"Invalid simulation enabled value: {value!r}")

    def change_game(self, params):
        game_name = params.get("game") if isinstance(params, dict) else params
        if not game_name:
            raise ValueError("Missing game name")

        accepted = self.manager.request_game_change(game_name)
        print(f"[RPC] Game change accepted: {accepted}")
        return {"game": accepted, "status": "accepted"}

    def list_games(self, params):
        return {"games": self.manager.get_available_games()}

    def status(self, params):
        return self.manager.get_status()

    def set_matrix_simulation(self, params):
        enabled = self._coerce_enabled_flag(params)
        return self.manager.set_simulation("matrix", enabled)

    def set_input_simulation(self, params):
        enabled = self._coerce_enabled_flag(params)
        return self.manager.set_simulation("input", enabled)

    def cycle_game(self, params=None):
        step = 1
        if isinstance(params, dict):
            if "step" in params and params["step"] is not None:
                step = -1 if int(params["step"]) < 0 else 1
            elif "direction" in params and params["direction"] is not None:
                direction = str(params["direction"]).strip().lower()
                if direction in ("prev", "previous", "back", "left", "-1"):
                    step = -1
                elif direction in ("next", "forward", "right", "+1", "1"):
                    step = 1
                else:
                    raise ValueError(f"Invalid cycle direction: {direction!r}")

        target = self.manager.cycle_game(step)
        print(f"[RPC] Cycle game requested (step={step}): target={target}")
        return {
            "game": target,
            "step": step,
            "status": "accepted" if target is not None else "unchanged",
        }
    @staticmethod
    def _coerce_brightness(params) -> float:
        if isinstance(params, dict):
            raw = params.get("brightness", params.get("value"))
        else:
            raw = params

        if raw is None or isinstance(raw, bool):
            raise ValueError(f"Invalid brightness value: {raw!r}")

        val = float(raw)
        # Allow 0..100 percentage input if someone passes e.g. 50 -> 0.5
        if 1.0 < val <= 100.0:
            val = val / 100.0

        if not (0.0 <= val <= 1.0):
            raise ValueError(f"Brightness out of range (0.0..1.0): {raw!r}")

        return val

    def set_matrix_brightness(self, params):
        brightness = self._coerce_brightness(params)
        applied = self.manager.set_matrix_brightness(brightness)
        print(f"[RPC] Matrix brightness set to: {applied}")
        return {"brightness": applied, "status": "ok"}