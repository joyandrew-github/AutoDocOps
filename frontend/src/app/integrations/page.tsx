'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { Plug, RefreshCw, Activity, FileText, AlertTriangle, CheckCircle2, XCircle, Loader2, Unplug, Zap, Clock } from 'lucide-react'

const CONNECTOR_ICONS: Record<string, string> = {
  jira: '/integrations/jira.svg',
  azure_devops: '/integrations/azure.svg',
  gitlab: '/integrations/gitlab.svg',
  bitbucket: '/integrations/bitbucket.svg',
  slack: '/integrations/slack.svg',
  teams: '/integrations/teams.svg',
  confluence: '/integrations/confluence.svg',
  servicenow: '/integrations/servicenow.svg',
}

const CONNECTOR_COLORS: Record<string, string> = {
  jira: 'bg-blue-500/10 text-blue-500',
  azure_devops: 'bg-sky-500/10 text-sky-500',
  gitlab: 'bg-orange-500/10 text-orange-500',
  bitbucket: 'bg-blue-600/10 text-blue-600',
  slack: 'bg-purple-500/10 text-purple-500',
  teams: 'bg-violet-500/10 text-violet-500',
  confluence: 'bg-blue-400/10 text-blue-400',
  servicenow: 'bg-green-500/10 text-green-500',
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { icon: any; cls: string }> = {
    active: { icon: CheckCircle2, cls: 'bg-green-500/10 text-green-500' },
    error: { icon: XCircle, cls: 'bg-red-500/10 text-red-500' },
    pending: { icon: Clock, cls: 'bg-yellow-500/10 text-yellow-500' },
    disconnected: { icon: Unplug, cls: 'bg-gray-500/10 text-gray-500' },
    inactive: { icon: Unplug, cls: 'bg-gray-500/10 text-gray-500' },
  }
  const v = variants[status] || variants.pending
  const Icon = v.icon
  return <Badge variant="outline" className={v.cls}><Icon className="h-3 w-3 mr-1" />{status}</Badge>
}

