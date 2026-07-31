import * as vscode from 'vscode';
import http from 'http';
import https from 'https';
import { URL } from 'url';

export interface ApiResponse<T = any> {
  ok: boolean;
  status: number;
  data?: T;
  error?: string;
}

export class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private context: vscode.ExtensionContext;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
  }

  private get baseUrl(): string {
    return vscode.workspace.getConfiguration('autodocops').get('serverUrl', 'http://localhost:8000');
  }

  setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
    this.context.globalState.update('autodocops.accessToken', access);
    this.context.globalState.update('autodocops.refreshToken', refresh);
  }

  loadTokens(): void {
    this.accessToken = this.context.globalState.get('autodocops.accessToken') || null;
    this.refreshToken = this.context.globalState.get('autodocops.refreshToken') || null;
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.context.globalState.update('autodocops.accessToken', undefined);
    this.context.globalState.update('autodocops.refreshToken', undefined);
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  private async request<T = any>(method: string, path: string, body?: any): Promise<ApiResponse<T>> {
    const url = new URL(path, this.baseUrl);
    const isHttps = url.protocol === 'https:';
    const lib = isHttps ? https : http;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const postData = body ? JSON.stringify(body) : undefined;

    return new Promise((resolve) => {
      const req = lib.request(
        {
          hostname: url.hostname,
          port: url.port,
          path: url.pathname + url.search,
          method,
          headers,
        },
        (res: any) => {
          let data = '';
          res.on('data', (chunk: any) => (data += chunk));
          res.on('end', () => {
            const status = res.statusCode || 0;
            if (status >= 200 && status < 300) {
              try {
                resolve({ ok: true, status, data: JSON.parse(data) });
              } catch {
                resolve({ ok: true, status, data: data as any });
              }
            } else if (status === 401 && this.refreshToken) {
              this.tryRefresh().then((refreshed) => {
                if (refreshed) {
                  this.request<T>(method, path, body).then(resolve);
                } else {
                  resolve({ ok: false, status, error: 'Authentication failed' });
                }
              });
            } else {
              let errorMsg = `HTTP ${status}`;
              try {
                const parsed = JSON.parse(data);
                errorMsg = parsed.detail || errorMsg;
              } catch { }
              resolve({ ok: false, status, error: errorMsg });
            }
          });
        }
      );

      req.on('error', (err: Error) => {
        resolve({ ok: false, status: 0, error: err.message });
      });

      if (postData) {
        req.write(postData);
      }
      req.end();
    });
  }

  private async tryRefresh(): Promise<boolean> {
    if (!this.refreshToken) { return false; }
    const resp = await this.request<any>('POST', '/api/v1/auth/refresh', {
      refresh_token: this.refreshToken,
    });
    if (resp.ok && resp.data) {
      this.setTokens(resp.data.access_token, resp.data.refresh_token);
      return true;
    }
    this.clearTokens();
    return false;
  }

  streamRequest(path: string, body: any, onChunk: (text: string) => void, onDone: () => void, onError: (err: string) => void): void {
    const url = new URL(path, this.baseUrl);
    const isHttps = url.protocol === 'https:';
    const lib = isHttps ? https : http;

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const req = lib.request(
      { hostname: url.hostname, port: url.port, path: url.pathname, method: 'POST', headers },
      (res: any) => {
        if (res.statusCode !== 200) {
          let data = '';
          res.on('data', (c: any) => (data += c));
          res.on('end', () => onError(`HTTP ${res.statusCode}: ${data}`));
          return;
        }
        res.on('data', (chunk: any) => onChunk(chunk.toString()));
        res.on('end', () => onDone());
      }
    );
    req.on('error', (err: any) => onError(err.message));
    req.write(JSON.stringify(body));
    req.end();
  }

  // ---- Auth ----
  async login(username: string, password: string): Promise<ApiResponse> {
    const resp = await this.request('POST', '/api/v1/auth/login', { username, password });
    if (resp.ok && resp.data) {
      this.setTokens(resp.data.access_token, resp.data.refresh_token);
    }
    return resp;
  }

  async logout(): Promise<void> {
    await this.request('POST', '/api/v1/auth/logout');
    this.clearTokens();
  }

  async getMe(): Promise<ApiResponse> {
    return this.request('GET', '/api/v1/auth/me');
  }

  // ---- Repositories ----
  async listRepositories(): Promise<ApiResponse> {
    return this.request('GET', '/api/v1/repositories');
  }

  async getRepository(id: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${id}`);
  }

  // ---- AI ----
  async aiChat(message: string, repoId?: number, conversationId?: string, selectedEntities?: string[]): Promise<ApiResponse> {
    return this.request('POST', '/api/v1/ai/chat', {
      message, repository_id: repoId, conversation_id: conversationId, selected_entities: selectedEntities || [],
    });
  }

  aiStream(message: string, repoId?: number, conversationId?: string, selectedEntities?: string[], onChunk?: (t: string) => void, onDone?: () => void, onError?: (e: string) => void): void {
    this.streamRequest('/api/v1/ai/stream', {
      message, repository_id: repoId, conversation_id: conversationId, selected_entities: selectedEntities || [],
    }, onChunk || (() => { }), onDone || (() => { }), onError || (() => { }));
  }

  async aiAgents(): Promise<ApiResponse> {
    return this.request('GET', '/api/v1/ai/agents');
  }

  async aiHistory(conversationId: string): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/ai/history?conversation_id=${conversationId}`);
  }

  // ---- Search ----
  async semanticSearch(query: string, repoId?: number, entityType?: string, topK?: number): Promise<ApiResponse> {
    return this.request('POST', '/api/v1/search', {
      query, repository_id: repoId, entity_type: entityType, top_k: topK || 20,
    });
  }

  // ---- Documentation ----
  async listDocumentation(repoId: number, docType?: string): Promise<ApiResponse> {
    const q = docType ? `?doc_type=${docType}` : '';
    return this.request('GET', `/api/v1/repositories/${repoId}/documentation${q}`);
  }

  async getDocumentation(docId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/documentation/${docId}`);
  }

  // ---- Architecture ----
  async listArchitecture(repoId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${repoId}/architecture`);
  }

  async getArchitecture(modelId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/architecture/${modelId}`);
  }

  async getDependencies(repoId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${repoId}/architecture/dependencies`);
  }

  // ---- Impact ----
  async analyzeImpact(repoId: number): Promise<ApiResponse> {
    return this.request('POST', `/api/v1/repositories/${repoId}/impact/analyze`);
  }

  async impactHistory(repoId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${repoId}/impact/history`);
  }

  async getRisk(repoId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${repoId}/impact/risk`);
  }

  async getEntityImpact(repoId: number, entityName: string): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${repoId}/impact/entity/${encodeURIComponent(entityName)}`);
  }

  // ---- Graph ----
  async graphStats(repoId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/v1/repositories/${repoId}/graph/statistics`);
  }

  // ---- Health ----
  async health(): Promise<ApiResponse> {
    return this.request('GET', '/api/v1/health');
  }
}
