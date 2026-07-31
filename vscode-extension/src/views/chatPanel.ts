import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

export class ChatPanel {
  public static currentPanel: ChatPanel | undefined;
  private panel: vscode.WebviewPanel;
  private client: ApiClient;
  private conversationId: string | undefined;
  private disposables: vscode.Disposable[] = [];

  private constructor(panel: vscode.WebviewPanel, client: ApiClient) {
    this.panel = panel;
    this.client = client;
    this.panel.webview.html = this.getHtml();

    this.panel.webview.onDidReceiveMessage(
      async (msg: any) => {
        switch (msg.command) {
          case 'send':
            await this.handleSend(msg.text, msg.entities);
            break;
          case 'clear':
            this.conversationId = undefined;
            break;
        }
      },
      null,
      this.disposables
    );

    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
  }

  static create(extensionUri: vscode.Uri, client: ApiClient): ChatPanel {
    if (ChatPanel.currentPanel) {
      ChatPanel.currentPanel.panel.reveal(vscode.ViewColumn.Beside);
      return ChatPanel.currentPanel;
    }
    const panel = vscode.window.createWebviewPanel(
      'autodocopsChat',
      'AutoDocOps AI Chat',
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true }
    );
    ChatPanel.currentPanel = new ChatPanel(panel, client);
    return ChatPanel.currentPanel;
  }

  sendInitialMessage(message: string): void {
    this.panel.webview.postMessage({ command: 'prefill', text: message });
    this.handleSend(message);
  }

  private async handleSend(text: string, entities?: string[]): Promise<void> {
    const repoId = vscode.workspace.getConfiguration('autodocops').get<number>('repositoryId') || undefined;
    const useStream = vscode.workspace.getConfiguration('autodocops').get<boolean>('streamResponses', true);

    this.panel.webview.postMessage({ command: 'userMessage', text });

    if (useStream) {
      let accumulated = '';
      this.panel.webview.postMessage({ command: 'streamStart' });
      this.client.aiStream(
        text,
        repoId,
        this.conversationId,
        entities,
        (chunk) => {
          accumulated += chunk;
          this.panel.webview.postMessage({ command: 'streamChunk', text: chunk, accumulated });
        },
        () => {
          this.panel.webview.postMessage({ command: 'streamEnd', text: accumulated });
        },
        (err) => {
          this.panel.webview.postMessage({ command: 'error', text: err });
        }
      );
    } else {
      const resp = await this.client.aiChat(text, repoId, this.conversationId, entities);
      if (resp.ok && resp.data) {
        this.conversationId = resp.data.conversation_id;
        this.panel.webview.postMessage({
          command: 'aiResponse',
          text: resp.data.content,
          agent: resp.data.agent_name,
        });
      } else {
        this.panel.webview.postMessage({ command: 'error', text: resp.error || 'Unknown error' });
      }
    }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root { --bg: var(--vscode-editor-background); --fg: var(--vscode-editor-foreground); --input-bg: var(--vscode-input-background); --input-border: var(--vscode-input-border); --btn: var(--vscode-button-background); --btn-fg: var(--vscode-button-foreground); }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: var(--vscode-font-family); color: var(--fg); background: var(--bg); display: flex; flex-direction: column; height: 100vh; }
  #messages { flex: 1; overflow-y: auto; padding: 12px; }
  .msg { margin-bottom: 12px; padding: 8px 12px; border-radius: 6px; max-width: 85%; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; }
  .msg.user { background: var(--btn); color: var(--btn-fg); margin-left: auto; }
  .msg.ai { background: var(--vscode-editorWidget-background, #252526); border: 1px solid var(--input-border); }
  .msg.error { background: var(--vscode-inputValidation-errorBackground, #5a1d1d); border: 1px solid var(--vscode-inputValidation-errorBorder, #be1100); }
  .agent-tag { font-size: 0.75em; opacity: 0.7; margin-bottom: 4px; }
  #input-area { display: flex; gap: 6px; padding: 8px 12px; border-top: 1px solid var(--input-border); }
  #input { flex: 1; padding: 8px; background: var(--input-bg); color: var(--fg); border: 1px solid var(--input-border); border-radius: 4px; font-family: inherit; font-size: 13px; resize: none; }
  #input:focus { outline: 1px solid var(--btn); }
  button { padding: 8px 16px; background: var(--btn); color: var(--btn-fg); border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
  button:hover { opacity: 0.9; }
  .toolbar { display: flex; justify-content: flex-end; padding: 4px 12px; gap: 8px; }
  .toolbar button { padding: 4px 8px; font-size: 11px; opacity: 0.8; }
</style>
</head>
<body>
  <div class="toolbar"><button onclick="clearChat()">Clear</button></div>
  <div id="messages"></div>
  <div id="input-area">
    <textarea id="input" rows="2" placeholder="Ask AutoDocOps AI..."></textarea>
    <button onclick="sendMessage()">Send</button>
  </div>
<script>
  const vscode = acquireVsCodeApi();
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('input');
  let streamEl = null;

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = '';
    vscode.postMessage({ command: 'send', text });
  }

  function clearChat() {
    messagesEl.innerHTML = '';
    vscode.postMessage({ command: 'clear' });
  }

  function addMsg(text, cls, agent) {
    const el = document.createElement('div');
    el.className = 'msg ' + cls;
    if (agent) {
      const tag = document.createElement('div');
      tag.className = 'agent-tag';
      tag.textContent = agent;
      el.appendChild(tag);
    }
    const content = document.createElement('div');
    content.textContent = text;
    el.appendChild(content);
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  window.addEventListener('message', (event) => {
    const msg = event.data;
    switch (msg.command) {
      case 'userMessage':
        addMsg(msg.text, 'user');
        break;
      case 'aiResponse':
        addMsg(msg.text, 'ai', msg.agent);
        break;
      case 'streamStart':
        streamEl = addMsg('', 'ai');
        break;
      case 'streamChunk':
        if (streamEl) { streamEl.lastChild.textContent = msg.accumulated; messagesEl.scrollTop = messagesEl.scrollHeight; }
        break;
      case 'streamEnd':
        streamEl = null;
        break;
      case 'error':
        addMsg(msg.text, 'error');
        break;
      case 'prefill':
        inputEl.value = msg.text;
        break;
    }
  });
</script>
</body>
</html>`;
  }

  private dispose(): void {
    ChatPanel.currentPanel = undefined;
    this.panel.dispose();
    this.disposables.forEach((d) => d.dispose());
  }
}
