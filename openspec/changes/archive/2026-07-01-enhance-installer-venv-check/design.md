## Context

Many Linux distributions unbundle Python's virtual environment module. The `bin/installer.sh` currently crashes with a generic installation instructions fallback if `python3 -m venv` and `virtualenv` both fail. We want to detect the underlying package manager and suggest the exact install command (e.g., `sudo apt install python3-venv` on Ubuntu/Debian) to eliminate developer friction.

## Goals / Non-Goals

**Goals:**
- Detect common package managers (`apt`, `dnf`, `pacman`, `apk`, `brew`) when virtual environment setup fails.
- Display the exact installation command appropriate for the user's operating system/distribution.
- Keep the script safe, predictable, and fully executable in user-space.

**Non-Goals:**
- Do not execute package installation commands automatically or prompt the user for their root/sudo password (maintain user-space isolation).
- Do not build a complex system-provisioning utility; keep detection logic lightweight and shell-native.

## Decisions

### Decision 1: Package Manager Detection Method

- **Option A (Chosen):** Check for the existence of package manager binaries (`apt-get`, `dnf`, `pacman`, `apk`, `brew`) using `command -v`.
  - *Rationale:* Portability across POSIX shells, lightweight, and requires no complex file parsing. Highly robust for standard installations.
- **Option B:** Parse `/etc/os-release` and inspect the `ID` or `ID_LIKE` values.
  - *Rationale:* While precise, parsing files in Bash introduces regex complexity and potential edge-case failures across custom or minimal container/distro environments.

### Decision 2: Installer Action on Missing Dependencies

- **Option A (Chosen):** Print the exact command, print a clear error, and exit with code 1.
  - *Rationale:* Maximizes security and user trust for a piped-curl installation. The user retains complete control.
- **Option B:** Auto-execute the installation command with `sudo`.
  - *Rationale:* Rejected due to the "curl-pipe-sudo" security anti-pattern. Prompts for root passwords within curled scripts are untrusted and fail in automated CI/CD runs.

## Risks / Trade-offs

- **[Risk]** Multiple package managers present (e.g., macOS with both `brew` and MacPorts, or a Linux distro running Nix + Apt).
  - *Mitigation:* Sequence the `command -v` checks in a logical order of priority (e.g., checking system-native package managers like `apt-get` before secondary ones).
- **[Risk]** The suggested package manager command fails because of system package lock issues or custom repos.
  - *Mitigation:* Since we only output the command text, any failures when running the command occur in the user's shell under the standard package manager output, keeping troubleshooting direct and simple.
