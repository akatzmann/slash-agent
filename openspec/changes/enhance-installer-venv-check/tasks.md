## 1. Implement Package Manager Detection

- [x] 1.1 Add helper function to detect system package manager (`apt-get`, `dnf`, `pacman`, `apk`, `brew`) inside `bin/installer.sh`
- [x] 1.2 Add logic to map each detected package manager to the correct python virtual environment package installation command

## 2. Refactor Prerequisites Check

- [x] 2.1 Update virtual environment creation verification block inside `bin/installer.sh` to call the package manager helper upon failure
- [x] 2.2 Print the contextual command and instructions, then exit with code 1

## 3. Verification

- [x] 3.1 Manually verify the fallback message by temporarily simulating environment creation failures in different environment contexts
- [x] 3.2 Verify that the installer still executes successfully without error when a working virtual environment is present
