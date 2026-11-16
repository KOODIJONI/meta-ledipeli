import ctypes
from ledmatrix_bindings import (
    _lib,
    Buffer,
    RgbColor,
    OK,
    ERROR_NULL_POINTER,
)


class LEDMatrix:

  def __init__(self, json_path="/etc/ledmatrix-driver/matrix_config.json", device_path=b"/dev/ledmatrix"):
    # Set everything close() touches first, so a failure part-way through
    # __init__ still leaves an object that can be cleaned up safely.
    self._matrix = None
    self._buffer = Buffer()
    self._driver_open = False

    # The C library allocates the Matrix. A falsy json_path passes NULL, which
    # MatrixCreate must treat as "use the default configuration".
    path = json_path.encode("utf-8") if json_path else None
    handle = _lib.MatrixCreate(path)
    if not handle:
      raise RuntimeError("Failed to initialize LED matrix: MatrixCreate returned NULL")
    self._matrix = handle

    rows = ctypes.c_int()
    cols = ctypes.c_int()
    ret = _lib.MatrixGetSize(self._matrix, ctypes.byref(rows), ctypes.byref(cols))
    if ret != OK:
      self.close()
      raise RuntimeError(f"Failed to get matrix size: error code {ret}")
    self.rows = rows.value
    self.cols = cols.value

    samples = _lib.BufferRequiredSamples(self._matrix)
    ret = _lib.BufferInit(ctypes.byref(self._buffer), samples)
    if ret != OK:
      self.close()
      raise RuntimeError(f"Failed to allocate buffer: error code {ret}")

    ret = _lib.BufferMatrixDriverOpen(device_path)
    if ret == OK:
      self._driver_open = True
    else:
      print("Warning: Could not open kernel driver device. Display flush disabled.")

  def set_pixel(self, x, y, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteColor(
        self._matrix, ctypes.c_uint8(x), ctypes.c_uint8(y), ctypes.byref(color)
    )

  def fill_rect(self, x1, y1, x2, y2, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteRectFill(
        self._matrix,
        ctypes.c_uint8(x1),
        ctypes.c_uint8(y1),
        ctypes.c_uint8(x2),
        ctypes.c_uint8(y2),
        color,
    )

  def draw_line(self, x1, y1, x2, y2, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteLine(
        self._matrix,
        ctypes.c_uint8(x1),
        ctypes.c_uint8(y1),
        ctypes.c_uint8(x2),
        ctypes.c_uint8(y2),
        color,
    )

  def fill(self, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteAll(self._matrix, color)

  def get_raw_frame(self):
    rows = ctypes.c_int()
    cols = ctypes.c_int()
    ret = _lib.MatrixGetSize(self._matrix, ctypes.byref(rows), ctypes.byref(cols))
    if ret != OK:
      raise RuntimeError(f"Failed to get logical matrix size: error code {ret}")

    logical_size = rows.value * cols.value
    logical_buffer = (RgbColor * logical_size)()
    ret = _lib.MatrixUndoTransformation(self._matrix, logical_buffer)
    if ret != OK:
      raise RuntimeError(f"Failed to undo matrix transformation: error code {ret}")

    blob = bytearray()
    for pixel in logical_buffer:
      blob.extend((pixel.g, pixel.r, pixel.b))
    return bytes(blob)

  def flush(self):
    """Encodes matrix pixels into SPI waveform buffer and writes to kernel driver"""
    ret = _lib.MatrixToBuffer(self._matrix, ctypes.byref(self._buffer))
    if ret != OK:
      return ret

    if self._driver_open:
      return _lib.BufferSendToKernel(ctypes.byref(self._buffer))
    return ERROR_NULL_POINTER

  def close(self):
    """Release the driver, buffer and matrix. Safe to call more than once."""
    if self._driver_open:
      _lib.BufferMatrixDriverClose()
      self._driver_open = False
    _lib.BufferFree(ctypes.byref(self._buffer))  # sets data to NULL, so repeat calls are harmless
    if self._matrix:
      _lib.MatrixDestroy(self._matrix)
      self._matrix = None

  def __del__(self):
    try:
      self.close()
    except Exception:
      pass