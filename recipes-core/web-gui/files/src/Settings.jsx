import { useMemo, useState } from 'react'
import { rpcClient } from './mqttRpc.js'

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