export default function IntegrationsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState('connections')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [connectForm, setConnectForm] = useState({
    integration_type: 'jira', name: '', auth_method: 'api_key', base_url: '',
    credentials: { api_key: '' }, config: {}, repository_id: null as number | null,
  })

  const integrations = useQuery({ queryKey: ['integrations'], queryFn: () => api.get('/api/v1/integrations') })
  const connectors = useQuery({ queryKey: ['connectors'], queryFn: () => api.get('/api/v1/integrations/connectors') })
  const logs = useQuery({
    queryKey: ['integration-logs', selectedId],
    queryFn: () => selectedId ? api.get(`/api/v1/integrations/${selectedId}/logs?limit=50`) : [],
    enabled: !!selectedId,
  })
  const status = useQuery({
    queryKey: ['integration-status', selectedId],
    queryFn: () => selectedId ? api.get(`/api/v1/integrations/${selectedId}/status`) : null,
    enabled: !!selectedId,
  })

  const connectMut = useMutation({
    mutationFn: () => api.post('/api/v1/integrations/connect', connectForm),
    onSuccess: (data: any) => {
      toast.success(`Connected: ${data.name || connectForm.name}`)
      qc.invalidateQueries({ queryKey: ['integrations'] })
      setConnectForm(prev => ({ ...prev, name: '', base_url: '', credentials: { api_key: '' } }))
    },
    onError: () => toast.error('Failed to connect integration'),
  })

  const syncMut = useMutation({
    mutationFn: (id: number) => api.post('/api/v1/integrations/sync', { integration_id: id, action: 'sync' }),
    onSuccess: () => { toast.success('Sync completed'); qc.invalidateQueries({ queryKey: ['integrations'] }) },
    onError: () => toast.error('Sync failed'),
  })

  const disconnectMut = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/integrations/${id}/disconnect`, {}),
    onSuccess: () => { toast.success('Disconnected'); qc.invalidateQueries({ queryKey: ['integrations'] }) },
    onError: () => toast.error('Disconnect failed'),
  })

  const list: any[] = integrations.data || []
  const connectorList: any[] = connectors.data || []
  const logList: any[] = logs.data || []
  const statusData: any = status.data || null

  const activeCount = list.filter((i: any) => i.status === 'active').length
  const errorCount = list.filter((i: any) => i.status === 'error').length

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2"><Plug className="h-8 w-8" /> Integrations</h1>
        <p className="text-muted-foreground">Manage enterprise connectors, monitor health, and view activity logs</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{list.length}</div><p className="text-sm text-muted-foreground">Total Integrations</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-green-500">{activeCount}</div><p className="text-sm text-muted-foreground">Active</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-red-500">{errorCount}</div><p className="text-sm text-muted-foreground">Errors</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{connectorList.length}</div><p className="text-sm text-muted-foreground">Available Connectors</p></CardContent></Card>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="connections">Connections</TabsTrigger>
          <TabsTrigger value="connect">Connect New</TabsTrigger>
          <TabsTrigger value="health">Health</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        {/* Connections tab */}
        <TabsContent value="connections" className="space-y-4">
          {list.length === 0 && <Card><CardContent className="pt-6 text-center text-muted-foreground">No integrations connected yet. Go to "Connect New" to add one.</CardContent></Card>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map((i: any) => (
              <Card key={i.id} className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => { setSelectedId(i.id); setTab('health') }}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <div className={`p-2 rounded-md ${CONNECTOR_COLORS[i.integration_type] || 'bg-gray-500/10'}`}>
                        <Plug className="h-4 w-4" />
                      </div>
                      {i.name}
                    </CardTitle>
                    <StatusBadge status={i.status} />
                  </div>
                  <CardDescription>{i.integration_type} &middot; {i.auth_method}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-muted-foreground space-y-1">
                    {i.base_url && <div>URL: {i.base_url}</div>}
                    <div>Syncs: {i.sync_count || 0}</div>
                    {i.last_sync_at && <div>Last sync: {new Date(i.last_sync_at).toLocaleString()}</div>}
                    {i.last_error && <div className="text-red-400 truncate">Error: {i.last_error}</div>}
                  </div>
                  <div className="flex gap-2 mt-3">
                    <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); syncMut.mutate(i.id) }} disabled={syncMut.isPending}>
                      <RefreshCw className={`h-3 w-3 mr-1 ${syncMut.isPending ? 'animate-spin' : ''}`} />Sync
                    </Button>
                    <Button size="sm" variant="ghost" className="text-red-500" onClick={(e) => { e.stopPropagation(); disconnectMut.mutate(i.id) }}>
                      <Unplug className="h-3 w-3 mr-1" />Disconnect
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Connect new tab */}
        <TabsContent value="connect" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Connect Integration</CardTitle><CardDescription>Add a new enterprise integration connector</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Connector Type</label>
                  <select className="w-full mt-1 p-2 rounded-md border bg-background" value={connectForm.integration_type} onChange={e => setConnectForm(p => ({ ...p, integration_type: e.target.value }))}>
                    {connectorList.map((c: any) => <option key={c.type} value={c.type}>{c.display_name}</option>)}
                    {connectorList.length === 0 && <>
                      <option value="jira">Jira</option><option value="azure_devops">Azure DevOps</option><option value="gitlab">GitLab</option>
                      <option value="bitbucket">Bitbucket</option><option value="slack">Slack</option><option value="teams">Microsoft Teams</option>
                      <option value="confluence">Confluence</option><option value="servicenow">ServiceNow</option>
                    </>}
                  </select>
                </div>
                <div><label className="text-sm font-medium">Name</label><input className="w-full mt-1 p-2 rounded-md border bg-background" placeholder="My Jira Integration" value={connectForm.name} onChange={e => setConnectForm(p => ({ ...p, name: e.target.value }))} /></div>
                <div>
                  <label className="text-sm font-medium">Auth Method</label>
                  <select className="w-full mt-1 p-2 rounded-md border bg-background" value={connectForm.auth_method} onChange={e => setConnectForm(p => ({ ...p, auth_method: e.target.value }))}>
                    <option value="api_key">API Key</option><option value="oauth2">OAuth 2.0</option><option value="personal_access_token">Personal Access Token</option>
                    <option value="basic">Basic Auth</option><option value="webhook">Webhook</option>
                  </select>
                </div>
                <div><label className="text-sm font-medium">Base URL</label><input className="w-full mt-1 p-2 rounded-md border bg-background" placeholder="https://myorg.atlassian.net" value={connectForm.base_url} onChange={e => setConnectForm(p => ({ ...p, base_url: e.target.value }))} /></div>
                <div className="md:col-span-2"><label className="text-sm font-medium">API Key / Token</label><input type="password" className="w-full mt-1 p-2 rounded-md border bg-background" placeholder="Enter API key or token" value={connectForm.credentials.api_key} onChange={e => setConnectForm(p => ({ ...p, credentials: { api_key: e.target.value } }))} /></div>
              </div>
              <Button onClick={() => connectMut.mutate()} disabled={connectMut.isPending || !connectForm.name}>
                {connectMut.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Plug className="h-4 w-4 mr-2" />}
                Connect
              </Button>
            </CardContent>
          </Card>
          {/* Available connectors */}
          <Card>
            <CardHeader><CardTitle>Available Connectors</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {connectorList.map((c: any) => (
                  <div key={c.type} className={`p-4 rounded-lg border text-center ${CONNECTOR_COLORS[c.type] || ''}`}>
                    <Zap className="h-6 w-6 mx-auto mb-2" />
                    <div className="font-medium">{c.display_name}</div>
                    <div className="text-xs text-muted-foreground mt-1">{c.actions?.length || 0} actions</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Health tab */}
        <TabsContent value="health" className="space-y-4">
          {selectedId && statusData ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{statusData.name}</CardTitle>
                  <StatusBadge status={statusData.status} />
                </div>
                <CardDescription>{statusData.integration_type}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div><div className="text-2xl font-bold">{statusData.is_healthy ? 'Healthy' : 'Unhealthy'}</div><div className="text-xs text-muted-foreground">Health</div></div>
                  <div><div className="text-2xl font-bold">{statusData.uptime_pct}%</div><div className="text-xs text-muted-foreground">Uptime</div></div>
                  <div><div className="text-2xl font-bold">{statusData.sync_count}</div><div className="text-xs text-muted-foreground">Total Syncs</div></div>
                  <div><div className="text-sm">{statusData.last_sync_at ? new Date(statusData.last_sync_at).toLocaleString() : 'Never'}</div><div className="text-xs text-muted-foreground">Last Sync</div></div>
                </div>
                {statusData.last_error && <div className="mt-4 p-3 rounded bg-red-500/10 text-red-500 text-sm"><AlertTriangle className="h-4 w-4 inline mr-1" />{statusData.last_error}</div>}
              </CardContent>
            </Card>
          ) : (
            <Card><CardContent className="pt-6 text-center text-muted-foreground">Select an integration from the Connections tab to view health details.</CardContent></Card>
          )}
          {/* All integrations health overview */}
          <Card>
            <CardHeader><CardTitle>All Integrations Health</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {list.map((i: any) => (
                  <div key={i.id} className="flex items-center justify-between p-3 rounded-lg border cursor-pointer hover:bg-accent/50" onClick={() => setSelectedId(i.id)}>
                    <div className="flex items-center gap-3">
                      <div className={`p-1.5 rounded ${CONNECTOR_COLORS[i.integration_type] || ''}`}><Activity className="h-3 w-3" /></div>
                      <div><div className="font-medium">{i.name}</div><div className="text-xs text-muted-foreground">{i.integration_type}</div></div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground">{i.sync_count || 0} syncs</span>
                      <StatusBadge status={i.status} />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Activity Logs</CardTitle>
                {selectedId && <select className="p-1 rounded border bg-background text-sm" value={selectedId || ''} onChange={e => setSelectedId(Number(e.target.value))}>
                  {list.map((i: any) => <option key={i.id} value={i.id}>{i.name} ({i.integration_type})</option>)}
                </select>}
              </div>
            </CardHeader>
            <CardContent>
              {!selectedId && <p className="text-muted-foreground text-center">Select an integration to view logs.</p>}
              {selectedId && logList.length === 0 && <p className="text-muted-foreground text-center">No logs yet.</p>}
              <div className="space-y-2">
                {logList.map((l: any) => (
                  <div key={l.id} className="flex items-start gap-3 p-3 rounded-lg border text-sm">
                    <div className={`mt-0.5 ${l.status === 'success' ? 'text-green-500' : 'text-red-500'}`}>
                      {l.status === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{l.event_type}</span>
                        <span className="text-xs text-muted-foreground">{l.duration_ms ? `${l.duration_ms}ms` : ''}</span>
                      </div>
                      {l.message && <div className="text-muted-foreground mt-1">{l.message}</div>}
                      <div className="text-xs text-muted-foreground mt-1">{l.created_at ? new Date(l.created_at).toLocaleString() : ''}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
