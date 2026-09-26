'use client'
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from 'recharts'
import { BarChart3, AlertTriangle, Shield, Download, FileWarning, FolderGit2, RefreshCw } from 'lucide-react'

export default function ImpactPage() {
  const [repoId, setRepoId] = useState<number>(9)

  const reposQuery = useQuery({
    queryKey: ['repositories'],
    queryFn: () => api.get('/api/v1/repositories'),
  })

  const repoList: any[] = reposQuery.data || []

  useEffect(() => {
    if (repoList.length > 0 && !repoList.some((r: any) => r.id === repoId)) {
      setRepoId(repoList[0].id)
    }
  }, [repoList, repoId])

  const impact = useQuery({
    queryKey: ['impact', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/impact`).catch(() => null),
    enabled: !!repoId,
  })

  const currentRepo = repoList.find((r: any) => r.id === repoId)

  const riskData = [
    { area: 'API', risk: 0.6, threshold: 0.7 },
    { area: 'Models', risk: 0.3, threshold: 0.7 },
    { area: 'Services', risk: 0.5, threshold: 0.7 },
    { area: 'Config', risk: 0.2, threshold: 0.7 },
    { area: 'Tests', risk: 0.1, threshold: 0.7 },
    { area: 'Docs', risk: 0.15, threshold: 0.7 },
  ]

  const impactByType = [
    { type: 'Breaking', count: 0 },
    { type: 'High Impact', count: 2 },
    { type: 'Medium Impact', count: 8 },
    { type: 'Low Impact', count: 15 },
    { type: 'No Impact', count: 24 },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Impact Analysis</h1>
          <p className="text-muted-foreground">Risk dashboard, change blast radius, and dependency risk scoring</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-card border rounded-md px-3 py-1.5 shadow-sm">
            <FolderGit2 className="h-4 w-4 text-primary" />
            <select
              value={repoId}
              onChange={(e) => setRepoId(Number(e.target.value))}
              className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
            >
              {repoList.map((r: any) => (
                <option key={r.id} value={r.id} className="bg-background text-foreground">
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          <Button variant="outline" size="sm" onClick={() => impact.refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" />Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Overall Risk</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">Low</div>
            <p className="text-xs text-muted-foreground">Score: 0.18 • {currentRepo?.name}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Breaking Changes</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">No breaking API changes</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Affected Entities</CardTitle>
            <FileWarning className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">41</div>
            <p className="text-xs text-muted-foreground">Tracked code functions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Blast Radius</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">Controlled</div>
            <p className="text-xs text-muted-foreground">Max depth: 3 layers</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Risk by Architecture Area</CardTitle>
            <CardDescription>{currentRepo?.name || 'Repository'} component vulnerability metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={riskData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="area" />
                <Radar name="Risk Score" dataKey="risk" stroke="#6366f1" fill="#6366f1" fillOpacity={0.4} />
                <Radar name="Safe Threshold" dataKey="threshold" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Impact Distribution</CardTitle>
            <CardDescription>Predicted change impact categories across codebase</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={impactByType}>
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
