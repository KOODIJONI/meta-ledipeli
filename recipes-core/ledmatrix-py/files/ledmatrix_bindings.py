
import ctypes

# --- Load Shared Library ---
_lib = ctypes.CDLL("/usr/lib/libledmatrix.so.1")

# --- Error Codes ---
OK = 0
ERROR_NULL_POINTER = -1
ERROR_OUT_OF_MEMORY = -2
ERROR_OUT_OF_BOUNDS = -3
ERROR_INVALID_COORDINATES = -4

# --- C Struct Definitions ---


class RgbColor(ctypes.Structure):
  _fields_ = [("r", ctypes.c_uint8), ("g", ctypes.c_uint8), ("b", ctypes.c_uint8)]


class MatrixConfig(ctypes.Structure):
  _fields_ = [
      ("tile_rows", ctypes.c_uint8),
      ("tile_cols", ctypes.c_uint8),
      ("grid_rows", ctypes.c_uint8),
      ("grid_cols", ctypes.c_uint8),
      ("brightness", ctypes.c_uint8),
      ("rotation", ctypes.c_uint8),
  ]


class Matrix(ctypes.Structure):
  _fields_ = [
      ("colors", ctypes.POINTER(RgbColor)),
      ("rows", ctypes.c_uint8),
      ("cols", ctypes.c_uint8),
      ("tile_rows", ctypes.c_uint8),
      ("tile_cols", ctypes.c_uint8),
      ("grid_rows", ctypes.c_uint8),
      ("grid_cols", ctypes.c_uint8),
      ("brightness", ctypes.c_uint8),
      ("rotation", ctypes.c_uint8),
  ]


class Buffer(ctypes.Structure):
  _fields_ = [
      ("data", ctypes.POINTER(ctypes.c_uint32)),
      ("size", ctypes.c_size_t),
      ("capacity", ctypes.c_size_t),
  ]


# --- Function Signatures ---

_lib.MatrixInit.argtypes = [ctypes.POINTER(Matrix), ctypes.POINTER(MatrixConfig)]
_lib.MatrixInit.restype = ctypes.c_int

_lib.MatrixInitWithJson.argtypes = [ctypes.POINTER(Matrix), ctypes.c_char_p]
_lib.MatrixInitWithJson.restype = ctypes.c_int

_lib.MatrixFree.argtypes = [ctypes.POINTER(Matrix)]
_lib.MatrixFree.restype = None

_lib.MatrixWriteColor.argtypes = [
    ctypes.POINTER(Matrix),
    ctypes.c_uint8,
    ctypes.c_uint8,
    ctypes.POINTER(RgbColor),
]
_lib.MatrixWriteColor.restype = ctypes.c_int

_lib.MatrixWriteRectFill.argtypes = [
    ctypes.POINTER(Matrix),
    ctypes.c_uint8,
    ctypes.c_uint8,
    ctypes.c_uint8,
    ctypes.c_uint8,
    RgbColor,
]
_lib.MatrixWriteRectFill.restype = ctypes.c_int

_lib.MatrixWriteLine.argtypes = [
    ctypes.POINTER(Matrix),
    ctypes.c_uint8,
    ctypes.c_uint8,
    ctypes.c_uint8,
    ctypes.c_uint8,
    RgbColor,
]
_lib.MatrixWriteLine.restype = ctypes.c_int

_lib.MatrixWriteAll.argtypes = [ctypes.POINTER(Matrix), RgbColor]
_lib.MatrixWriteAll.restype = ctypes.c_int

_lib.MatrixGetSize.argtypes = [
    ctypes.POINTER(Matrix),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
]
_lib.MatrixGetSize.restype = ctypes.c_int

_lib.BufferRequiredSamples.argtypes = [ctypes.POINTER(Matrix)]
_lib.BufferRequiredSamples.restype = ctypes.c_size_t

_lib.BufferInit.argtypes = [ctypes.POINTER(Buffer), ctypes.c_size_t]
_lib.BufferInit.restype = ctypes.c_int

_lib.BufferFree.argtypes = [ctypes.POINTER(Buffer)]
_lib.BufferFree.restype = None

_lib.MatrixToBuffer.argtypes = [ctypes.POINTER(Matrix), ctypes.POINTER(Buffer)]
_lib.MatrixToBuffer.restype = ctypes.c_int

_lib.BufferMatrixDriverOpen.argtypes = [ctypes.c_char_p]
_lib.BufferMatrixDriverOpen.restype = ctypes.c_int

_lib.BufferSendToKernel.argtypes = [ctypes.POINTER(Buffer)]
_lib.BufferSendToKernel.restype = ctypes.c_int

_lib.BufferMatrixDriverClose.argtypes = []
_lib.BufferMatrixDriverClose.restype = None