## 1. Python Config Loading Implementation

- [x] 1.1 Implement config path resolution helper in `slash_agent/main.py` supporting XDG specifications and falling back to `~/.config/slash-agent/env`
- [x] 1.2 Implement auto-migration logic in `slash_agent/main.py` to detect, load, and write legacy `.env` configuration properties into the relocated config file, followed by clearing or removing the old `.env` file
- [x] 1.3 Update the initialization sequence in `slash_agent/main.py` to execute the migration and load the environment variables from the resolved config path

## 2. Installer Configuration Update

- [x] 2.1 Implement config path resolution function in `bin/installer.sh` to match the XDG resolution logic
- [x] 2.2 Update all reading, checking, loading, prompting, and saving logic in `bin/installer.sh` to target the XDG config path instead of the local `.env` file
- [x] 2.3 Add permissions enforcement (`chmod 600`) and parent directory creation for the config file in `bin/installer.sh`
- [x] 2.4 Add legacy `.env` migration and cleanup handling inside the installer script

## 3. Documentation Updates

- [x] 3.1 Update `README.md` configuration guide to direct users to the XDG config path (`~/.config/slash-agent/env`) and explain `SLASH_AGENT_CONFIG_FILE` override
- [x] 3.2 Update `docs/documentation.md` configuration details to point to the new relocated config path and XDG resolution specifications

## 4. Verification

- [x] 4.1 Verify that running the agent with a legacy `.env` file migrates the config to the XDG path, locks permissions to `600`, and clears the legacy `.env` file
- [x] 4.2 Verify that the installer configured in standard mode or with `--configure` reads and writes to the correct XDG path
- [x] 4.3 Verify that all references to the configuration file in `README.md` and `docs/documentation.md` are correct and refer to the new XDG configuration paths
- [x] 4.4 Run `/agent` command interactively and ensure agent operations succeed without issues using the new config location
