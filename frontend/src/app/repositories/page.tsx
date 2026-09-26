'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import Link from 'next/link'
import { FolderGit2, RefreshCw, GitBranch, Clock, CheckCircle, XCircle, Loader2, Boxes, FileText, Sparkles, ArrowUpRight } from 'lucide-react'

export default function RepositoriesPage() {
  const qc = useQueryClient()
  const repos = useQuery({ queryKey: ['repositories'], queryFn: () => api.get('/api/v1/repositories') })
  const ghRepos = useQuery({ queryKey: ['gh-repos'], queryFn: () => api.get('/api/v1/github/repositories?account_id=1').catch(() => []) })

  const scanMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/api/v1/repositories/${id}/scan`, {})
      await api.post(`/api/v1/repositories/${id}/parse`, {})
      await api.post(`/api/v1/repositories/${id}/architecture/generate`, {})
    },
    onSuccess: () => {
      toast.success('Repository analyzed & architecture generated!')
      qc.invalidateQueries({ queryKey: ['repositories'] })
    },
    onError: () => toast.error('Analysis failed'),
  })

  const ghSyncMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/github/repositories/${id}/sync`, {}),
    onSuccess: () => {
      toast.success('GitHub sync completed!')
      qc.invalidateQueries({ queryKey: ['gh-repos'] })
      qc.invalidateQueries({ queryKey: ['repositories'] })
    },
    onError: () => toast.error('Sync failed'),
  })

  const repoList: any[] = repos.data || []
  const connectedList: any[] = ghRepos.data || []

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
          <p className="text-muted-foreground">Manage, explore, and run architecture intelligence across your codebases</p>
        </div>
        <Button variant="outline" onClick={() => { qc.invalidateQueries({ queryKey: ['repositories'] }); qc.invalidateQueries({ queryKey: ['gh-repos'] }) }}>
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
            <Card><CardContent className="p-8 text-center text-muted-foreground">No repositories found. Connect a repository in Settings to get started.</CardContent></Card>
          ) : repoList.map((repo: any) => (
            <Card key={repo.id} className="hover:border-primary/50 transition-colors">
              <CardHeader className="flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <FolderGit2 className="h-6 w-6" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{repo.name}</CardTitle>
                    <CardDescription className="text-xs font-mono">{repo.url}</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {repo.default_branch && (
                    <Badge variant="outline"><GitBranch className="h-3 w-3 mr-1" />{repo.default_branch}</Badge>
                  )}
                  <Badge variant={repo.is_active ? 'default' : 'secondary'}>{repo.is_active ? 'Active' : 'Inactive'}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2 border-t text-sm">
                  <div className="flex items-center gap-6 text-muted-foreground text-xs">
                    <span>ID: <strong className="text-foreground">{repo.id}</strong></span>
                    <span>Path: <code className="text-foreground bg-muted px-1.5 py-0.5 rounded">{repo.local_path}</code></span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => scanMutation.mutate(repo.id)}
                      disabled={scanMutation.isPending}
                      className="flex items-center gap-1"
                    >
                      {scanMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                      Analyze & Parse
                    </Button>

                    <Link href={`/architecture`}>
                      <Button size="sm" variant="secondary" className="flex items-center gap-1">
                        <Boxes className="h-3.5 w-3.5" />
                        Architecture
                        <ArrowUpRight className="h-3 w-3" />
                      </Button>
                    </Link>

                    <Link href={`/docs`}>
                      <Button size="sm" variant="secondary" className="flex items-center gap-1">
                        <FileText className="h-3.5 w-3.5" />
                        Docs
                        <ArrowUpRight className="h-3 w-3" />
                      </Button>
                    </Link>
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
                  <Badge variant={cr.sync_status === 'synced' ? 'default' : cr.sync_status === 'failed' ? 'destructive' : 'outline'}>
                    {cr.sync_status === 'synced' ? <CheckCircle className="h-3 w-3 mr-1" /> : cr.sync_status === 'failed' ? <XCircle className="h-3 w-3 mr-1" /> : <Clock className="h-3 w-3 mr-1" />}
                    {cr.sync_status}
                  </Badge>
                  <Badge variant={cr.auto_sync ? 'default' : 'outline'}>{cr.auto_sync ? 'Auto-sync' : 'Manual'}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                  <div>
                    Last synced: {cr.last_synced_at || 'Never'}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => ghSyncMutation.mutate(cr.id)} disabled={ghSyncMutation.isPending}>
                      {ghSyncMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1" />}
                      Sync Now
                    </Button>
                    <Link href="/architecture">
                      <Button size="sm" variant="secondary">View Architecture</Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
