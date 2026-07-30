'use client'
import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Boxes, GitBranch, AlertTriangle, Download } from 'lucide-react'

function MermaidDiagram({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState('')

  useEffect(() => {
    if (!code) return
    let cancelled = false
    import('mermaid').then(m => {
      m.default.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' })
      m.default.render('mermaid-' + Math.random().toString(36).slice(2), code).then(({ svg }) => {
        if (!cancelled) setSvg(svg)
      }).catch(() => { if (!cancelled) setSvg('<p class="text-red-500 text-sm">Diagram render failed</p>') })
    })
    return () => { cancelled = true }
  }, [code])

  return <div ref={ref} className="overflow-auto" dangerouslySetInnerHTML={{ __html: svg }} />
}

export default function ArchitecturePage() {
  const [repoId] = useState(1)
  const arch = useQuery({
    queryKey: ['architecture', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/architecture`).catch(() => null),
  })

  const data = arch.data

  const sampleMermaid = `graph TD
    A[API Layer] --> B[Service Layer]
    B --> C[Engine Layer]
    C --> D[Repository Layer]
    D --> E[(Database)]
    B --> F[External APIs]
    C --> G[(Neo4j)]
    C --> H[(Redis)]`

  const sampleCallGraph = `graph LR
    parse[Parser] --> analyze[Analyzer]
    analyze --> doc[Documentation]
    analyze --> arch[Architecture]
    analyze --> impact[Impact]
    doc --> export[Export]
    arch --> diagram[Diagram Gen]`

  if (arch.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-[400px]" /></div>
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Architecture Intelligence</h1>
          <p className="text-muted-foreground">Mermaid diagrams, dependency explorer, and call graph</p>
        </div>
        <Button variant="outline"><Download className="h-4 w-4 mr-1" />Export</Button>
      </div>

      <Tabs defaultValue="layers">
        <TabsList>
          <TabsTrigger value="layers">Architecture Layers</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
          <TabsTrigger value="callgraph">Call Graph</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
        </TabsList>

        <TabsContent value="layers" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Boxes className="h-4 w-4" />Architecture Diagram</CardTitle></CardHeader>
              <CardContent>
                <MermaidDiagram code={data?.diagram?.content || sampleMermaid} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Layer Summary</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(data?.layers ? Object.entries(data.layers) : [
                    ['api', ['endpoints/health.py', 'endpoints/ai.py', 'endpoints/github.py']],
                    ['service', ['repository_service.py', 'git_manager.py']],
                    ['engine', ['ai_engine/', 'github_engine/', 'architecture_engine/']],
                    ['repository', ['repository_repo.py', 'parser_repo.py', 'github_repo.py']],
                    ['model', ['user.py', 'repository.py', 'github.py', 'parser.py']],
                  ]).map(([layer, files]) => (
                    <div key={String(layer)}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium capitalize">{String(layer)}</span>
                        <Badge variant="secondary">{Array.isArray(files) ? files.length : 0} files</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">{Array.isArray(files) ? files.slice(0, 3).join(', ') : ''}{Array.isArray(files) && files.length > 3 ? '...' : ''}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="dependencies" className="mt-4">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><GitBranch className="h-4 w-4" />Dependency Explorer</CardTitle></CardHeader>
            <CardContent>
              <MermaidDiagram code={sampleMermaid} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="callgraph" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Call Graph</CardTitle></CardHeader>
            <CardContent>
              <MermaidDiagram code={sampleCallGraph} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="violations" className="mt-4">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4" />Architecture Violations</CardTitle></CardHeader>
            <CardContent>
              {data?.violations && data.violations.length > 0 ? (
                <div className="space-y-3">
                  {data.violations.map((v: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-destructive/5 rounded-lg">
                      <AlertTriangle className="h-4 w-4 text-destructive mt-0.5" />
                      <div><p className="text-sm font-medium">{v.type}</p><p className="text-xs text-muted-foreground">{v.description}</p></div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No architecture violations detected.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
