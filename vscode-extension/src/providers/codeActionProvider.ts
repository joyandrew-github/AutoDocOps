import * as vscode from 'vscode';

export class AutoDocOpsCodeActionProvider implements vscode.CodeActionProvider {
  static readonly providedCodeActionKinds = [vscode.CodeActionKind.QuickFix];

  provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range | vscode.Selection,
    _context: vscode.CodeActionContext,
    _token: vscode.CancellationToken
  ): vscode.CodeAction[] {
    const enabled = vscode.workspace.getConfiguration('autodocops').get<boolean>('enableInlineCodeActions', true);
    if (!enabled) { return []; }

    const actions: vscode.CodeAction[] = [];
    const line = document.lineAt(range.start.line).text;

    if (/^\s*(def |async\s+def |function |async\s+function |export\s+(default\s+)?function\s)/.test(line)) {
      const explain = new vscode.CodeAction('AutoDocOps: Explain Function', vscode.CodeActionKind.QuickFix);
      explain.command = { command: 'autodocops.explainFunction', title: 'Explain Function' };
      actions.push(explain);
    }

    if (/^\s*(class |export\s+(default\s+)?class\s)/.test(line)) {
      const explain = new vscode.CodeAction('AutoDocOps: Explain Class', vscode.CodeActionKind.QuickFix);
      explain.command = { command: 'autodocops.explainClass', title: 'Explain Class' };
      actions.push(explain);
    }

    if (!range.isEmpty) {
      const explainSel = new vscode.CodeAction('AutoDocOps: Explain Selection', vscode.CodeActionKind.QuickFix);
      explainSel.command = { command: 'autodocops.explainSelection', title: 'Explain Selection' };
      actions.push(explainSel);

      const askAi = new vscode.CodeAction('AutoDocOps: Ask AI About Selection', vscode.CodeActionKind.QuickFix);
      askAi.command = { command: 'autodocops.askAboutSelection', title: 'Ask AI' };
      actions.push(askAi);
    }

    return actions;
  }
}
