import ctypes
from ledmatrix_bindings import (
    _lib,
    Matrix,
    Buffer,
    RgbColor,
    OK,
    ERROR_NULL_POINTER,
)


class LEDMatrix:

  def __init__(self, json_path="/etc/ledmatrix-driver/matrix_config.json", device_path=b"/dev/ledmatrix"):
    self._matrix = Matrix()
    self._buffer = Buffer()
    self._driver_open = False

    if json_path:
      ret = _lib.MatrixInitWithJson(
          ctypes.byref(self._matrix), json_path.encode("utf-8")
      )
    else:
      ret = _lib.MatrixInit(ctypes.byref(self._matrix), None)

    if ret != OK:
      raise RuntimeError(f"Failed to initialize LED matrix: error code {ret}")

    rows = ctypes.c_int()
    cols = ctypes.c_int()
    _lib.MatrixGetSize(ctypes.byref(self._matrix), ctypes.byref(rows), ctypes.byref(cols))
    self.rows = rows.value
    self.cols = cols.value

    samples = _lib.BufferRequiredSamples(ctypes.byref(self._matrix))
    ret = _lib.BufferInit(ctypes.byref(self._buffer), samples)
    if ret != OK:
      _lib.MatrixFree(ctypes.byref(self._matrix))
      raise RuntimeError(f"Failed to allocate buffer: error code {ret}")

    ret = _lib.BufferMatrixDriverOpen(device_path)
    if ret == OK:
      self._driver_open = True
    else:
      print("Warning: Could not open kernel driver device. Display flush disabled.")

  def set_pixel(self, x, y, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteColor(
        ctypes.byref(self._matrix), ctypes.c_uint8(x), ctypes.c_uint8(y), ctypes.byref(color)
    )

  def fill_rect(self, x1, y1, x2, y2, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteRectFill(
        ctypes.byref(self._matrix),
        ctypes.c_uint8(x1),
        ctypes.c_uint8(y1),
        ctypes.c_uint8(x2),
        ctypes.c_uint8(y2),
        color,
    )

  def draw_line(self, x1, y1, x2, y2, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteLine(
        ctypes.byref(self._matrix),
        ctypes.c_uint8(x1),
        ctypes.c_uint8(y1),
        ctypes.c_uint8(x2),
        ctypes.c_uint8(y2),
        color,
    )

  def fill(self, r, g, b):
    color = RgbColor(r, g, b)
    return _lib.MatrixWriteAll(ctypes.byref(self._matrix), color)

  def flush(self):
    """Encodes matrix pixels into SPI waveform buffer and writes to kernel driver"""
    ret = _lib.MatrixToBuffer(ctypes.byref(self._matrix), ctypes.byref(self._buffer))
    if ret != OK:
      return ret

    if self._driver_open:
      return _lib.BufferSendToKernel(ctypes.byref(self._buffer))
    return ERROR_NULL_POINTER

  def __del__(self):
    if self._driver_open:
      _lib.BufferMatrixDriverClose()
    _lib.BufferFree(ctypes.byref(self._buffer))
    _lib.MatrixFree(ctypes.byref(self._matrix))