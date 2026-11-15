import { useEffect, useMemo, useState } from 'react'
import { rpcClient } from './mqttRpc.js'

const GAME_TOPIC = 'engine/available'
const SIMULATOR_STATE_TOPIC = 'engine/simulator/config'

const settingsConfig = [
  {
    key: 'brightness',
    label: 'Brightness',
    type: 'range',
    min: 0,
    max: 100,
    defaultValue: 50,
    methods: ['setBrightness', 'set_brightness'],
  },
  
  {
    key: 'volume',
    label: 'Volume',
    type: 'range',
    min: 0,
    max: 100,
    defaultValue: 70,
    methods: ['setVolume', 'set_volume'],
  },
  {
    key: 'reboot',
    label: 'Reboot Device',
    type: 'button',
    buttonLabel: 'Reboot',
    defaultValue: '',
    payload: {},
    methods: ['rebootDevice', 'reboot_device'],
  },
    {
    key: 'pause',
    label: 'Pause game',
    type: 'button',
    buttonLabel: 'Pause',
    defaultValue: '',
    payload: {},
    methods: ['pauseGame', 'pause_game'],
  },
  {
    key: 'test',
    label: 'Matrix test',
    type: 'button',
    buttonLabel: 'Test',
    defaultValue: '',
    payload: {},
    methods: ['testMatrix', 'test_matrix'],
  },
  {
    key: 'simulateMatrix',
    label: 'Simulate matrix',
    type: 'button',
    buttonLabel: 'Simulate matrix',
    defaultValue: '',
    payload: {},
    methods: ['simulateMatrix', 'simulate_matrix'],
  },
  {
    key: 'simulateInput',
    label: 'Simulate input',
    type: 'button',
    buttonLabel: 'Simulate input',
    defaultValue: '',
    payload: {},
    methods: ['simulateInput', 'simulate_input'],
  },
]

