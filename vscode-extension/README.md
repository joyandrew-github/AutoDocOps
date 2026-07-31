# AutoDocOps VS Code Extension

Official VS Code extension for the AutoDocOps AI Documentation Operations platform.

## Features

- **Login / Logout** — JWT-based authentication with the AutoDocOps backend
- **Repository Selection** — pick from connected repositories
- **AI Chat** — streaming AI responses with full conversation history
- **Explain Function** — right-click or use lightbulb on any function definition
- **Explain Class** — right-click or use lightbulb on any class definition
- **Explain File** — get an AI overview of the entire file
- **Explain Selection** — select code and ask AI to explain it
- **Ask AI About Selection** — custom question about selected code
- **Semantic Search** — natural language code search (`Ctrl+Shift+S`)
- **Architecture Viewer** — view architecture models and dependency graph
- **Documentation Viewer** — browse generated documentation
- **Impact Analysis** — view risk assessment and change impact
- **Hover Explanations** — AI explanations on hover for function/class definitions
- **Inline Code Actions** — lightbulb actions for AI features
- **Status Bar** — shows login state and current user
- **Settings** — configure server URL, repository, and feature toggles

## Keyboard Shortcuts

| Shortcut | Command |
|---|---|
| `Ctrl+Shift+A` | Open AI Chat |
| `Ctrl+Shift+S` | Semantic Search |
| `Ctrl+Shift+E` | Explain Selection |

## Configuration

| Setting | Default | Description |
|---|---|---|
| `autodocops.serverUrl` | `http://localhost:8000` | Backend server URL |
| `autodocops.repositoryId` | `0` | Selected repository ID |
| `autodocops.enableHoverExplanations` | `true` | Show AI hover explanations |
| `autodocops.enableInlineCodeActions` | `true` | Show lightbulb code actions |
| `autodocops.streamResponses` | `true` | Stream AI responses |
| `autodocops.maxSearchResults` | `20` | Max semantic search results |

## Development

```bash
cd vscode-extension
npm install
npm run compile
```

Press `F5` to launch the extension in a new VS Code window.

## Building

```bash
npm run package
```

## Requirements

- AutoDocOps backend running (default: `http://localhost:8000`)
- VS Code 1.85.0+
