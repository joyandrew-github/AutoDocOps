'use client'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { FolderGit2, Code, FileText, Boxes, Activity, CheckCircle, XCircle, Clock } from 'lucide-react'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

function StatCard({ title, value, icon: Icon, description }: { title: string; value: string | number; icon: React.ElementType; description?: string }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const health = useQuery({ queryKey: ['health'], queryFn: () => api.get('/api/v1/health') })
  const agents = useQuery({ queryKey: ['agents'], queryFn: () => api.get('/api/v1/ai/agents') })

  const healthData = health.data
  const agentList = agents.data || []

  const serviceData = healthData ? [
    { name: 'PostgreSQL', status: healthData.postgres?.status || 'unknown' },
    { name: 'Neo4j', status: healthData.neo4j?.status || 'unknown' },
    { name: 'Redis', status: healthData.redis?.status || 'unknown' },
  ] : []

  const chartData = [
    { name: 'Repos', count: 4 },
    { name: 'Functions', count: 128 },
    { name: 'Classes', count: 42 },
    { name: 'Docs', count: 18 },
    { name: 'Agents', count: agentList.length },
  ]

  const pieData = [
    { name: 'Python', value: 45 },
    { name: 'TypeScript', value: 30 },
    { name: 'JavaScript', value: 15 },
    { name: 'Other', value: 10 },
  ]

  if (health.isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Platform overview and system health</p>
        </div>
        <Badge variant={healthData?.status === 'healthy' ? 'success' : 'destructive'}>
          {healthData?.status || 'Unknown'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Repositories" value={4} icon={FolderGit2} description="Connected repos" />
        <StatCard title="Code Entities" value={170} icon={Code} description="Functions + Classes" />
        <StatCard title="Documents" value={18} icon={FileText} description="Generated docs" />
        <StatCard title="AI Agents" value={agentList.length} icon={Boxes} description="Available agents" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Platform Metrics</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Language Distribution</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4" />Service Health</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {serviceData.map(s => (
                <div key={s.name} className="flex items-center justify-between">
                  <span className="text-sm">{s.name}</span>
                  <Badge variant={s.status === 'connected' ? 'success' : 'destructive'}>
                    {s.status === 'connected' ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
                    {s.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Clock className="h-4 w-4" />Recent Jobs</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span>Push pipeline</span><Badge variant="success">Completed</Badge></div>
              <div className="flex justify-between"><span>PR Analysis #42</span><Badge variant="success">Completed</Badge></div>
              <div className="flex justify-between"><span>Doc generation</span><Badge variant="warning">Running</Badge></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>AI Agents</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              {agentList.slice(0, 5).map((a: { name: string; description: string }) => (
                <div key={a.name} className="flex justify-between items-center">
                  <span className="font-medium">{a.name.replace(/_/g, ' ')}</span>
                  <Badge variant="outline">Ready</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
