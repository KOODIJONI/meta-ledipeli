import { useEffect, useMemo, useRef, useState } from 'react'
import { rpcClient } from './mqttRpc.js'

const MATRIX_SIZE_TOPIC = 'engine/matrix/size'
const CAMERA_SIZE_TOPIC = 'engine/camera/size'
const MATRIX_DATA_TOPIC = 'engine/matrix/data'
const MOUSE_EVENT_TOPIC = 'engine/mouse'
const SIMULATOR_STATE_TOPIC = 'engine/simulator/config'

function parseSizeValue(raw) {
  if (!raw) return { width: 0, height: 0 }

  let text = raw
  if (ArrayBuffer.isView(raw)) {
    text = new TextDecoder().decode(raw)
  } else if (raw instanceof ArrayBuffer) {
    text = new TextDecoder().decode(new Uint8Array(raw))
  } else if (typeof raw !== 'string') {
    try {
      text = String(raw)
    } catch {
      text = ''
    }
  }

  try {
    const parsed = JSON.parse(text)
    if (parsed && typeof parsed === 'object') {
      if ('width' in parsed || 'height' in parsed) {
        return {
          width: Number(parsed.width ?? 0),
          height: Number(parsed.height ?? 0),
        }
      }

      if (Array.isArray(parsed) && parsed.length >= 2) {
        return {
          width: Number(parsed[0] ?? 0),
          height: Number(parsed[1] ?? 0),
        }
      }
    }
  } catch {
    // fall through to text parsing below
  }

  const numbers = (String(text).match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number)
  if (numbers.length >= 2) {
    return {
      width: numbers[0],
      height: numbers[1],
    }
  }

  return { width: 0, height: 0 }
}

function buildRgbMatrixFromBytes(bytes, width = 0, height = 0) {
  if (!bytes || bytes.length === 0) return []

  const pixelBytes = Array.from(bytes).map((value) => Number(value) & 0xff)
  if (pixelBytes.length % 3 !== 0) return []

  const pixels = []
  for (let index = 0; index < pixelBytes.length; index += 3) {
    const r = pixelBytes[index] ?? 0
    const g = pixelBytes[index + 1] ?? 0
    const b = pixelBytes[index + 2] ?? 0
    pixels.push({ r, g, b })
  }

  if (width > 0 && height > 0) {
    const rows = []
    const totalPixels = width * height
    for (let row = 0; row < height; row += 1) {
      const rowPixels = []
      for (let col = 0; col < width; col += 1) {
        const pixelIndex = row * width + col
        rowPixels.push(pixels[pixelIndex] ?? { r: 0, g: 0, b: 0 })
      }
      rows.push(rowPixels)
    }
    return rows.slice(0, totalPixels ? rows.length : 0)
  }

  return [pixels]
}

function normalizeArrayMatrix(data) {
  if (!Array.isArray(data)) return []

  if (data.length > 0 && Array.isArray(data[0])) {
    return data.map((row) =>
      row.map((cell) => {
        if (Array.isArray(cell) && cell.length >= 3) {
          return { r: Number(cell[1] ?? 0), g: Number(cell[0] ?? 0), b: Number(cell[2] ?? 0) }
        }
        const value = Number(cell ?? 0)
        return { r: value, g: value, b: value }
      }),
    )
  }

  const flatValues = data.map((value) => Number(value) & 0xff)
  if (flatValues.length % 3 !== 0) {
    return []
  }

  const pixels = []
  for (let index = 0; index < flatValues.length; index += 3) {
    const g = flatValues[index] ?? 0
    const r = flatValues[index + 1] ?? 0
    const b = flatValues[index + 2] ?? 0
    pixels.push({ r, g, b })
  }

  return [pixels]
}

