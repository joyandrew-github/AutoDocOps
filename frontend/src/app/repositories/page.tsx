'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { FolderGit2, RefreshCw, GitBranch, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'

export default function RepositoriesPage() {
  const qc = useQueryClient()
  const repos = useQuery({ queryKey: ['repositories'], queryFn: () => api.get('/api/v1/repositories') })
  const ghRepos = useQuery({ queryKey: ['gh-repos'], queryFn: () => api.get('/api/v1/github/repositories?account_id=1').catch(() => []) })

  const syncMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/github/repositories/${id}/sync`, {}),
    onSuccess: () => { toast.success('Sync started'); qc.invalidateQueries({ queryKey: ['repositories'] }) },
    onError: () => toast.error('Sync failed'),
  })

  const repoList = repos.data || []
  const connectedList = ghRepos.data || []

  if (repos.isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-40" />)}
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Repository Explorer</h1>
          <p className="text-muted-foreground">Manage and explore connected repositories</p>
        </div>
        <Button variant="outline" onClick={() => qc.invalidateQueries({ queryKey: ['repositories'] })}>
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Repositories ({repoList.length})</TabsTrigger>
          <TabsTrigger value="connected">GitHub Connected ({connectedList.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-4">
          {repoList.length === 0 ? (
            <Card><CardContent className="p-8 text-center text-muted-foreground">No repositories found. Connect a repository to get started.</CardContent></Card>
          ) : repoList.map((repo: any) => (
            <Card key={repo.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                  <FolderGit2 className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle className="text-base">{repo.name}</CardTitle>
                    <CardDescription className="text-xs">{repo.url}</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {repo.default_branch && (
                    <Badge variant="outline"><GitBranch className="h-3 w-3 mr-1" />{repo.default_branch}</Badge>
                  )}
                  <Badge variant={repo.is_active ? 'success' : 'secondary'}>{repo.is_active ? 'Active' : 'Inactive'}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div><span className="text-muted-foreground">ID:</span> <span className="font-medium">{repo.id}</span></div>
                  <div><span className="text-muted-foreground">Branch:</span> <span className="font-medium">{repo.default_branch || 'N/A'}</span></div>
                  <div><span className="text-muted-foreground">Description:</span> <span className="font-medium">{repo.description || 'None'}</span></div>
                  <div>
                    <Button size="sm" variant="outline" onClick={() => syncMutation.mutate(repo.id)} disabled={syncMutation.isPending}>
                      {syncMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1" />}
                      Sync
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="connected" className="space-y-4 mt-4">
          {connectedList.length === 0 ? (
            <Card><CardContent className="p-8 text-center text-muted-foreground">No GitHub-connected repositories. Use Settings to connect.</CardContent></Card>
          ) : connectedList.map((cr: any) => (
            <Card key={cr.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">{cr.full_name}</CardTitle>
                  <CardDescription className="flex items-center gap-2 mt-1">
                    <GitBranch className="h-3 w-3" />{cr.selected_branch || cr.default_branch}
                    {cr.is_private && <Badge variant="secondary" className="text-xs">Private</Badge>}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={cr.sync_status === 'synced' ? 'success' : cr.sync_status === 'failed' ? 'destructive' : 'warning'}>
                    {cr.sync_status === 'synced' ? <CheckCircle className="h-3 w-3 mr-1" /> : cr.sync_status === 'failed' ? <XCircle className="h-3 w-3 mr-1" /> : <Clock className="h-3 w-3 mr-1" />}
                    {cr.sync_status}
                  </Badge>
                  <Badge variant={cr.auto_sync ? 'success' : 'outline'}>{cr.auto_sync ? 'Auto-sync' : 'Manual'}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-muted-foreground">
                  Last synced: {cr.last_synced_at || 'Never'}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
