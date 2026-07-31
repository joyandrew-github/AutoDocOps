import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

export class AutoDocOpsHoverProvider implements vscode.HoverProvider {
  private client: ApiClient;
  private cache = new Map<string, { content: string; timestamp: number }>();
  private cacheTTL = 60_000;

  constructor(client: ApiClient) {
    this.client = client;
  }

  async provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
    _token: vscode.CancellationToken
  ): Promise<vscode.Hover | undefined> {
    const enabled = vscode.workspace.getConfiguration('autodocops').get<boolean>('enableHoverExplanations', true);
    if (!enabled || !this.client.isAuthenticated()) { return undefined; }

    const wordRange = document.getWordRangeAtPosition(position);
    if (!wordRange) { return undefined; }

    const word = document.getText(wordRange);
    if (word.length < 3) { return undefined; }

    const line = document.lineAt(position.line).text;
    const isDefinition = /^\s*(def |function |class |async\s+def |async\s+function |export\s+(default\s+)?(function|class)\s)/.test(line);
    if (!isDefinition) { return undefined; }

    const cacheKey = `${document.uri.toString()}:${position.line}:${word}`;
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return new vscode.Hover(new vscode.MarkdownString(cached.content));
    }

    const repoId = vscode.workspace.getConfiguration('autodocops').get<number>('repositoryId');
    if (!repoId) { return undefined; }

    const resp = await this.client.aiChat(
      `Briefly explain this ${isDefinition ? 'definition' : 'symbol'}: ${word}\nContext: ${line.trim()}`,
      repoId
    );

    if (resp.ok && resp.data?.content) {
      const content = `**AutoDocOps AI** — *${resp.data.agent_name || 'AI'}*\n\n${resp.data.content}`;
      this.cache.set(cacheKey, { content, timestamp: Date.now() });
      return new vscode.Hover(new vscode.MarkdownString(content));
    }

    return undefined;
  }
}