function parseMatrixData(raw, requestedWidth = 0, requestedHeight = 0) {
  if (raw == null) return []

  if (raw instanceof ArrayBuffer) {
    return buildRgbMatrixFromBytes(new Uint8Array(raw), requestedWidth, requestedHeight)
  }

  if (ArrayBuffer.isView(raw)) {
    return buildRgbMatrixFromBytes(new Uint8Array(raw.buffer, raw.byteOffset, raw.byteLength), requestedWidth, requestedHeight)
  }

  if (Array.isArray(raw)) {
    return normalizeArrayMatrix(raw)
  }

  if (typeof raw === 'string') {
    const trimmed = raw.trim()
    if (!trimmed) return []

    try {
      const parsed = JSON.parse(trimmed)
      if (Array.isArray(parsed)) {
        return normalizeArrayMatrix(parsed)
      }

      if (parsed && typeof parsed === 'object') {
        if (Array.isArray(parsed.data)) return normalizeArrayMatrix(parsed.data)
        if (Array.isArray(parsed.matrix)) return normalizeArrayMatrix(parsed.matrix)
        if (Array.isArray(parsed.rows)) return normalizeArrayMatrix(parsed.rows)
      }
    } catch {
      // fall through to byte parsing below
    }

    const lines = trimmed.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
    if (lines.length > 0) {
      const rows = lines.map((line) =>
        line.split(/[\s,]+/).map((cell) => {
          const value = Number(cell.trim() || 0)
          return { r: value, g: value, b: value }
        }),
      )
      if (rows.length > 0 && rows.every((row) => row.length > 0)) {
        return rows
      }
    }

    const numbers = (trimmed.match(/-?\d+/g) ?? []).map((value) => Number(value) & 0xff)
    if (numbers.length >= 3 && numbers.length % 3 === 0) {
      return buildRgbMatrixFromBytes(Uint8Array.from(numbers), requestedWidth, requestedHeight)
    }

    return []
  }

  return []
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function GameSimulator() {
  const [matrixSize, setMatrixSize] = useState({ width: 0, height: 0 })
  const [cameraSize, setCameraSize] = useState({ width: 0, height: 0 })
  const [matrixData, setMatrixData] = useState([])
  const [cycling, setCycling] = useState(false)
  const [pausing, setPausing] = useState(false)

  const [simulateMatrix, setSimulateMatrix] = useState(false)
  const [simulateInput, setSimulateInput] = useState(false)
  const [selectedGesture, setSelectedGesture] = useState('pointing')
  const matrixSizeRef = useRef({ width: 0, height: 0 })
  const lastPointerRef = useRef({ x: 0.5, y: 0.5 }) // normalized 0..1, defaults to center
  const cameraSizeRef = useRef({ width: 0, height: 0 })

  useEffect(() => {
    matrixSizeRef.current = matrixSize
  }, [matrixSize])

  useEffect(() => {
  cameraSizeRef.current = cameraSize
}, [cameraSize])

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.repeat) return

      const key = Number(event.key)
      if (!Number.isInteger(key) || key < 1) return

      const gestureOptions = [
        'unknown',
        'open',
        'closed',
        'pointing',
        'victory',
        'thumbs_up',
        'thumbs_down',
      ]

      const gesture = gestureOptions[key - 1]
      if (gesture) {
        event.preventDefault()
        sendGesture(gesture)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    const unsubscribeMatrixSize = rpcClient.subscribe(MATRIX_SIZE_TOPIC, (payload) => {
      const nextSize = parseSizeValue(payload)
      setMatrixSize(nextSize)
      matrixSizeRef.current = nextSize
    })

    const unsubscribeCameraSize = rpcClient.subscribe(CAMERA_SIZE_TOPIC, (payload) => {
      setCameraSize(parseSizeValue(payload))
    })

    const unsubscribeMatrixData = rpcClient.subscribe(MATRIX_DATA_TOPIC, (payload) => {
      setMatrixData(parseMatrixData(payload, matrixSizeRef.current.width, matrixSizeRef.current.height))
    })

    const unsubscribeSimulatorState = rpcClient.subscribe(SIMULATOR_STATE_TOPIC, (payload) => {
      try {
        const nextState =
          typeof payload === 'string'
            ? JSON.parse(payload)
            : ArrayBuffer.isView(payload) || payload instanceof ArrayBuffer
              ? JSON.parse(new TextDecoder().decode(payload))
              : payload
        const state = nextState && typeof nextState === 'object' ? nextState : {}

        if (state.camera && state.camera.width && state.camera.height) {
          setCameraSize({
            width: Number(state.camera.width),
            height: Number(state.camera.height),
          })
        }
        if (typeof state.simulateMatrix === 'boolean') {
          setSimulateMatrix(state.simulateMatrix)
        }
        if (typeof state.simulateInput === 'boolean') {
          setSimulateInput(state.simulateInput)
        }
        if (state.matrix && (state.matrix.width || state.matrix.height)) {
          const nextSize = {
            width: Number(state.matrix.width ?? matrixSizeRef.current.width ?? 0),
            height: Number(state.matrix.height ?? matrixSizeRef.current.height ?? 0),
          }
          setMatrixSize(nextSize)
          matrixSizeRef.current = nextSize
        }
      } catch (error) {
        console.warn('simulator config parse failed', error)
      }
    })

    return () => {
      unsubscribeMatrixSize()
      unsubscribeCameraSize()
      unsubscribeMatrixData()
      unsubscribeSimulatorState()
    }
  }, [])

  const gridStyle = useMemo(() => {
    if (matrixSize.width <= 0 || matrixSize.height <= 0) {
      return {
        gridTemplateColumns: 'repeat(1, minmax(0, 1fr))',
      }
    }

    return {
      gridTemplateColumns: `repeat(${matrixSize.width}, minmax(0, 1fr))`,
    }
  }, [matrixSize])

  const handlePointerEvent = async (event) => {
    if (!cameraSize.width || !cameraSize.height || !matrixSize.width || !matrixSize.height) {
      return
    }

    const rect = event.currentTarget.getBoundingClientRect()
    if (!rect.width || !rect.height) {
      return
    }

    const xInRect = clamp(event.clientX - rect.left, 0, rect.width)
    const yInRect = clamp(event.clientY - rect.top, 0, rect.height)

    const normalizedX = xInRect / rect.width
    const normalizedY = yInRect / rect.height

    lastPointerRef.current = { x: normalizedX, y: normalizedY }

    const cameraX = Math.round(normalizedX * cameraSize.width)
    const cameraY = Math.round(normalizedY * cameraSize.height)

    const gesture = selectedGesture || 'pointing'

    try {
      await rpcClient.publish(MOUSE_EVENT_TOPIC, {
        x: cameraX,
        y: cameraY,
        gesture,
      })
    } catch (error) {
      console.error('Failed to publish mouse event:', error)
    }
  }

  const visibleRows = matrixData.length
  const visibleCols = matrixData[0]?.length ?? 0


  const cycleGame = async (step) => {
      setCycling(true)
      try {
        await rpcClient.call('cycle_game', { step })
      } catch (error) {
        console.warn(`Cycle game failed: ${error.message}`)
      } finally {
        setCycling(false)
      }
    }
  const pauseGame = async () => {
      setPausing(true)
      try {
        await rpcClient.call('pause_game')
      } catch (error) {
        console.warn(`Pause game failed: ${error.message}`)
      } finally {
        setPausing(false)
      }
  }
  const toggleSimulation = async (type, checked) => {
    const methodNames = {
      matrix: ['simulateMatrix', 'simulate_matrix'],
      input: ['simulateInput', 'simulate_input'],
    }

    const methods = methodNames[type] ?? []
    let lastError = null

    try {
      for (const method of methods) {
        try {
          await rpcClient.call(method, { enabled: checked })
          return
        } catch (error) {
          lastError = error
        }
      }

      console.warn(`Simulation ${type} failed: ${lastError?.message ?? 'Unknown error'}`)
    } catch (error) {
      console.warn(`Simulation ${type} failed: ${error.message}`)
    }

    if (type === 'matrix') {
      setSimulateMatrix(checked)
    } else {
      setSimulateInput(checked)
    }
  }

  const gestureOptions = [
    'unknown',
    'open',
    'closed',
    'pointing',
    'victory',
    'thumbs_up',
    'thumbs_down',
  ]

  const sendGesture = async (gesture) => {
  setSelectedGesture(gesture)

  const { width, height } = cameraSizeRef.current
  const { x, y } = lastPointerRef.current

  try {
    await rpcClient.publish(MOUSE_EVENT_TOPIC, {
      x: width ? Math.round(x * width) : x,
      y: height ? Math.round(y * height) : y,
      gesture,
    })
  } catch (error) {
    console.warn('Gesture publish failed:', error)
  }
}

  return (
    <main>
  <h1>Game Simulator</h1>

  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
    <button type="button" onClick={() => cycleGame(-1)} disabled={cycling}>
      ◀ Previous game
    </button>
    <button type="button" onClick={() => cycleGame(1)} disabled={cycling}>
      Next game ▶
    </button>
      <button type="button" onClick={() => pauseGame(1)} disabled={pausing}>
      Pause 
    </button>
  </div>

  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
    <label>
      <input
        type="checkbox"
        checked={simulateMatrix}
        onChange={async (event) => {
          const checked = event.target.checked
          setSimulateMatrix(checked)
          await toggleSimulation('matrix', checked)
        }}
      />
      Simulate matrix
    </label>

    <label>
      <input
        type="checkbox"
        checked={simulateInput}
        onChange={async (event) => {
          const checked = event.target.checked
          setSimulateInput(checked)
          await toggleSimulation('input', checked)
        }}
      />
      Simulate input
    </label>
  </div>


      <div style={{ marginBottom: '1rem' }}>
        <div style={{ marginBottom: '0.5rem' }}><strong>Gesture:</strong> {selectedGesture}</div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {gestureOptions.map((gesture) => (
            <button
              key={gesture}
              type="button"
              onClick={() => sendGesture(gesture)}
              style={{
                padding: '0.35rem 0.65rem',
                borderRadius: '6px',
                cursor: 'pointer',
                background: selectedGesture === gesture ? '#2563eb' : '#1f2937',
                color: '#fff',
                border: '1px solid #374151',
              }}
            >
              {gesture}
            </button>
          ))}
        </div>
      </div>

      <div>
        <strong>Matrix:</strong> {matrixSize.width} x {matrixSize.height}
      </div>
      <div>
        <strong>Camera:</strong> {cameraSize.width} x {cameraSize.height}
      </div>

      <div
        onPointerDown={handlePointerEvent}
        onPointerMove={handlePointerEvent}
        onPointerUp={handlePointerEvent}
        style={{
          display: 'grid',
          gap: '2px',
          width: '420px',
          maxWidth: '100%',
          marginTop: '1rem',
          background: '#111827',
          padding: '8px',
          borderRadius: '8px',
          ...gridStyle,
        }}
      >
        {matrixData.length > 0 ? (
          matrixData.map((row, rowIndex) =>
            row.map((cell, colIndex) => (
              <div
                key={`${rowIndex}-${colIndex}`}
                style={{
                  width: '100%',
                  aspectRatio: '1 / 1',
                  background:
                    cell && typeof cell === 'object'
                      ? `rgb(${cell.r ?? 0}, ${cell.g ?? 0}, ${cell.b ?? 0})`
                      : Number(cell) ? '#22c55e' : '#1f2937',
                  border: '1px solid rgba(255,255,255,0.08)',
                  boxSizing: 'border-box',
                }}
              />
            )),
          )
        ) : (
          <div
            style={{
              minHeight: '180px',
              display: 'grid',
              placeItems: 'center',
              color: '#9ca3af',
              background: '#111827',
            }}
          >
            Waiting for matrix data...
          </div>
        )}
      </div>

      {visibleRows > 0 && visibleCols > 0 && (
        <div style={{ marginTop: '0.75rem', color: '#cbd5e1' }}>
          Matrix cells: {visibleRows} x {visibleCols}
        </div>
      )}
    </main>
  )
}

export default GameSimulator
