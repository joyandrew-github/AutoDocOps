import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

export class ImpactPanel {
  private panel: vscode.WebviewPanel;

  constructor(client: ApiClient) {
    this.panel = vscode.window.createWebviewPanel(
      'autodocopsImpact', 'AutoDocOps Impact Analysis', vscode.ViewColumn.One, { enableScripts: true }
    );
    this.load(client);
  }

  private async load(client: ApiClient): Promise<void> {
    const repoId = vscode.workspace.getConfiguration('autodocops').get<number>('repositoryId');
    if (!repoId) {
      this.panel.webview.html = '<html><body><h2>No repository selected.</h2></body></html>';
      return;
    }

    this.panel.webview.html = '<html><body><h2>Loading impact analysis...</h2></body></html>';

    const [historyResp, riskResp] = await Promise.all([
      client.impactHistory(repoId),
      client.getRisk(repoId),
    ]);

    const history = historyResp.ok ? historyResp.data || [] : [];
    const risk = riskResp.ok ? riskResp.data : null;

    this.panel.webview.html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  body { font-family: var(--vscode-font-family); color: var(--vscode-editor-foreground); background: var(--vscode-editor-background); padding: 16px; }
  .risk-card { padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--vscode-widget-border); background: var(--vscode-editorWidget-background); }
  .risk-level { font-size: 1.4em; font-weight: bold; text-transform: uppercase; }
  .risk-level.high, .risk-level.critical { color: #f44336; }
  .risk-level.medium { color: #ff9800; }
  .risk-level.low { color: #4caf50; }
  .score-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; margin-top: 12px; }
  .score-item { padding: 8px; background: var(--vscode-editor-background); border-radius: 4px; }
  .score-label { font-size: 0.85em; opacity: 0.7; }
  .score-value { font-size: 1.2em; font-weight: bold; }
  .history-item { padding: 10px; border-bottom: 1px solid var(--vscode-widget-border); }
  .empty { opacity: 0.6; font-style: italic; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--vscode-widget-border); }
  th { opacity: 0.7; font-size: 0.85em; }
</style></head><body>
  <h1>Impact Analysis — Repository #${repoId}</h1>
  ${risk ? `<div class="risk-card">
    <div class="risk-level ${risk.risk_level}">${esc(risk.risk_level)} Risk</div>
    <div>Score: ${risk.risk_score?.toFixed(1) || 'N/A'}</div>
    <div class="score-grid">
      <div class="score-item"><div class="score-label">Dependency</div><div class="score-value">${risk.dependency_score?.toFixed(1) || '-'}</div></div>
      <div class="score-item"><div class="score-label">API</div><div class="score-value">${risk.api_score?.toFixed(1) || '-'}</div></div>
      <div class="score-item"><div class="score-label">Cross-Module</div><div class="score-value">${risk.cross_module_score?.toFixed(1) || '-'}</div></div>
      <div class="score-item"><div class="score-label">Architecture</div><div class="score-value">${risk.architecture_score?.toFixed(1) || '-'}</div></div>
    </div>
    ${risk.summary ? `<p style="margin-top:12px">${esc(risk.summary)}</p>` : ''}
  </div>` : '<p class="empty">No risk assessment available.</p>'}
  <h2>History</h2>
  ${history.length ? `<table><tr><th>ID</th><th>Status</th><th>Changes</th><th>Affected</th><th>Risk</th><th>Created</th></tr>
    ${history.map((h: any) => `<tr><td>${h.id}</td><td>${esc(h.status)}</td><td>${h.total_changes}</td><td>${h.total_affected}</td><td class="risk-level ${h.overall_risk_level || ''}">${esc(h.overall_risk_level || '-')}</td><td>${h.created_at ? new Date(h.created_at).toLocaleString() : '-'}</td></tr>`).join('')}
  </table>` : '<p class="empty">No analyses yet.</p>'}
<script>function esc(s) { const d = document.createElement('div'); d.textContent = s||''; return d.innerHTML; }</script>
</body></html>`;
  }
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
