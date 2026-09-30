'use client'
import { useState, useEffect, useRef, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { Boxes, GitBranch, AlertTriangle, RefreshCw, FolderGit2, Loader2, Sparkles, Layers, Network, Download } from 'lucide-react'

function MermaidDiagram({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Remove any stray error elements created by Mermaid on document.body
    const cleanMermaidStray = () => {
      if (typeof document !== 'undefined') {
        document.querySelectorAll('div[id^="dmermaid"]').forEach(el => el.remove())
      }
    }

    if (!code || !code.trim()) {
      setSvg('')
      setError(null)
      setLoading(false)
      cleanMermaidStray()
      return
    }

    setLoading(true)
    setError(null)
    let cancelled = false

    import('mermaid').then(async (m) => {
      try {
        m.default.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
          suppressErrorRendering: true,
          flowchart: { curve: 'basis', htmlLabels: true },
        } as any)

        // Clean any stray elements before rendering
        cleanMermaidStray()

        // Validate syntax first
        const isValid = await m.default.parse(code, { suppressErrors: true }).catch(() => false)
        if (!isValid) {
          if (!cancelled) {
            cleanMermaidStray()
            setError('Diagram definition could not be parsed by Mermaid.')
            setLoading(false)
          }
          return
        }

        const id = 'mermaid_' + Math.random().toString(36).replace(/[^a-z0-9]/g, '').slice(0, 8)
        const { svg: renderedSvg } = await m.default.render(id, code)

        if (!cancelled) {
          cleanMermaidStray()
          setSvg(renderedSvg)
          setLoading(false)
        }
      } catch (err: any) {
        if (!cancelled) {
          cleanMermaidStray()
          setError(err?.message || 'Error rendering Mermaid diagram')
          setLoading(false)
        }
      }
    }).catch(err => {
      if (!cancelled) {
        cleanMermaidStray()
        setError('Failed to load Mermaid module')
        setLoading(false)
      }
    })

    return () => {
      cancelled = true
      cleanMermaidStray()
    }
  }, [code])

  if (loading) {
    return <div className="h-64 flex items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg border border-amber-500/20 bg-muted/40 space-y-2 w-full my-2">
        <div className="flex items-center gap-2 text-amber-500 text-xs font-semibold">
          <AlertTriangle className="h-4 w-4" />
          <span>Diagram Render Warning</span>
        </div>
        <p className="text-xs text-muted-foreground">{error}</p>
        <pre className="text-xs bg-background/60 p-3 rounded font-mono overflow-auto max-h-60 whitespace-pre text-foreground/80">{code}</pre>
      </div>
    )
  }

  return (
    <div
      ref={ref}
      className="overflow-auto max-h-[600px] w-full flex justify-center items-center py-4 [&>svg]:max-w-full [&>svg]:h-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}

function ArchitecturePageContent() {
  const qc = useQueryClient()
  const router = useRouter()
  const searchParams = useSearchParams()

  const reposQuery = useQuery({
    queryKey: ['repositories'],
    queryFn: () => api.get('/api/v1/repositories'),
  })

  const repoList: any[] = reposQuery.data || []

  // Initialize repoId from query param or default
  const paramRepoId = searchParams.get('repoId') ? Number(searchParams.get('repoId')) : null
  const [repoId, setRepoId] = useState<number>(paramRepoId || 9)

  useEffect(() => {
    if (paramRepoId && paramRepoId !== repoId) {
      setRepoId(paramRepoId)
    }
  }, [paramRepoId])

  useEffect(() => {
    if (repoList.length > 0 && !repoList.some((r: any) => r.id === repoId)) {
      const defaultId = repoList[0].id
      setRepoId(defaultId)
      router.replace(`/architecture?repoId=${defaultId}`)
    }
  }, [repoList, repoId, router])

  const handleRepoChange = (newId: number) => {
    setRepoId(newId)
    router.replace(`/architecture?repoId=${newId}`)
  }

  const archListQuery = useQuery({
    queryKey: ['architecture', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/architecture`).catch(() => []),
    enabled: !!repoId,
  })

  const archModels: any[] = archListQuery.data || []

  // Find models by type
  const layerModel = archModels.find((m: any) => m.model_type === 'layers')
  const depModel = archModels.find((m: any) => m.model_type === 'dependencies')
  const callModel = archModels.find((m: any) => m.model_type === 'callgraph')
  const compModel = archModels.find((m: any) => m.model_type === 'components')

  // Fetch full model details for diagrams
  const layerDetail = useQuery({
    queryKey: ['arch-model', layerModel?.id],
    queryFn: () => api.get(`/api/v1/architecture/${layerModel.id}`),
    enabled: !!layerModel?.id,
  })

  const depDetail = useQuery({
    queryKey: ['arch-model', depModel?.id],
    queryFn: () => api.get(`/api/v1/architecture/${depModel.id}`),
    enabled: !!depModel?.id,
  })

  const callDetail = useQuery({
    queryKey: ['arch-model', callModel?.id],
    queryFn: () => api.get(`/api/v1/architecture/${callModel.id}`),
    enabled: !!callModel?.id,
  })

  const compDetail = useQuery({
    queryKey: ['arch-model', compModel?.id],
    queryFn: () => api.get(`/api/v1/architecture/${compModel.id}`),
    enabled: !!compModel?.id,
  })

  const violationsQuery = useQuery({
    queryKey: ['arch-violations', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/architecture/violations`).catch(() => []),
    enabled: !!repoId,
  })

  const generateMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/repositories/${repoId}/architecture/generate`, {}),
    onSuccess: (data: any) => {
      toast.success(`Architecture generated! ${data.models_created + data.models_updated} models, ${data.diagrams_generated} diagrams`)
      qc.invalidateQueries({ queryKey: ['architecture', repoId] })
      qc.invalidateQueries({ queryKey: ['arch-model'] })
      qc.invalidateQueries({ queryKey: ['arch-violations', repoId] })
    },
    onError: () => toast.error('Failed to generate architecture'),
  })

  const currentRepo = repoList.find((r: any) => r.id === repoId)

  // Real Mermaid content from DB
  const layerMermaid = layerDetail.data?.diagrams?.find((d: any) => d.format === 'mermaid')?.content || ''
  const depMermaid = depDetail.data?.diagrams?.find((d: any) => d.format === 'mermaid')?.content || ''
  const callMermaid = callDetail.data?.diagrams?.find((d: any) => d.format === 'mermaid')?.content || ''
  const compMermaid = compDetail.data?.diagrams?.find((d: any) => d.format === 'mermaid')?.content || ''
  const layerData = layerDetail.data?.data?.layers || {}
  const violations: any[] = violationsQuery.data || []

  const downloadDiagram = (type: string, content: string, format: string = 'mmd') => {
    if (!content) {
      toast.error('No diagram content to download')
      return
    }
    const filename = `${currentRepo?.name || 'repo'}_${type}_diagram.${format}`
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success(`Downloaded ${filename}`)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Architecture Intelligence</h1>
          <p className="text-muted-foreground">Extracted architecture layers, dependency graphs, and call hierarchies for {currentRepo?.name}</p>
        </div>

        {/* Repository selector and actions */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 bg-card border rounded-md px-3 py-1.5 shadow-sm">
            <FolderGit2 className="h-4 w-4 text-primary" />
            <select
              value={repoId}
              onChange={(e) => handleRepoChange(Number(e.target.value))}
              className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
            >
              {repoList.map((r: any) => (
                <option key={r.id} value={r.id} className="bg-background text-foreground">
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => downloadDiagram('layer_architecture', layerMermaid, 'mmd')}
            disabled={!layerMermaid}
          >
            <Download className="h-4 w-4 mr-1.5" />Export Diagram
          </Button>

          <Button
            size="sm"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center gap-1.5"
          >
            {generateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {archModels.length > 0 ? 'Regenerate' : 'Generate Architecture'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              qc.invalidateQueries({ queryKey: ['architecture', repoId] })
              qc.invalidateQueries({ queryKey: ['arch-model'] })
              qc.invalidateQueries({ queryKey: ['arch-violations', repoId] })
            }}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {archModels.length === 0 && !archListQuery.isLoading && (
        <Card className="border-dashed bg-muted/30">
          <CardContent className="p-8 text-center space-y-3">
            <Boxes className="h-10 w-10 text-muted-foreground mx-auto" />
            <div>
              <h3 className="font-semibold text-lg">No architecture models generated yet</h3>
              <p className="text-sm text-muted-foreground">Click below to analyze the codebase and generate diagrams for {currentRepo?.name}.</p>
            </div>
            <Button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
              {generateMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
              Generate Architecture Now
            </Button>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="layers">
        <TabsList>
          <TabsTrigger value="layers" className="flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5" />
            Architecture Layers ({Object.keys(layerData).length})
          </TabsTrigger>
          <TabsTrigger value="dependencies" className="flex items-center gap-1.5">
            <GitBranch className="h-3.5 w-3.5" />
            Dependencies
          </TabsTrigger>
          <TabsTrigger value="callgraph" className="flex items-center gap-1.5">
            <Network className="h-3.5 w-3.5" />
            Call Graph
          </TabsTrigger>
          <TabsTrigger value="components" className="flex items-center gap-1.5">
            <Boxes className="h-3.5 w-3.5" />
            Components
          </TabsTrigger>
          <TabsTrigger value="violations" className="flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5" />
            Violations ({violations.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="layers" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary" />
                  {currentRepo?.name} — Layer Diagram
                </CardTitle>
                <CardDescription>Extracted architectural boundaries and data flow</CardDescription>
              </CardHeader>
              <CardContent>
                {layerMermaid ? (
                  <MermaidDiagram code={layerMermaid} />
                ) : (
                  <div className="p-8 text-center text-muted-foreground">Click &quot;Generate Architecture&quot; to produce diagrams.</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Layer Breakdown</CardTitle>
                <CardDescription>{currentRepo?.name} files by architectural layer</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.keys(layerData).length > 0 ? (
                    Object.entries(layerData).map(([layer, files]: any) => (
                      <div key={layer} className="p-3 bg-muted/40 rounded-lg border">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-semibold uppercase tracking-wider text-primary">{layer}</span>
                          <Badge variant="secondary">{Array.isArray(files) ? files.length : 0} files</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground space-y-0.5 max-h-36 overflow-auto">
                          {Array.isArray(files) && files.map((f: string, idx: number) => (
                            <div key={idx} className="truncate font-mono">{f}</div>
                          ))}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No layers available. Generate architecture above.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="dependencies" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-primary" />
                {currentRepo?.name} — Dependency Graph
              </CardTitle>
              <CardDescription>Module and file import dependencies extracted from source code</CardDescription>
            </CardHeader>
            <CardContent>
              {depMermaid ? (
                <MermaidDiagram code={depMermaid} />
              ) : (
                <div className="p-8 text-center text-muted-foreground">Click &quot;Generate Architecture&quot; to analyze dependencies.</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="callgraph" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-4 w-4 text-primary" />
                {currentRepo?.name} — Function Call Graph
              </CardTitle>
              <CardDescription>Function, controller, and route invocations across {currentRepo?.name}</CardDescription>
            </CardHeader>
            <CardContent>
              {callMermaid ? (
                <MermaidDiagram code={callMermaid} />
              ) : (
                <div className="p-8 text-center text-muted-foreground">Click &quot;Generate Architecture&quot; to map function call chains.</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="components" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Boxes className="h-4 w-4 text-primary" />
                {currentRepo?.name} — Logical Components
              </CardTitle>
              <CardDescription>Subsystem and module boundaries identified in {currentRepo?.name}</CardDescription>
            </CardHeader>
            <CardContent>
              {compMermaid ? (
                <MermaidDiagram code={compMermaid} />
              ) : (
                <div className="p-8 text-center text-muted-foreground">Click &quot;Generate Architecture&quot; to detect components.</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="violations" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-destructive" />
                Architecture Violations
              </CardTitle>
              <CardDescription>Boundary violations and circular dependency alerts for {currentRepo?.name}</CardDescription>
            </CardHeader>
            <CardContent>
              {violations.length > 0 ? (
                <div className="space-y-3">
                  {violations.map((v: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                      <AlertTriangle className="h-4 w-4 text-destructive mt-0.5" />
                      <div>
                        <p className="text-sm font-medium">{v.description || v.violation_type}</p>
                        <p className="text-xs text-muted-foreground mt-0.5 font-mono">{v.source_file} → {v.target_file}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center space-y-2">
                  <Badge variant="outline" className="text-emerald-500 border-emerald-500">Clean Architecture</Badge>
                  <p className="text-sm text-muted-foreground">No architecture violations or circular dependencies detected in {currentRepo?.name}.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default function ArchitecturePage() {
  return (
    <Suspense fallback={
      <div className="p-6 space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    }>
      <ArchitecturePageContent />
    </Suspense>
  )
}
