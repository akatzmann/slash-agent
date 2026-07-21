## Why

Windows users running `slash-agent` inside WSL2 and local LLM servers (like `llama.cpp` or `Ollama`) on the Windows host face network boundaries (due to WSL2's default NAT networking) that prevent connectivity. We need to document the configuration steps required to connect these environments.

## What Changes

- Add a visually distinct block note (`> [!NOTE]`) under the WSL2 section of `README.md` pointing developers to the host integration documentation.
- Add a dedicated, concise "WSL2 Host Network Integration" troubleshooting section in `docs/documentation.md` detailing both Mirrored Networking and NAT Mode routing options.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `github-documentation`: Update the specification to include scenarios verifying documentation of WSL2 cross-boundary networking configurations (both Mirrored Networking and NAT routing).

## Impact

- `README.md` (Updated to include redirect note)
- `docs/documentation.md` (Updated to include integration guides)
- `openspec/specs/github-documentation/spec.md` (Updated specification file)
