'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from 'recharts'
import { BarChart3, AlertTriangle, Shield, Download, FileWarning } from 'lucide-react'

export default function ImpactPage() {
  const [repoId] = useState(1)
  const impact = useQuery({
    queryKey: ['impact', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/impact`).catch(() => null),
  })

  const riskData = [
    { area: 'API', risk: 0.6, threshold: 0.7 },
    { area: 'Models', risk: 0.3, threshold: 0.7 },
    { area: 'Services', risk: 0.5, threshold: 0.7 },
    { area: 'Config', risk: 0.2, threshold: 0.7 },
    { area: 'Tests', risk: 0.1, threshold: 0.7 },
    { area: 'Docs', risk: 0.15, threshold: 0.7 },
  ]

  const impactByType = [
    { type: 'Breaking', count: 2 },
    { type: 'High Impact', count: 5 },
    { type: 'Medium Impact', count: 12 },
    { type: 'Low Impact', count: 28 },
    { type: 'No Impact', count: 45 },
  ]

  if (impact.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-[400px]" /></div>
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Impact Analysis</h1>
          <p className="text-muted-foreground">Risk dashboard, impact reports, and change analysis</p>
        </div>
        <Button variant="outline"><Download className="h-4 w-4 mr-1" />Export Report</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Overall Risk</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">Medium</div>
            <p className="text-xs text-muted-foreground">Score: 0.42</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Breaking Changes</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">2</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Files Affected</CardTitle>
            <FileWarning className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">47</div>
            <p className="text-xs text-muted-foreground">Across 8 modules</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Tests Needed</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">14</div>
            <p className="text-xs text-muted-foreground">Recommended tests</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="risk">
        <TabsList>
          <TabsTrigger value="risk">Risk Dashboard</TabsTrigger>
          <TabsTrigger value="reports">Impact Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="risk" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle>Risk by Area</CardTitle></CardHeader>
              <CardContent className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={riskData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="area" fontSize={12} />
                    <Radar name="Risk" dataKey="risk" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                    <Radar name="Threshold" dataKey="threshold" stroke="#ef4444" fill="none" strokeDasharray="4 4" />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Impact Distribution</CardTitle></CardHeader>
              <CardContent className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={impactByType} layout="vertical">
                    <XAxis type="number" fontSize={12} />
                    <YAxis dataKey="type" type="category" fontSize={12} width={100} />
                    <Tooltip />
                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="reports" className="mt-4 space-y-4">
          {[
            { title: 'API Endpoint Changes', risk: 'high', desc: 'Breaking changes in /api/v1/repositories endpoint signatures', files: 3 },
            { title: 'Model Schema Update', risk: 'medium', desc: 'New fields added to Repository model, backward compatible', files: 5 },
            { title: 'New GitHub Integration', risk: 'low', desc: 'New engine added, no existing code modified', files: 12 },
          ].map((r, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">{r.title}</CardTitle>
                  <CardDescription>{r.desc}</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={r.risk === 'high' ? 'destructive' : r.risk === 'medium' ? 'warning' : 'success'}>{r.risk}</Badge>
                  <Badge variant="outline">{r.files} files</Badge>
                </div>
              </CardHeader>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
