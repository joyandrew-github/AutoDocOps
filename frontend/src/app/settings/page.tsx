'use client'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { Settings, Github, Plug, User, Globe, Loader2, Trash2 } from 'lucide-react'

export default function SettingsPage() {
  const qc = useQueryClient()
  const [connectForm, setConnectForm] = useState({ github_account_id: 1, github_repo_id: 0, full_name: '', default_branch: 'main', is_private: false })

  const ghRepos = useQuery({ queryKey: ['gh-repos'], queryFn: () => api.get('/api/v1/github/repositories?account_id=1').catch(() => []) })

  const connectMutation = useMutation({
    mutationFn: () => api.post('/api/v1/github/connect', connectForm),
    onSuccess: (data: any) => {
      toast.success(`Repository connected! Webhook secret: ${data.webhook_secret?.slice(0, 10)}...`)
      qc.invalidateQueries({ queryKey: ['gh-repos'] })
      setConnectForm(prev => ({ ...prev, full_name: '', github_repo_id: 0 }))
    },
    onError: () => toast.error('Failed to connect repository'),
  })

  const disconnectMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/github/disconnect?repo_id=${id}`, {}),
    onSuccess: () => { toast.success('Repository disconnected'); qc.invalidateQueries({ queryKey: ['gh-repos'] }) },
    onError: () => toast.error('Failed to disconnect'),
  })

  const connectedList: any[] = ghRepos.data || []

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Manage GitHub connections, API configuration, and profile</p>
      </div>

      <Tabs defaultValue="github">
        <TabsList>
          <TabsTrigger value="github"><Github className="h-4 w-4 mr-1" />GitHub</TabsTrigger>
          <TabsTrigger value="api"><Globe className="h-4 w-4 mr-1" />API Config</TabsTrigger>
          <TabsTrigger value="profile"><User className="h-4 w-4 mr-1" />Profile</TabsTrigger>
        </TabsList>

        <TabsContent value="github" className="mt-4 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Plug className="h-4 w-4" />Connect Repository</CardTitle>
              <CardDescription>Link a GitHub repository for automatic analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={(e) => { e.preventDefault(); connectMutation.mutate() }} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Repository Full Name</label>
                    <input
                      value={connectForm.full_name}
                      onChange={e => setConnectForm(prev => ({ ...prev, full_name: e.target.value }))}
                      placeholder="owner/repository"
                      className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">GitHub Repo ID</label>
                    <input
                      type="number"
                      value={connectForm.github_repo_id || ''}
                      onChange={e => setConnectForm(prev => ({ ...prev, github_repo_id: parseInt(e.target.value) || 0 }))}
                      placeholder="12345"
                      className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Default Branch</label>
                    <input
                      value={connectForm.default_branch}
                      onChange={e => setConnectForm(prev => ({ ...prev, default_branch: e.target.value }))}
                      className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    />
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={connectForm.is_private}
                        onChange={e => setConnectForm(prev => ({ ...prev, is_private: e.target.checked }))}
                        className="rounded border-input"
                      />
                      Private repository
                    </label>
                  </div>
                </div>
                <Button type="submit" disabled={connectMutation.isPending || !connectForm.full_name}>
                  {connectMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Github className="h-4 w-4 mr-1" />}
                  Connect Repository
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Connected Repositories</CardTitle>
              <CardDescription>{connectedList.length} repositories connected</CardDescription>
            </CardHeader>
            <CardContent>
              {connectedList.length === 0 ? (
                <p className="text-sm text-muted-foreground">No connected repositories yet.</p>
              ) : (
                <div className="space-y-3">
                  {connectedList.map((cr: any) => (
                    <div key={cr.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium text-sm">{cr.full_name}</div>
                        <div className="text-xs text-muted-foreground">Branch: {cr.selected_branch || cr.default_branch} • {cr.is_private ? 'Private' : 'Public'}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={cr.sync_status === 'synced' ? 'success' : 'warning'}>{cr.sync_status}</Badge>
                        <Badge variant={cr.auto_sync ? 'success' : 'outline'}>{cr.auto_sync ? 'Auto' : 'Manual'}</Badge>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => disconnectMutation.mutate(cr.id)}>
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Configuration</CardTitle>
              <CardDescription>Backend connection settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">API Base URL</label>
                <input
                  value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                  readOnly
                  className="w-full mt-1 rounded-md border border-input bg-muted px-3 py-2 text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 border rounded-lg">
                  <span className="text-muted-foreground">Health endpoint:</span>
                  <code className="block mt-1">/api/v1/health</code>
                </div>
                <div className="p-3 border rounded-lg">
                  <span className="text-muted-foreground">Webhook endpoint:</span>
                  <code className="block mt-1">/api/v1/github/webhook</code>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="profile" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>User Profile</CardTitle>
              <CardDescription>Manage your account settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Username</label>
                  <input defaultValue="admin" className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium">Email</label>
                  <input defaultValue="admin@autodocops.dev" className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
              </div>
              <Button>Save Changes</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
