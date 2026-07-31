import * as vscode from 'vscode';
import { ApiClient } from './api/client';
import { AuthProvider } from './auth/authProvider';
import { ChatPanel } from './views/chatPanel';
import { ArchitecturePanel } from './views/architecturePanel';
import { DocumentationPanel } from './views/documentationPanel';
import { ImpactPanel } from './views/impactPanel';
import { AutoDocOpsHoverProvider } from './providers/hoverProvider';
import { AutoDocOpsCodeActionProvider } from './providers/codeActionProvider';

let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  const outputChannel = vscode.window.createOutputChannel('AutoDocOps');
  outputChannel.appendLine('AutoDocOps extension activating...');

  // Status bar
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  context.subscriptions.push(statusBarItem);

  // API client & auth
  const client = new ApiClient(context);
  const auth = new AuthProvider(client, statusBarItem);
  auth.initialize();

  // All supported languages for providers
  const langSelector: vscode.DocumentSelector = [
    { scheme: 'file', language: 'python' },
    { scheme: 'file', language: 'javascript' },
    { scheme: 'file', language: 'typescript' },
    { scheme: 'file', language: 'typescriptreact' },
    { scheme: 'file', language: 'javascriptreact' },
    { scheme: 'file', language: 'java' },
    { scheme: 'file', language: 'go' },
    { scheme: 'file', language: 'rust' },
    { scheme: 'file', language: 'csharp' },
    { scheme: 'file', language: 'cpp' },
    { scheme: 'file', language: 'c' },
  ];

  // Register hover provider
  context.subscriptions.push(
    vscode.languages.registerHoverProvider(langSelector, new AutoDocOpsHoverProvider(client))
  );

  // Register code action provider
  context.subscriptions.push(
    vscode.languages.registerCodeActionsProvider(
      langSelector,
      new AutoDocOpsCodeActionProvider(),
      { providedCodeActionKinds: AutoDocOpsCodeActionProvider.providedCodeActionKinds }
    )
  );

  // ---- Commands ----

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.login', () => auth.login())
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.logout', () => auth.logout())
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.selectRepository', async () => {
      const resp = await client.listRepositories();
      if (!resp.ok || !resp.data?.length) {
        vscode.window.showWarningMessage('No repositories found. Connect one via the dashboard first.');
        return;
      }
      const items = resp.data.map((r: any) => ({
        label: r.name,
        description: r.url,
        detail: `ID: ${r.id} — ${r.default_branch || 'main'}`,
        id: r.id,
      }));
      const picked = await vscode.window.showQuickPick(items, { placeHolder: 'Select a repository' });
      if (picked) {
        await vscode.workspace.getConfiguration('autodocops').update('repositoryId', (picked as any).id, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(`AutoDocOps: Selected repository "${(picked as any).label}"`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.openChat', () => {
      ChatPanel.create(context.extensionUri, client);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.explainFunction', () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) { return; }
      const line = editor.document.lineAt(editor.selection.active.line).text;
      const match = line.match(/(def|function|async\s+function|async\s+def)\s+(\w+)/);
      const name = match ? match[2] : 'this function';
      const panel = ChatPanel.create(context.extensionUri, client);
      panel.sendInitialMessage(`Explain the function "${name}" in file ${editor.document.fileName}:\n\n${getContextLines(editor, 30)}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.explainClass', () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) { return; }
      const line = editor.document.lineAt(editor.selection.active.line).text;
      const match = line.match(/class\s+(\w+)/);
      const name = match ? match[1] : 'this class';
      const panel = ChatPanel.create(context.extensionUri, client);
      panel.sendInitialMessage(`Explain the class "${name}" in file ${editor.document.fileName}:\n\n${getContextLines(editor, 50)}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.explainFile', () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) { return; }
      const content = editor.document.getText().substring(0, 3000);
      const panel = ChatPanel.create(context.extensionUri, client);
      panel.sendInitialMessage(`Explain the file ${editor.document.fileName}:\n\n${content}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.explainSelection', () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.selection.isEmpty) {
        vscode.window.showWarningMessage('Select some code first.');
        return;
      }
      const selection = editor.document.getText(editor.selection);
      const panel = ChatPanel.create(context.extensionUri, client);
      panel.sendInitialMessage(`Explain this code from ${editor.document.fileName}:\n\n${selection}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.askAboutSelection', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.selection.isEmpty) {
        vscode.window.showWarningMessage('Select some code first.');
        return;
      }
      const question = await vscode.window.showInputBox({ prompt: 'What would you like to ask about this code?' });
      if (!question) { return; }
      const selection = editor.document.getText(editor.selection);
      const panel = ChatPanel.create(context.extensionUri, client);
      panel.sendInitialMessage(`${question}\n\nCode from ${editor.document.fileName}:\n\n${selection}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.semanticSearch', async () => {
      const query = await vscode.window.showInputBox({
        prompt: 'Semantic Search',
        placeHolder: 'Search code with natural language...',
      });
      if (!query) { return; }
      const repoId = vscode.workspace.getConfiguration('autodocops').get<number>('repositoryId');
      const maxResults = vscode.workspace.getConfiguration('autodocops').get<number>('maxSearchResults', 20);

      const resp = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: 'AutoDocOps: Searching...' },
        () => client.semanticSearch(query, repoId || undefined, undefined, maxResults)
      );

      if (!resp.ok || !resp.data?.results?.length) {
        vscode.window.showInformationMessage('No results found.');
        return;
      }

      const items = resp.data.results.map((r: any) => ({
        label: `$(symbol-${getSymbolIcon(r.entity_type)}) ${r.entity_name || r.name || 'Unknown'}`,
        description: `${r.entity_type || ''} — score: ${(r.similarity_score || r.score || 0).toFixed(3)}`,
        detail: r.file_path || '',
        filePath: r.file_path,
        line: r.start_line,
      }));

      const picked = await vscode.window.showQuickPick(items, {
        placeHolder: `${resp.data.total} results for "${query}"`,
        matchOnDescription: true,
        matchOnDetail: true,
      });

      if (picked && (picked as any).filePath) {
        try {
          const doc = await vscode.workspace.openTextDocument((picked as any).filePath);
          const editor = await vscode.window.showTextDocument(doc);
          if ((picked as any).line) {
            const line = Math.max(0, (picked as any).line - 1);
            const pos = new vscode.Position(line, 0);
            editor.selection = new vscode.Selection(pos, pos);
            editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
          }
        } catch {
          vscode.window.showWarningMessage(`Could not open file: ${(picked as any).filePath}`);
        }
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.viewArchitecture', () => {
      new ArchitecturePanel(client);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.viewDocumentation', () => {
      new DocumentationPanel(client);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('autodocops.viewImpact', () => {
      new ImpactPanel(client);
    })
  );

  outputChannel.appendLine('AutoDocOps extension activated.');
}

export function deactivate() { }

function getContextLines(editor: vscode.TextEditor, count: number): string {
  const line = editor.selection.active.line;
  const start = Math.max(0, line - 5);
  const end = Math.min(editor.document.lineCount - 1, line + count);
  const lines: string[] = [];
  for (let i = start; i <= end; i++) {
    lines.push(editor.document.lineAt(i).text);
  }
  return lines.join('\n');
}

function getSymbolIcon(entityType: string): string {
  switch (entityType?.toLowerCase()) {
    case 'function': return 'function';
    case 'class': return 'class';
    case 'method': return 'method';
    case 'variable': return 'variable';
    case 'file': return 'file';
    case 'import': return 'namespace';
    default: return 'misc';
  }
}
