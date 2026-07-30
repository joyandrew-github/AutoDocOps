'use client'
import { useState, useCallback, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import ReactFlow, { Controls, Background, MiniMap, Node, Edge, useNodesState, useEdgesState } from 'reactflow'
import 'reactflow/dist/style.css'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Share2, Info, RefreshCw } from 'lucide-react'

function buildGraphData(stats: any) {
  const nodes: Node[] = []
  const edges: Edge[] = []
  const labels = stats?.node_labels || []
  const rels = stats?.relationship_types || []

  labels.forEach((l: any, i: number) => {
    const angle = (2 * Math.PI * i) / Math.max(labels.length, 1)
    nodes.push({
      id: `label-${l.label}`,
      data: { label: `${l.label} (${l.count})` },
      position: { x: 400 + 200 * Math.cos(angle), y: 300 + 200 * Math.sin(angle) },
      style: { background: 'hsl(221 83% 53%)', color: '#fff', borderRadius: 8, padding: 10, fontSize: 12, border: 'none' },
    })
  })

  rels.forEach((r: any, i: number) => {
    if (nodes.length >= 2) {
      edges.push({
        id: `edge-${i}`,
        source: nodes[i % nodes.length].id,
        target: nodes[(i + 1) % nodes.length].id,
        label: `${r.type} (${r.count})`,
        animated: true,
        style: { stroke: 'hsl(215 20% 65%)' },
      })
    }
  })

  return { nodes, edges }
}

export default function GraphPage() {
  const stats = useQuery({ queryKey: ['graph-stats'], queryFn: () => api.get('/api/v1/graph/stats').catch(() => null) })
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => buildGraphData(stats.data), [stats.data])
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const onNodeClick = useCallback((_: any, node: Node) => setSelectedNode(node), [])

  if (stats.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-[500px]" /></div>
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="border-b p-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2"><Share2 className="h-5 w-5" />Knowledge Graph</h1>
            <p className="text-sm text-muted-foreground">Interactive graph visualization</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => stats.refetch()}><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
        </div>
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
          >
            <Controls />
            <Background />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>

      <div className="hidden lg:block w-72 border-l p-4 overflow-y-auto">
        <h3 className="font-semibold text-sm mb-3">Graph Statistics</h3>
        {stats.data ? (
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Node Labels</CardTitle></CardHeader>
              <CardContent className="space-y-1">
                {(stats.data.node_labels || []).map((l: any) => (
                  <div key={l.label} className="flex justify-between text-sm">
                    <span>{l.label}</span><Badge variant="secondary">{l.count}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Relationships</CardTitle></CardHeader>
              <CardContent className="space-y-1">
                {(stats.data.relationship_types || []).map((r: any) => (
                  <div key={r.type} className="flex justify-between text-sm">
                    <span>{r.type}</span><Badge variant="secondary">{r.count}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
            {selectedNode && (
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-1"><Info className="h-3 w-3" />Selected</CardTitle></CardHeader>
                <CardContent><p className="text-sm">{String(selectedNode.data?.label)}</p></CardContent>
              </Card>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Connect Neo4j to view graph data.</p>
        )}
      </div>
    </div>
  )
}