function Settings() {
  const [settingsState, setSettingsState] = useState(() =>
    Object.fromEntries(
      settingsConfig.map((setting) => [
        setting.key,
        {
          value: setting.defaultValue,
          status: 'Ready',
        },
      ]),
    ),
  )
  const [availableGames, setAvailableGames] = useState([])
  const [selectedGame, setSelectedGame] = useState('')
  const [gameStatus, setGameStatus] = useState('Loading available games...')

  useEffect(() => {
    const loadAvailableGames = async () => {
      try {
        const response = await rpcClient.call('game.list', {})
        const games = Array.isArray(response?.games) ? response.games : []

        setAvailableGames(games)
        if (games.length > 0) {
          setSelectedGame((current) => current || games[0])
          setGameStatus(`Loaded ${games.length} game(s)`) 
        } else {
          setGameStatus('No games available')
        }
      } catch (error) {
        setGameStatus(`Unable to load games: ${error?.message ?? 'Unknown error'}`)
      }
    }

    loadAvailableGames()

    const unsubscribeGames = rpcClient.subscribe(GAME_TOPIC, (message) => {
      try {
        const payload = JSON.parse(message.toString())
        const games = Array.isArray(payload?.games) ? payload.games : []
        if (!games.length) {
          return
        }

        setAvailableGames(games)
        setSelectedGame((current) => (games.includes(current) ? current : games[0]))
        setGameStatus(`Game list updated (${games.length})`)
      } catch (error) {
        const raw = message.toString().trim()
        if (!raw) {
          return
        }

        const fallbackGames = raw
          .replace(/[\[\]{}]/g, '')
          .split(',')
          .map((value) => value.replace(/['"]/g, '').trim())
          .filter(Boolean)

        if (fallbackGames.length > 0) {
          setAvailableGames(fallbackGames)
          setSelectedGame((current) => (fallbackGames.includes(current) ? current : fallbackGames[0]))
          setGameStatus(`Game list updated (${fallbackGames.length})`)
        }
      }
    })

    const unsubscribeSimulatorState = rpcClient.subscribe(SIMULATOR_STATE_TOPIC, (message) => {
      try {
        const payload = JSON.parse(message.toString())
        if (typeof payload?.simulateMatrix === 'boolean') {
          setSettingsState((previous) => ({
            ...previous,
            simulateMatrix: {
              ...previous.simulateMatrix,
              status: payload.simulateMatrix ? 'Enabled' : 'Disabled',
            },
          }))
        }
        if (typeof payload?.simulateInput === 'boolean') {
          setSettingsState((previous) => ({
            ...previous,
            simulateInput: {
              ...previous.simulateInput,
              status: payload.simulateInput ? 'Enabled' : 'Disabled',
            },
          }))
        }
      } catch {
        // ignore malformed simulator state messages
      }
    })

    return () => {
      unsubscribeGames()
      unsubscribeSimulatorState()
    }
  }, [])

  const handleGameChange = async (event) => {
    const nextGame = event.target.value
    setSelectedGame(nextGame)
    setGameStatus(`Switching to ${nextGame}...`)

    try {
      const response = await rpcClient.call('game.change', { game: nextGame })
      setGameStatus(`Game changed to ${response?.game ?? nextGame}`)
    } catch (error) {
      setGameStatus(`Failed to change game: ${error?.message ?? 'Unknown error'}`)
    }
  }

  const settingHandlers = useMemo(
    () =>
      Object.fromEntries(
        settingsConfig.map((setting) => [
          setting.key,
          async (event) => {
            const nextValue =
              setting.type === 'button'
                ? setting.defaultValue
                : event.target.value

            if (setting.type !== 'button') {
              setSettingsState((previous) => ({
                ...previous,
                [setting.key]: {
                  ...previous[setting.key],
                  value: nextValue,
                },
              }))
            }

            try {
              const payload =
                setting.type === 'button'
                  ? setting.payload ?? {}
                  : { [setting.key]: nextValue }

              let lastError = null

              for (const method of setting.methods) {
                try {
                  await rpcClient.call(method, payload)
                  setSettingsState((previous) => ({
                    ...previous,
                    [setting.key]: {
                      ...previous[setting.key],
                      status:
                        setting.type === 'button'
                          ? `${setting.label} triggered via ${method}`
                          : `${setting.label} set to ${nextValue}${setting.type === 'text' ? '' : '%'} via ${method}`,
                    },
                  }))
                  return
                } catch (error) {
                  lastError = error
                }
              }

              setSettingsState((previous) => ({
                ...previous,
                [setting.key]: {
                  ...previous[setting.key],
                  status: `Failed to set ${setting.label}: ${lastError?.message ?? 'Unknown error'}`,
                },
              }))
            } catch (error) {
              setSettingsState((previous) => ({
                ...previous,
                [setting.key]: {
                  ...previous[setting.key],
                  status: `Failed to set ${setting.label}: ${error.message}`,
                },
              }))
            }
          },
        ]),
      ),
    [],
  )

  return (
    <main>
      <h1>Settings</h1>

      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="game-select-control">Game</label>
        <select
          id="game-select-control"
          value={selectedGame}
          onChange={handleGameChange}
          disabled={availableGames.length === 0}
          style={{ display: 'block', marginTop: '0.5rem', minWidth: '180px' }}
        >
          {availableGames.length === 0 ? (
            <option value="">Loading...</option>
          ) : (
            availableGames.map((game) => (
              <option key={game} value={game}>
                {game}
              </option>
            ))
          )}
        </select>
        <div>{gameStatus}</div>
      </div>

      {settingsConfig.map((setting) => {
        const current = settingsState[setting.key]

        return (
          <div key={setting.key} style={{ marginBottom: '1rem' }}>
            <label htmlFor={`${setting.key}-control`}>
              {setting.label}
              {setting.type === 'range' && (
                <strong> {current.value}%</strong>
              )}
            </label>

            {setting.type === 'range' && (
              <input
                id={`${setting.key}-control`}
                type="range"
                min={setting.min}
                max={setting.max}
                value={current.value}
                onChange={settingHandlers[setting.key]}
              />
            )}

            {setting.type === 'select' && (
              <select
                id={`${setting.key}-control`}
                value={current.value}
                onChange={settingHandlers[setting.key]}
              >
                {setting.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            )}

            {setting.type === 'text' && (
              <input
                id={`${setting.key}-control`}
                type="text"
                value={current.value}
                onChange={settingHandlers[setting.key]}
              />
            )}

            {setting.type === 'button' && (
              <button type="button" onClick={settingHandlers[setting.key]}>
                {setting.buttonLabel}
              </button>
            )}

            <div>{current.status}</div>
          </div>
        )
      })}
    </main>
  )
}

export default Settings
