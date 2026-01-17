# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-17

### Added

- Climate entity with HVAC mode control, target temperature, and preset modes (thermostat modes)
- HACS compatibility with `hacs.json` configuration
- Proper `custom_components/` directory structure
- Transport-specific default poll intervals (BLE: 30s, WebSocket: 60s)
- Comprehensive README with installation, configuration, and troubleshooting guides
- `.gitignore` for Python, IDE, and macOS artifacts

### Changed

- Bumped version to 0.2.0
- Consolidated duplicate `_parse_ble_init_message` and `_parse_ws_init_message` functions into single `_parse_init_message`
- Updated `manifest.json` with proper Bluetooth UUID format
- Improved code organization by removing duplicate files

### Removed

- Duplicate `models.py` at integration root (protocol/models.py is canonical)
- Duplicate `json_stream.py` in api folder (protocol/json_stream.py is canonical)
- Root-level duplicate files (sensor.py, switch.py, coordinator.py, etc.)
- `__MACOSX/`, `__pycache__/`, `.DS_Store`, and `BTDebug/` artifacts
- Duplicate README inside integration folder

### Fixed

- Missing `DEFAULT_POLL_INTERVAL_BLE` and `DEFAULT_POLL_INTERVAL_WS` constants in `const.py`
- Import statements to use transport-specific poll intervals

## [0.1.0] - Initial Release

### Added

- Initial implementation with BLE and WebSocket transport support
- Config flow for easy setup
- DataUpdateCoordinator for efficient state management
- Entity platforms: sensors, binary sensors, switches, numbers, selects
- Custom services for heater control
- Push-based updates via transport callbacks
- JSON stream parser for fragmented BLE payloads
- Diagnostics support with sensitive data redaction
