# Meton Project Guidelines

## Documentation Style

### Markdown Files (.md)
- Keep all official documentation professional
- Do not use emoticons or emojis in .md files
- Use clear, technical language
- Follow standard markdown formatting

### Code Comments
- Standard Python docstring conventions
- Clear, concise explanations

## File Operations

### Tool Development
- All file operations must use the FileOperationsTool
- Validate paths against allowed/blocked lists
- Respect size limits for file operations

### Testing
- Test files should be prefixed with `test_`
- Place in project root or appropriate subdirectory
- Include descriptive test names

## Agent Behavior

### System Prompt Rules
- Agent must trust tool output statistics completely
- CRITICAL: When tool output shows "✓ Found X file(s)", use that exact number X
- Do not manually count file paths - the tool already counted them correctly
- Do not verify or double-check numerical data provided by tools
- WRONG: "Based on file paths provided, I count 4 files"
- RIGHT: "Tool found 5 files" (using the count from "Found 5 file(s)" header)

### Answer Formatting
- When user asks for counts/numbers: provide ONLY the count
- When user asks to list/show: provide individual items
- Do not dump full file lists when user only wants counts
- Read the user's question carefully to determine what format to use

### Commit Policy
- User handles commits manually
- Do not auto-commit changes
- Provide clear summaries of changes made
