# Meton AI Assistant - VS Code Extension

A VS Code extension that integrates Meton, a local AI coding assistant, directly into your editor.

## Features

- **Code Explanation**: Get detailed explanations of selected code
- **Code Review**: Receive AI-powered code review feedback
- **Test Generation**: Automatically generate tests for your code
- **Refactoring Suggestions**: Get intelligent refactoring recommendations
- **Interactive Chat**: Ask Meton anything about your code
- **Workspace Indexing**: Semantic search across your entire codebase
- **Status Bar Integration**: Quick access and connection status

## Requirements

- **Meton Server**: The Meton API server must be running
- **Python 3.11+**: Required for the Meton backend
- **VS Code 1.80.0+**: Minimum supported VS Code version

## Installation

### 1. Install the Extension

```bash
# Build from source
cd vscode-extension
npm install
npm run compile
npm run package

# Install the generated .vsix file
code --install-extension meton-0.1.0.vsix
```

### 2. Start the Meton API Server

```bash
# From the main Meton directory
source venv/bin/activate
python api/server.py

# Or specify custom host/port
python api/server.py --host 127.0.0.1 --port 8000
```

## Configuration

Configure the extension in VS Code settings:

```json
{
  "meton.serverUrl": "http://localhost:8000",
  "meton.autoIndex": true,
  "meton.enableInlineAssist": true
}
```

### Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `meton.serverUrl` | string | `http://localhost:8000` | Meton API server URL |
| `meton.autoIndex` | boolean | `true` | Automatically index workspace on open |
| `meton.enableInlineAssist` | boolean | `true` | Enable inline code assistance |

## Usage

### Commands

Access Meton commands through the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

- **Meton: Explain Selected Code** - Get detailed code explanation
- **Meton: Review Selected Code** - Get code review feedback
- **Meton: Generate Tests** - Generate tests for selected code
- **Meton: Suggest Refactorings** - Get refactoring suggestions
- **Meton: Open Chat** - Ask Meton anything
- **Meton: Index Workspace** - Manually index your workspace

### Keyboard Shortcuts

| Command | Windows/Linux | macOS |
|---------|---------------|-------|
| Explain Code | `Ctrl+Shift+E` | `Cmd+Shift+E` |
| Open Chat | `Ctrl+Shift+M` | `Cmd+Shift+M` |

### Status Bar

The Meton status bar item shows the current connection status:

- ✓ **Meton** - Connected and ready
- ✗ **Meton** - Disconnected (check if server is running)
- ⟲ **Meton** - Processing request
- ⚡ **Meton** - Indexing workspace

Click the status bar item to open the chat.

## Features in Detail

### Code Explanation

1. Select code in the editor
2. Run `Meton: Explain Selected Code`
3. View detailed explanation in a side panel

### Code Review

1. Select code to review
2. Run `Meton: Review Selected Code`
3. Get feedback on:
   - Code quality
   - Potential bugs
   - Security issues
   - Performance improvements
   - Best practices

### Test Generation

1. Select a function or class
2. Run `Meton: Generate Tests`
3. Get generated test cases (pytest/unittest style)

### Refactoring Suggestions

1. Select code that needs improvement
2. Run `Meton: Suggest Refactorings`
3. Get specific refactoring recommendations

### Interactive Chat

1. Click the Meton status bar item or use `Ctrl+Shift+M`
2. Type your question
3. Get AI-powered responses

### Workspace Indexing

Meton automatically indexes your workspace for semantic code search:

- Runs on workspace open (if `autoIndex` is enabled)
- Indexes all Python files
- Enables intelligent code search
- Manual indexing: `Meton: Index Workspace`

## Troubleshooting

### Extension Shows "Disconnected"

1. Make sure the Meton API server is running:
   ```bash
   python api/server.py
   ```

2. Check the server URL in settings matches where the server is running

3. Verify the server is healthy:
   ```bash
   curl http://localhost:8000/health
   ```

### Commands Don't Work

1. Make sure code is selected for explain/review/test/refactor commands
2. Check the VS Code developer console for errors (`Help > Toggle Developer Tools`)
3. Restart VS Code

### Indexing Fails

1. Make sure you have a workspace folder open
2. Check that the Meton server has access to the workspace path
3. Verify sufficient disk space for the index

## Development

### Building from Source

```bash
# Install dependencies
cd vscode-extension
npm install

# Compile TypeScript
npm run compile

# Watch mode for development
npm run watch

# Package extension
npm run package
```

### Project Structure

```
vscode-extension/
├── src/
│   ├── extension.ts      # Main entry point
│   ├── metonClient.ts    # HTTP client for Meton API
│   ├── commands.ts       # VS Code command implementations
│   └── statusBar.ts      # Status bar integration
├── package.json          # Extension manifest
├── tsconfig.json         # TypeScript configuration
└── README.md            # This file
```

## Contributing

Contributions are welcome! Please see the main Meton repository for contribution guidelines.

## License

Same license as the main Meton project.

## Links

- [Meton Repository](https://github.com/your-repo/meton)
- [Report Issues](https://github.com/your-repo/meton/issues)
- [Documentation](https://github.com/your-repo/meton/docs)

## Changelog

### 0.1.0 - Initial Release

- Basic extension scaffold
- Core commands (explain, review, test, refactor, chat)
- Workspace indexing
- Status bar integration
- HTTP API client
