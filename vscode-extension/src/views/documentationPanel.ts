import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

export class DocumentationPanel {
  private panel: vscode.WebviewPanel;
  private client: ApiClient;
  private disposables: vscode.Disposable[] = [];

  constructor(client: ApiClient) {
    this.client = client;
    this.panel = vscode.window.createWebviewPanel(
      'autodocopsDocs', 'AutoDocOps Documentation', vscode.ViewColumn.One, { enableScripts: true }
    );
    this.panel.webview.onDidReceiveMessage(
      async (msg: any) => {
        if (msg.command === 'viewDoc') {
          await this.showDoc(msg.id);
        }
      },
      null,
      this.disposables
    );
    this.panel.onDidDispose(() => this.disposables.forEach(d => d.dispose()));
    this.loadList();
  }

  private async loadList(): Promise<void> {
    const repoId = vscode.workspace.getConfiguration('autodocops').get<number>('repositoryId');
    if (!repoId) {
      this.panel.webview.html = '<html><body><h2>No repository selected.</h2></body></html>';
      return;
    }
    const resp = await this.client.listDocumentation(repoId);
    const docs = resp.ok ? resp.data || [] : [];
    this.panel.webview.html = this.listHtml(docs, repoId);
  }

  private async showDoc(docId: number): Promise<void> {
    const resp = await this.client.getDocumentation(docId);
    if (!resp.ok) {
      vscode.window.showErrorMessage(`Failed to load doc #${docId}`);
      return;
    }
    const doc = resp.data;
    this.panel.webview.html = this.docHtml(doc);
  }

  private listHtml(docs: any[], repoId: number): string {
    return `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  body { font-family: var(--vscode-font-family); color: var(--vscode-editor-foreground); background: var(--vscode-editor-background); padding: 16px; }
  .doc-item { padding: 10px; border: 1px solid var(--vscode-widget-border); border-radius: 6px; margin-bottom: 8px; cursor: pointer; }
  .doc-item:hover { background: var(--vscode-list-hoverBackground); }
  .doc-title { font-weight: bold; }
  .doc-meta { font-size: 0.85em; opacity: 0.7; }
  .empty { opacity: 0.6; font-style: italic; }
</style></head><body>
  <h1>Documentation — Repository #${repoId}</h1>
  ${docs.length ? docs.map((d: any) => `<div class="doc-item" onclick="viewDoc(${d.id})"><div class="doc-title">${esc(d.title)}</div><div class="doc-meta">${esc(d.doc_type)} · ${esc(d.entity_type || '')} · ${esc(d.entity_name || '')}</div><div>${esc(d.summary || '')}</div></div>`).join('') : '<p class="empty">No documentation generated yet.</p>'}
<script>
  const vscode = acquireVsCodeApi();
  function viewDoc(id) { vscode.postMessage({ command: 'viewDoc', id }); }
  function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
</script>
</body></html>`;
  }

  private docHtml(doc: any): string {
    const sections = doc.sections || [];
    return `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  body { font-family: var(--vscode-font-family); color: var(--vscode-editor-foreground); background: var(--vscode-editor-background); padding: 16px; max-width: 800px; margin: 0 auto; }
  h1 { margin-bottom: 8px; }
  .meta { font-size: 0.85em; opacity: 0.7; margin-bottom: 16px; }
  .section { margin-bottom: 20px; }
  .section h2, .section h3 { margin-bottom: 6px; }
  .content { white-space: pre-wrap; line-height: 1.6; }
  button { margin-bottom: 16px; padding: 6px 12px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; }
</style></head><body>
  <button onclick="location.reload()">← Back to list</button>
  <h1>${esc(doc.title)}</h1>
  <div class="meta">${esc(doc.doc_type)} · ${esc(doc.entity_name || '')} · v${doc.version || 1}</div>
  <div class="content">${esc(doc.content || '')}</div>
  ${sections.map((s: any) => `<div class="section"><h${Math.min(s.level || 2, 4)}>${esc(s.title)}</h${Math.min(s.level || 2, 4)}><div class="content">${esc(s.content)}</div></div>`).join('')}
<script>function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }</script>
</body></html>`;
  }
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
