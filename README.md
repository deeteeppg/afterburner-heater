# Afterburner Heater

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)

Custom Home Assistant integration for Afterburner diesel heaters over Bluetooth Low Energy (BLE) or WebSocket.

## Features

- **Dual transport support**: Connect via BLE or WebSocket
- **Real-time updates**: Push-based updates from heater
- **Full control**: Power on/off, thermostat modes, cyclic heating, frost protection
- **Comprehensive sensors**: Temperature, humidity, voltage, fuel usage, fan speed, and more
- **GPIO control**: General-purpose outputs for accessories

## Transport Selection

Both BLE and WebSocket transports receive identical data. **BLE is recommended** for best performance:

| Transport | Response Time | Network Requirement |
|-----------|--------------|---------------------|
| **BLE** | ~113ms (3x faster) | Bluetooth range only |
| WebSocket | ~400ms | Network connectivity |

Choose WebSocket only if you need to control the heater beyond Bluetooth range.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu and select "Custom repositories"
3. Add `https://github.com/deeteeppg/afterburner-heater` as an "Integration"
4. Search for "Afterburner Heater" and install
5. Restart Home Assistant
6. Add the integration via Settings → Devices & Services → Add Integration

### Manual Installation

1. Copy the `custom_components/afterburner_heater/` folder to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services → Add Integration

## Configuration

### BLE Setup

1. Ensure your heater is powered on and Bluetooth is enabled
2. Add the integration and select "BLE" transport
3. Select your heater from the discovered devices list (or enter address manually)
4. Configure options:
   - **Update interval**: How often to request full state refresh (default: 30s)
   - **Write characteristic**: FFE1 or FFE2
   - **Write with response**: Enable for reliable delivery

### WebSocket Setup

1. Note your heater's IP address
2. Add the integration and select "WebSocket" transport
3. Enter connection details:
   - **Host**: IP address or hostname
   - **Port**: 81 (default)
   - **Path**: / (default)
   - **Token**: Optional authentication token

## Entities

### Climate

The main climate entity provides:
- **HVAC modes**: Off, Heat
- **Target temperature**: Sets cyclic temperature setpoint
- **Preset modes**: Standard, Deadband, Linear Hz, Stop/Start (thermostat modes)

### Sensors

- Temperature (ambient, body, thermostat, BME280)
- Humidity
- Pressure (barometric)
- Voltage (input, system, glow plug)
- Current (glow plug)
- Fan speed (RPM)
- Pump speed
- Fuel usage
- Heater state and error strings

### Switches

- Power (on/off)
- Cyclic mode enable
- Frost protection enable
- Thermostat enable
- GP outputs 1 & 2

### Number Controls

- Cyclic temperature setpoint
- Cyclic on/off thresholds
- Frost start/rise/target temperatures
- Fixed power demand

### Selects

- Thermostat mode (Standard, Deadband, Linear Hz, Stop/Start)
- Frost mode

## Services

### `afterburner_heater.send_json`

Send a raw JSON command:

```yaml
service: afterburner_heater.send_json
data:
  cmd: ThermostatMode
  value: "Deadband"
```

Or send a complete payload:

```yaml
service: afterburner_heater.send_json
data:
  payload: '{"CyclicTemp": 22.5, "CyclicEnb": 1}'
```

### Helper Services

- `set_cyclic_temp`, `set_cyclic_on`, `set_cyclic_off`
- `set_cyclic_enabled`
- `set_frost_enable`, `set_frost_on`, `set_frost_rise`, `set_frost_target`
- `set_thermostat`, `set_thermostat_mode`
- `set_fixed_demand`
- `set_gpout1`, `set_gpout2`

## Command Reference

| Command | Type | Description |
|---------|------|-------------|
| `Run` | `"heat"` or `"off"` | Start/stop heater |
| `CyclicTemp` | float | Target temperature |
| `CyclicOn` | float | Restart threshold |
| `CyclicOff` | float | Stop threshold |
| `CyclicEnb` | 0/1 | Enable cyclic mode |
| `FrostEnable` | 0/1 | Enable frost protection |
| `FrostOn` | float | Frost activation temp |
| `FrostRise` | float | Frost rise value |
| `FrostTarget` | float | Frost target temp |
| `Thermostat` | 0/1 | Enable thermostat |
| `ThermostatMode` | string | Mode selection |
| `FixedDemand` | float/null | Fixed power demand |
| `GPout1`, `GPout2` | 0/1 | GPIO outputs |

## Troubleshooting

### BLE Connection Issues

1. Ensure your heater is within Bluetooth range
2. Check that no other device is connected to the heater
3. Try restarting the heater
4. Check Home Assistant logs for BLE errors

### WebSocket Connection Issues

1. Verify the heater's IP address is correct
2. Ensure port 81 is accessible
3. Check if a firewall is blocking the connection
4. Try accessing `ws://<ip>:81/` with a WebSocket client

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.afterburner_heater: debug
```

## Protocol Details

### BLE

- Service UUID: `FFE0`
- Notify characteristic: `FFE1`
- Write characteristic: `FFE1` (or `FFE2`)
- Commands sent as UTF-8 JSON

### WebSocket

- Default URL: `ws://<host>:81/`
- Messages are JSON objects
- Heater pushes periodic updates automatically

## License

This project is provided as-is for personal use with Afterburner heaters.
