import json
import re


def parse_size_value(raw):
    if raw is None:
        return {"width": 0, "height": 0}

    if isinstance(raw, dict):
        if "width" in raw or "height" in raw:
            return {
                "width": int(raw.get("width", 0)),
                "height": int(raw.get("height", 0)),
            }
        if len(raw) >= 2:
            values = list(raw.values())
            return {
                "width": int(values[0]),
                "height": int(values[1]),
            }

    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        return {
            "width": int(raw[0]),
            "height": int(raw[1]),
        }

    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                if "width" in parsed or "height" in parsed:
                    return {
                        "width": int(parsed.get("width", 0)),
                        "height": int(parsed.get("height", 0)),
                    }
                if len(parsed) >= 2:
                    values = list(parsed.values())
                    return {
                        "width": int(values[0]),
                        "height": int(values[1]),
                    }
            if isinstance(parsed, (list, tuple)) and len(parsed) >= 2:
                return {
                    "width": int(parsed[0]),
                    "height": int(parsed[1]),
                }
        except json.JSONDecodeError:
            pass

        numbers = [int(value) for value in re.findall(r"-?\d+", raw)]
        if len(numbers) >= 2:
            return {"width": numbers[0], "height": numbers[1]}

    return {"width": 0, "height": 0}


def parse_matrix_data(raw, width=None, height=None):
    if raw is None:
        return []

    if isinstance(raw, (bytes, bytearray)):
        values = list(raw)
        if len(values) % 3 != 0:
            return []

        pixels = []
        for index in range(0, len(values), 3):
            g, r, b = values[index:index + 3]
            pixels.append({"r": r, "g": g, "b": b})

        if width and height:
            rows = []
            for row_index in range(height):
                row = []
                for col_index in range(width):
                    pixel_index = row_index * width + col_index
                    row.append(pixels[pixel_index] if pixel_index < len(pixels) else {"r": 0, "g": 0, "b": 0})
                rows.append(row)
            return rows
        return [pixels]

    if isinstance(raw, list):
        if raw and all(isinstance(row, list) for row in raw):
            return raw
        return [raw]

    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                if parsed and all(isinstance(row, list) for row in parsed):
                    return parsed
                return [parsed]
            if isinstance(parsed, dict):
                for key in ("data", "matrix", "rows"):
                    if isinstance(parsed.get(key), list):
                        return parsed[key]
        except json.JSONDecodeError:
            pass

        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if lines:
            matrix = []
            for line in lines:
                cells = [int(part) for part in re.split(r"[\s,]+", line) if part.strip()]
                if cells:
                    matrix.append(cells)
            if matrix:
                return matrix

        numbers = [int(value) for value in re.findall(r"-?\d+", raw)]
        if len(numbers) >= 3 and len(numbers) % 3 == 0:
            byte_values = [value & 0xFF for value in numbers]
            return parse_matrix_data(bytes(byte_values), width, height)

        return []

    return []


def normalize_mouse_position(pointer_x, pointer_y, rect_width, rect_height, camera_width, camera_height):
    if rect_width <= 0:
        norm_x = 0
    else:
        norm_x = max(0, min(pointer_x / rect_width, 1))

    if rect_height <= 0:
        norm_y = 0
    else:
        norm_y = max(0, min(pointer_y / rect_height, 1))

    translated_x = int(round(norm_x * camera_width))
    translated_y = int(round(norm_y * camera_height))
    return translated_x, translated_y


def pointer_gesture(event_type):
    return {
        "pointerdown": "down",
        "pointermove": "move",
        "pointerup": "up",
    }.get(event_type, "move")


def run_tests():
    assert parse_size_value('{"width": 8, "height": 8}') == {"width": 8, "height": 8}
    assert parse_size_value('width=8 height=12') == {"width": 8, "height": 12}
    assert parse_size_value([8, 12]) == {"width": 8, "height": 12}

    assert parse_matrix_data('[ [1,0],[0,1] ]') == [[1, 0], [0, 1]]
    assert parse_matrix_data('1,0\n0,1') == [[1, 0], [0, 1]]

    blob = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255])
    parsed_blob = parse_matrix_data(blob, width=1, height=3)
    assert parsed_blob[0][0] == {"r": 0, "g": 255, "b": 0}
    assert parsed_blob[1][0] == {"r": 255, "g": 0, "b": 0}

    assert normalize_mouse_position(100, 80, 200, 160, 640, 480) == (320, 240)
    assert normalize_mouse_position(200, 160, 200, 160, 640, 480) == (640, 480)
    assert normalize_mouse_position(0, 0, 200, 160, 640, 480) == (0, 0)

    assert pointer_gesture("pointerdown") == "down"
    assert pointer_gesture("pointermove") == "move"
    assert pointer_gesture("pointerup") == "up"
    assert pointer_gesture("unknown") == "move"

    print("All simulator tests passed.")


if __name__ == "__main__":
    run_tests()
