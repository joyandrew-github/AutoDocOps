'use client'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ListChecks, RefreshCw, CheckCircle, XCircle, Clock, Loader2, RotateCcw } from 'lucide-react'

const statusIcon = (status: string) => {
  switch (status) {
    case 'completed': return <CheckCircle className="h-4 w-4 text-emerald-500" />
    case 'failed': return <XCircle className="h-4 w-4 text-destructive" />
    case 'running': return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    case 'queued': return <Clock className="h-4 w-4 text-amber-500" />
    default: return <Clock className="h-4 w-4 text-muted-foreground" />
  }
}

const statusVariant = (status: string): 'success' | 'destructive' | 'warning' | 'default' | 'secondary' => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'destructive'
    case 'running': return 'default'
    case 'queued': return 'warning'
    default: return 'secondary'
  }
}

export default function JobsPage() {
  const qc = useQueryClient()
  const jobs = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.get('/api/v1/github/jobs?repo_id=1&limit=50').catch(() => []),
    refetchInterval: 5000,
  })

  const jobList: any[] = jobs.data || []
  const completedJobs = jobList.filter(j => j.status === 'completed')
  const failedJobs = jobList.filter(j => j.status === 'failed')
  const runningJobs = jobList.filter(j => j.status === 'running')
  const queuedJobs = jobList.filter(j => j.status === 'queued')

  if (jobs.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-8 w-48" />{[1, 2, 3].map(i => <Skeleton key={i} className="h-20" />)}</div>
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Pipeline Jobs</h1>
          <p className="text-muted-foreground">Background jobs, queue status, and retry history</p>
        </div>
        <Button variant="outline" onClick={() => qc.invalidateQueries({ queryKey: ['jobs'] })}><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Total Jobs</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{jobList.length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-emerald-500">Completed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-emerald-500">{completedJobs.length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-destructive">Failed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-destructive">{failedJobs.length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-amber-500">Queued / Running</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-amber-500">{queuedJobs.length + runningJobs.length}</div></CardContent>
        </Card>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All ({jobList.length})</TabsTrigger>
          <TabsTrigger value="running">Running ({runningJobs.length})</TabsTrigger>
          <TabsTrigger value="failed">Failed ({failedJobs.length})</TabsTrigger>
        </TabsList>

        {['all', 'running', 'failed'].map(tab => (
          <TabsContent key={tab} value={tab} className="mt-4 space-y-2">
            {(tab === 'all' ? jobList : tab === 'running' ? runningJobs : failedJobs).length === 0 ? (
              <Card><CardContent className="p-8 text-center text-muted-foreground">No {tab === 'all' ? '' : tab} jobs.</CardContent></Card>
            ) : (tab === 'all' ? jobList : tab === 'running' ? runningJobs : failedJobs).map((job: any) => (
              <Card key={job.id}>
                <CardContent className="flex items-center justify-between py-3 px-4">
                  <div className="flex items-center gap-3">
                    {statusIcon(job.status)}
                    <div>
                      <div className="text-sm font-medium">{job.job_type.replace(/_/g, ' ')}</div>
                      <div className="text-xs text-muted-foreground">Job #{job.id} {job.created_at ? `• ${job.created_at}` : ''}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {job.duration_seconds && <span className="text-xs text-muted-foreground">{job.duration_seconds}s</span>}
                    <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
                    {job.attempt > 0 && <Badge variant="outline" className="text-xs">Attempt {job.attempt}</Badge>}
                    {job.status === 'failed' && (
                      <Button variant="ghost" size="icon" className="h-7 w-7"><RotateCcw className="h-3 w-3" /></Button>
                    )}
                  </div>
                </CardContent>
                {job.error_message && (
                  <CardContent className="pt-0 pb-3 px-4">
                    <div className="text-xs text-destructive bg-destructive/5 p-2 rounded">{job.error_message}</div>
                  </CardContent>
                )}
              </Card>
            ))}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
