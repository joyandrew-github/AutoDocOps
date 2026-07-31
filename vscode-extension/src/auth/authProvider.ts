import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

export class AuthProvider {
  private client: ApiClient;
  private statusBarItem: vscode.StatusBarItem;
  private _onDidChangeAuth = new vscode.EventEmitter<boolean>();
  readonly onDidChangeAuth = this._onDidChangeAuth.event;
  private currentUser: any = null;

  constructor(client: ApiClient, statusBarItem: vscode.StatusBarItem) {
    this.client = client;
    this.statusBarItem = statusBarItem;
  }

  async initialize(): Promise<void> {
    this.client.loadTokens();
    if (this.client.isAuthenticated()) {
      const resp = await this.client.getMe();
      if (resp.ok) {
        this.currentUser = resp.data;
        this.updateStatusBar(true);
        this._onDidChangeAuth.fire(true);
        return;
      }
      this.client.clearTokens();
    }
    this.updateStatusBar(false);
  }

  async login(): Promise<boolean> {
    const username = await vscode.window.showInputBox({
      prompt: 'AutoDocOps Username',
      placeHolder: 'Enter your username',
    });
    if (!username) { return false; }

    const password = await vscode.window.showInputBox({
      prompt: 'AutoDocOps Password',
      password: true,
      placeHolder: 'Enter your password',
    });
    if (!password) { return false; }

    const resp = await this.client.login(username, password);
    if (resp.ok) {
      const me = await this.client.getMe();
      if (me.ok) { this.currentUser = me.data; }
      this.updateStatusBar(true);
      this._onDidChangeAuth.fire(true);
      vscode.window.showInformationMessage(`AutoDocOps: Logged in as ${username}`);
      return true;
    } else {
      vscode.window.showErrorMessage(`AutoDocOps: Login failed — ${resp.error}`);
      return false;
    }
  }

  async logout(): Promise<void> {
    await this.client.logout();
    this.currentUser = null;
    this.updateStatusBar(false);
    this._onDidChangeAuth.fire(false);
    vscode.window.showInformationMessage('AutoDocOps: Logged out');
  }

  getUser(): any {
    return this.currentUser;
  }

  private updateStatusBar(loggedIn: boolean): void {
    if (loggedIn && this.currentUser) {
      this.statusBarItem.text = `$(shield) AutoDocOps: ${this.currentUser.username}`;
      this.statusBarItem.tooltip = `Logged in as ${this.currentUser.email}`;
      this.statusBarItem.command = 'autodocops.logout';
    } else {
      this.statusBarItem.text = '$(shield) AutoDocOps: Sign In';
      this.statusBarItem.tooltip = 'Click to sign in to AutoDocOps';
      this.statusBarItem.command = 'autodocops.login';
    }
    this.statusBarItem.show();
  }
}
