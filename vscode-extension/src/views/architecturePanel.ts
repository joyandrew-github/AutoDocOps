import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

export class ArchitecturePanel {
  private panel: vscode.WebviewPanel;

  constructor(client: ApiClient) {
    this.panel = vscode.window.createWebviewPanel(
      'autodocopsArch', 'AutoDocOps Architecture', vscode.ViewColumn.One, { enableScripts: true }
    );
    this.load(client);
  }

  private async load(client: ApiClient): Promise<void> {
    const repoId = vscode.workspace.getConfiguration('autodocops').get<number>('repositoryId');
    if (!repoId) {
      this.panel.webview.html = '<html><body><h2>No repository selected.</h2><p>Use "AutoDocOps: Select Repository" first.</p></body></html>';
      return;
    }

    this.panel.webview.html = '<html><body><h2>Loading architecture...</h2></body></html>';

    const [modelsResp, depsResp] = await Promise.all([
      client.listArchitecture(repoId),
      client.getDependencies(repoId),
    ]);

    const models = modelsResp.ok ? modelsResp.data : [];
    const deps = depsResp.ok ? depsResp.data : {};

    this.panel.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: var(--vscode-font-family); color: var(--vscode-editor-foreground); background: var(--vscode-editor-background); padding: 16px; }
  h1 { margin-bottom: 16px; }
  .model { background: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-widget-border); border-radius: 6px; padding: 12px; margin-bottom: 12px; }
  .model h3 { margin: 0 0 4px; }
  .model .meta { font-size: 0.85em; opacity: 0.7; }
  .section { margin-top: 16px; }
  .dep-item { padding: 4px 8px; font-size: 13px; border-bottom: 1px solid var(--vscode-widget-border); }
  .empty { opacity: 0.6; font-style: italic; }
</style>
</head>
<body>
  <h1>Architecture — Repository #${repoId}</h1>
  <div class="section">
    <h2>Models</h2>
    ${models.length ? models.map((m: any) => `<div class="model"><h3>${esc(m.name)}</h3><div class="meta">${esc(m.model_type)} · v${m.version}</div><p>${esc(m.description || '')}</p></div>`).join('') : '<p class="empty">No architecture models generated yet.</p>'}
  </div>
  <div class="section">
    <h2>Dependencies</h2>
    ${deps.nodes ? `<p>${deps.nodes.length} nodes, ${(deps.edges || []).length} edges</p>` : '<p class="empty">No dependency data available.</p>'}
  </div>
</body>
<script>
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
</script>
</html>`;
  }
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
