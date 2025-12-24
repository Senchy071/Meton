---
name: log-tool-usage
hook_type: post_tool
command: echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Tool: {name} | Success: {success} | Duration: {duration}s" >> ~/.meton/tool_usage.log
description: Logs all tool executions to a file for analysis
enabled: false
blocking: false
timeout: 5
---

# Log Tool Usage

This hook logs all tool executions to `~/.meton/tool_usage.log` for later analysis.

## Purpose

- Track which tools are used most frequently
- Monitor tool execution times
- Debug failed tool executions

## Output Format

Each line contains:
- Timestamp
- Tool name
- Success status
- Duration in seconds

## Example Output

```
[2025-01-15 14:30:22] Tool: file_operations | Success: true | Duration: 0.05s
[2025-01-15 14:30:25] Tool: codebase_search | Success: true | Duration: 1.23s
```

## Enabling

Enable this hook with:
```
/hook enable log-tool-usage
```
