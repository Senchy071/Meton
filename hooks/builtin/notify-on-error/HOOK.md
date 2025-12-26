---
name: notify-on-error
hook_type: post_tool
command: 'notify-send "Meton Tool Error" "Tool ''{name}'' failed: {error}"'
condition: "{success} == false"
description: Sends desktop notification when a tool fails
enabled: false
blocking: false
timeout: 5
---

# Notify on Error

This hook sends a desktop notification when any tool execution fails.

## Purpose

- Get immediate feedback on tool failures
- Don't miss errors when working in another window
- Helpful for long-running operations

## Requirements

- Linux: `notify-send` (from libnotify)
- macOS: Use `osascript` instead
- Windows: Use PowerShell notification

## Enabling

Enable this hook with:
```
/hook enable notify-on-error
```

## Customization

Create a project-specific version in `.meton/hooks/notify-on-error/HOOK.md` to:
- Customize the notification message
- Add sound alerts
- Send to different notification systems
