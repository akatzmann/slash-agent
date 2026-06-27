## ADDED Requirements

### Requirement: Terminal Skill Read Visualization
The event streaming loop in `main.py` SHALL intercept `ToolExecutionStartEvent` and `ToolExecutionEndEvent` for `read_skill_instructions` calls to output real-time visual badges in the terminal.

#### Scenario: Real-time skill read badges rendered
- **WHEN** `read_skill_instructions` execution starts and ends
- **THEN** the terminal displays `🛠 [Skill] <skill-name>` on start and `✓ Loaded skill instructions` on completion
