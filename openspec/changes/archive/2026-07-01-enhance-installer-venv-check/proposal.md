## Why

Many Linux distributions (most notably Debian, Ubuntu, and their derivatives) package the Python standard library's `venv` module separately. When a user runs the installer on a clean distro without `python3-venv` installed, virtual environment setup fails. The installer currently prints a generic error message, causing manual troubleshooting and installation friction.

## What Changes

- Implement contextual package manager detection inside the installer script.
- Modify the virtual environment verification fallback logic: if environment creation fails, detect the package manager (e.g. `apt`, `dnf`, `pacman`, `apk`, `brew`) and output the exact system command to install `python3-venv` or `virtualenv` on the user's platform.
- Update documentation and specification to reflect this requirement.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `simple-installer`: Modify the virtual environment prerequisite check to provide platform-specific package manager instructions on failure.

## Impact

- `bin/installer.sh`: Affected by package manager detection and custom error messaging.
- `openspec/specs/simple-installer/spec.md`: Requirements updated to reflect contextual suggestions.
