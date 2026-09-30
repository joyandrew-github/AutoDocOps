'use client'
import { useState, useCallback, useMemo, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import {
  Share2,
  Info,
  RefreshCw,
  FolderGit2,
  Sparkles,
  Download,
  Filter,
  FileCode2,
  Folder,
  Boxes,
  Code2,
  Cpu,
  Package,
  Layers,
  CheckCircle2,
  ArrowRight,
  ExternalLink,
  Search,
  Trash2,
  Layers3,
  Check,
} from 'lucide-react'

// Color theme mappings per node label
const LABEL_THEMES: Record<string, { bg: string; border: string; text: string; badge: string; icon: any }> = {
  Repository: { bg: '#1e1b4b', border: '#6366f1', text: '#e0e7ff', badge: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30', icon: FolderGit2 },
  Directory: { bg: '#451a03', border: '#f59e0b', text: '#fef3c7', badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: Folder },
  File: { bg: '#064e3b', border: '#10b981', text: '#ecfdf5', badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: FileCode2 },
  Function: { bg: '#164e63', border: '#06b6d4', text: '#ecfeff', badge: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30', icon: Code2 },
  Class: { bg: '#581c87', border: '#a855f7', text: '#faf5ff', badge: 'bg-purple-500/20 text-purple-400 border-purple-500/30', icon: Boxes },
  Dependency: { bg: '#881337', border: '#f43f5e', text: '#fff1f2', badge: 'bg-rose-500/20 text-rose-400 border-rose-500/30', icon: Package },
  Framework: { bg: '#7c2d12', border: '#f97316', text: '#fff7ed', badge: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: Cpu },
  ProgrammingLanguage: { bg: '#134e4a', border: '#14b8a6', text: '#f0fdfa', badge: 'bg-teal-500/20 text-teal-400 border-teal-500/30', icon: Layers },
  Import: { bg: '#3b0764', border: '#8b5cf6', text: '#f5f3ff', badge: 'bg-violet-500/20 text-violet-400 border-violet-500/30', icon: ArrowRight },
  Variable: { bg: '#0f172a', border: '#64748b', text: '#f8fafc', badge: 'bg-slate-500/20 text-slate-400 border-slate-500/30', icon: Code2 },
}

const DEFAULT_THEME = { bg: '#18181b', border: '#71717a', text: '#f4f4f5', badge: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30', icon: Share2 }

function layoutSubgraph(subgraphData: any, activeFilter: string): { nodes: Node[]; edges: Edge[] } {
  if (!subgraphData || !subgraphData.nodes || subgraphData.nodes.length === 0) {
    return { nodes: [], edges: [] }
  }

  const rawNodes = subgraphData.nodes.filter((n: any) => {
    if (activeFilter === 'ALL') return true
    return n.label === activeFilter || n.label === 'Repository'
  })

  const nodeMap = new Map<string, any>()
  rawNodes.forEach((n: any) => nodeMap.set(n.id, n))

  // Categorize nodes by tier for concentric rings layout
  const centerNodes: any[] = []
  const ring1Nodes: any[] = [] // Directory, Framework, Language
  const ring2Nodes: any[] = [] // File
  const ring3Nodes: any[] = [] // Function, Dependency, Import, Variable, Class

  rawNodes.forEach((n: any) => {
    const lbl = n.label
    if (lbl === 'Repository') centerNodes.push(n)
    else if (['Directory', 'Framework', 'ProgrammingLanguage'].includes(lbl)) ring1Nodes.push(n)
    else if (lbl === 'File') ring2Nodes.push(n)
    else ring3Nodes.push(n)
  })

  const cx = 500
  const cy = 400

  const flowNodes: Node[] = []

  // Place center nodes
  centerNodes.forEach((n, idx) => {
    const theme = LABEL_THEMES[n.label] || DEFAULT_THEME
    flowNodes.push({
      id: n.id,
      data: { ...n, displayName: n.name || n.id },
      position: { x: cx - 90, y: cy - 30 + idx * 70 },
      style: {
        background: theme.bg,
        color: theme.text,
        border: `2px solid ${theme.border}`,
        borderRadius: 12,
        padding: '12px 18px',
        fontSize: 13,
        fontWeight: 600,
        boxShadow: `0 0 20px ${theme.border}44`,
        width: 180,
        textAlign: 'center',
      },
    })
  })

  // Place Ring 1
  const r1Radius = 240
  ring1Nodes.forEach((n, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(ring1Nodes.length, 1) - Math.PI / 2
    const theme = LABEL_THEMES[n.label] || DEFAULT_THEME
    flowNodes.push({
      id: n.id,
      data: { ...n, displayName: n.name || n.id },
      position: { x: cx + r1Radius * Math.cos(angle) - 75, y: cy + r1Radius * Math.sin(angle) - 25 },
      style: {
        background: theme.bg,
        color: theme.text,
        border: `1.5px solid ${theme.border}`,
        borderRadius: 10,
        padding: '8px 14px',
        fontSize: 12,
        fontWeight: 500,
        boxShadow: `0 4px 12px ${theme.border}22`,
        maxWidth: 160,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      },
    })
  })

  // Place Ring 2 (Files)
  const r2Radius = 450
  ring2Nodes.forEach((n, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(ring2Nodes.length, 1)
    const theme = LABEL_THEMES[n.label] || DEFAULT_THEME
    flowNodes.push({
      id: n.id,
      data: { ...n, displayName: n.name || n.id },
      position: { x: cx + r2Radius * Math.cos(angle) - 70, y: cy + r2Radius * Math.sin(angle) - 20 },
      style: {
        background: theme.bg,
        color: theme.text,
        border: `1.5px solid ${theme.border}`,
        borderRadius: 8,
        padding: '6px 12px',
        fontSize: 11,
        maxWidth: 150,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      },
    })
  })

  // Place Ring 3 (Entities / Dependencies)
  const r3Radius = 660
  ring3Nodes.forEach((n, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(ring3Nodes.length, 1) + 0.1
    const theme = LABEL_THEMES[n.label] || DEFAULT_THEME
    flowNodes.push({
      id: n.id,
      data: { ...n, displayName: n.name || n.id },
      position: { x: cx + r3Radius * Math.cos(angle) - 60, y: cy + r3Radius * Math.sin(angle) - 18 },
      style: {
        background: theme.bg,
        color: theme.text,
        border: `1px solid ${theme.border}`,
        borderRadius: 6,
        padding: '5px 10px',
        fontSize: 11,
        maxWidth: 140,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      },
    })
  })

  // Process edges
  const flowEdges: Edge[] = []
  const rawEdges = subgraphData.edges || []
  rawEdges.forEach((e: any, idx: number) => {
    if (nodeMap.has(e.source) && nodeMap.has(e.target)) {
      flowEdges.push({
        id: `e-${idx}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        label: e.type,
        animated: ['DEPENDS_ON', 'USES', 'IMPORTS', 'CALLS'].includes(e.type),
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#64748b',
          width: 15,
          height: 15,
        },
        style: {
          stroke: '#475569',
          strokeWidth: 1.5,
        },
        labelStyle: {
          fill: '#94a3b8',
          fontSize: 9,
          fontWeight: 500,
        },
        labelBgStyle: {
          fill: '#0f172a',
          fillOpacity: 0.85,
        },
        labelBgPadding: [3, 2],
        labelBgBorderRadius: 4,
      })
    }
  })

  return { nodes: flowNodes, edges: flowEdges }
}

function GraphContent() {
  const qc = useQueryClient()
  const searchParams = useSearchParams()
  const urlRepoId = searchParams.get('repoId') ? Number(searchParams.get('repoId')) : null

  const [repoId, setRepoId] = useState<number>(urlRepoId || 9)
  const [activeFilter, setActiveFilter] = useState<string>('ALL')
  const [selectedNode, setSelectedNode] = useState<any | null>(null)

  // 1. Fetch repositories
  const reposQuery = useQuery({
    queryKey: ['repositories'],
    queryFn: () => api.get('/api/v1/repositories'),
  })

  const repoList: any[] = reposQuery.data || []

  // Ensure selected repoId is valid
  useEffect(() => {
    if (urlRepoId && repoList.some((r: any) => r.id === urlRepoId)) {
      setRepoId(urlRepoId)
    } else if (repoList.length > 0 && !repoList.some((r: any) => r.id === repoId)) {
      setRepoId(repoList[0].id)
    }
  }, [repoList, repoId, urlRepoId])

  const currentRepo = repoList.find((r: any) => r.id === repoId)

  // 2. Fetch specific repository graph statistics
  const statsQuery = useQuery({
    queryKey: ['graph-statistics', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/graph/statistics`).catch(() => null),
    enabled: !!repoId,
  })

  // 3. Fetch specific visual subgraph
  const subgraphQuery = useQuery({
    queryKey: ['graph-subgraph', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/graph/subgraph?limit=85`).catch(() => null),
    enabled: !!repoId,
  })

  // 4. Fetch status of all repositories
  const repoStatusQuery = useQuery({
    queryKey: ['graph-repositories-status'],
    queryFn: () => api.get('/api/v1/graph/repositories-status').catch(() => []),
  })

  // 5. Fetch neighbors when a node is selected
  const neighborsQuery = useQuery({
    queryKey: ['graph-neighbors', repoId, selectedNode?.element_id],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/graph/neighbors/${selectedNode.element_id}`),
    enabled: !!repoId && !!selectedNode?.element_id,
  })

  // 6. Fetch connected files analytics
  const connectedFilesQuery = useQuery({
    queryKey: ['graph-connected-files', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/graph/analytics/connected-files?limit=8`).catch(() => []),
    enabled: !!repoId,
  })

  // Mutation: Sync this specific repository
  const syncSpecificMutation = useMutation({
    mutationFn: (clearExisting: boolean = false) =>
      api.post(`/api/v1/repositories/${repoId}/graph/sync?clear_existing=${clearExisting}`, {}),
    onSuccess: (data: any) => {
      toast.success(
        `Specific Graph Built for ${currentRepo?.name}! +${data.nodes_created} nodes, +${data.relationships_created} rels in ${data.duration_seconds}s`
      )
      qc.invalidateQueries({ queryKey: ['graph-statistics', repoId] })
      qc.invalidateQueries({ queryKey: ['graph-subgraph', repoId] })
      qc.invalidateQueries({ queryKey: ['graph-connected-files', repoId] })
      qc.invalidateQueries({ queryKey: ['graph-repositories-status'] })
    },
    onError: () => toast.error('Failed to build graph for this repository'),
  })

  // Mutation: Sync all repositories
  const syncAllMutation = useMutation({
    mutationFn: (clearExisting: boolean = false) =>
      api.post(`/api/v1/graph/sync-all?clear_existing=${clearExisting}`, {}),
    onSuccess: (data: any) => {
      toast.success(`Successfully built specific knowledge graphs for all ${data.total_repositories} repositories!`)
      qc.invalidateQueries({ queryKey: ['graph-statistics'] })
      qc.invalidateQueries({ queryKey: ['graph-subgraph'] })
      qc.invalidateQueries({ queryKey: ['graph-repositories-status'] })
    },
    onError: () => toast.error('Failed to build graphs for all repositories'),
  })

  // Mutation: Clear specific repository graph
  const clearSpecificMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/repositories/${repoId}/graph/clear`, {}),
    onSuccess: (data: any) => {
      toast.info(`Cleared ${data.nodes_deleted} nodes for ${currentRepo?.name}. Ready for clean rebuild.`)
      qc.invalidateQueries({ queryKey: ['graph-statistics', repoId] })
      qc.invalidateQueries({ queryKey: ['graph-subgraph', repoId] })
      qc.invalidateQueries({ queryKey: ['graph-repositories-status'] })
      setSelectedNode(null)
    },
    onError: () => toast.error('Failed to clear graph'),
  })

  // Build ReactFlow nodes & edges
  const { nodes: computedNodes, edges: computedEdges } = useMemo(() => {
    return layoutSubgraph(subgraphQuery.data, activeFilter)
  }, [subgraphQuery.data, activeFilter])

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  useEffect(() => {
    setNodes(computedNodes)
    setEdges(computedEdges)
  }, [computedNodes, computedEdges, setNodes, setEdges])

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node.data)
  }, [])

  const statsData = statsQuery.data
  const nodeLabels = statsData?.node_labels || []
  const relTypes = statsData?.relationship_types || []

  // Download graph json
  const exportGraph = () => {
    if (!subgraphQuery.data) {
      toast.error('No graph data available to export')
      return
    }
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(subgraphQuery.data, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `${currentRepo?.name || 'repository'}_knowledge_graph.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    toast.success('Knowledge Graph exported as JSON')
  }

  // Filter labels available in dataset
  const filterOptions = useMemo(() => {
    const list = ['ALL', 'Repository', 'File', 'Directory', 'Dependency', 'Function', 'ProgrammingLanguage', 'Framework', 'Import']
    return list.filter((l) => l === 'ALL' || nodeLabels.some((nl: any) => nl.label === l))
  }, [nodeLabels])

  const allRepoStatuses: any[] = repoStatusQuery.data || []

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden">
      {/* Top Action Bar */}
      <div className="border-b bg-card/60 backdrop-blur px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <Share2 className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight">Repository Knowledge Graph</h1>
              <Badge variant="outline" className="text-xs bg-indigo-500/10 text-indigo-400 border-indigo-500/20">
                Isolated Graph • #{repoId}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Deep architecture topology & entity graph for{' '}
              <span className="font-semibold text-foreground">{currentRepo?.name || 'Repository'}</span>
            </p>
          </div>
        </div>

        {/* Repository selector and action buttons */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Repo dropdown */}
          <div className="flex items-center gap-2 bg-background border rounded-lg px-3 py-1.5 shadow-sm">
            <FolderGit2 className="h-4 w-4 text-primary" />
            <select
              value={repoId}
              onChange={(e) => {
                setRepoId(Number(e.target.value))
                setSelectedNode(null)
              }}
              className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
            >
              {repoList.map((r: any) => (
                <option key={r.id} value={r.id} className="bg-card text-foreground">
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          {/* Build This Specific Graph */}
          <Button
            size="sm"
            onClick={() => syncSpecificMutation.mutate(false)}
            disabled={syncSpecificMutation.isPending}
            className="flex items-center gap-1.5 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
          >
            {syncSpecificMutation.isPending ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            {syncSpecificMutation.isPending ? 'Building Graph...' : 'Build This Graph'}
          </Button>

          {/* Clean Rebuild option */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncSpecificMutation.mutate(true)}
            disabled={syncSpecificMutation.isPending}
            title="Wipe previous nodes and rebuild from scratch"
            className="text-xs"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1" />
            Clean Rebuild
          </Button>

          {/* Build All Graphs button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncAllMutation.mutate(false)}
            disabled={syncAllMutation.isPending}
            className="flex items-center gap-1.5"
          >
            {syncAllMutation.isPending ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Layers3 className="h-3.5 w-3.5 text-primary" />
            )}
            Build All Graphs
          </Button>

          {/* Export Button */}
          <Button variant="outline" size="sm" onClick={exportGraph} className="flex items-center gap-1.5">
            <Download className="h-3.5 w-3.5" />
            Export
          </Button>

          {/* Refresh Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              qc.invalidateQueries({ queryKey: ['graph-statistics', repoId] })
              qc.invalidateQueries({ queryKey: ['graph-subgraph', repoId] })
              qc.invalidateQueries({ queryKey: ['graph-connected-files', repoId] })
              qc.invalidateQueries({ queryKey: ['graph-repositories-status'] })
            }}
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Graph Canvas & Filter Bar */}
        <div className="flex-1 flex flex-col relative bg-dot-grid">
          {/* Filter Pills Bar */}
          <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-1.5 bg-background/90 backdrop-blur p-1.5 rounded-lg border shadow-sm">
            <span className="text-xs font-semibold px-2 text-muted-foreground flex items-center gap-1">
              <Filter className="h-3 w-3" /> Filter:
            </span>
            {filterOptions.map((opt) => {
              return (
                <button
                  key={opt}
                  onClick={() => setActiveFilter(opt)}
                  className={`text-xs px-2.5 py-1 rounded-md transition-all font-medium ${
                    activeFilter === opt
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  {opt}
                </button>
              )
            })}
          </div>

          {/* Canvas Stats Pill */}
          <div className="absolute top-3 right-3 z-10 flex items-center gap-3 bg-background/90 backdrop-blur px-3 py-1.5 rounded-lg border text-xs text-muted-foreground shadow-sm">
            <span>
              Repository: <strong className="text-foreground">{currentRepo?.name}</strong>
            </span>
            <span>•</span>
            <span>
              Nodes: <strong className="text-foreground">{nodes.length}</strong>
            </span>
            <span>•</span>
            <span>
              Edges: <strong className="text-foreground">{edges.length}</strong>
            </span>
          </div>

          {/* ReactFlow Viewport */}
          <div className="flex-1 w-full h-full">
            {subgraphQuery.isLoading ? (
              <div className="flex flex-col items-center justify-center h-full space-y-3">
                <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Loading Knowledge Graph from Neo4j for {currentRepo?.name}...</p>
              </div>
            ) : nodes.length > 0 ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                fitView
                fitViewOptions={{ padding: 0.15 }}
                minZoom={0.1}
                maxZoom={2.5}
              >
                <Controls className="bg-card border text-foreground" />
                <Background color="#334155" gap={20} size={1} />
                <MiniMap
                  nodeColor={(n: any) => {
                    const theme = LABEL_THEMES[n.data?.label]
                    return theme ? theme.border : '#64748b'
                  }}
                  className="bg-card border rounded-lg overflow-hidden shadow-lg"
                  maskColor="rgba(0, 0, 0, 0.65)"
                />
              </ReactFlow>
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-8 text-center space-y-4">
                <div className="p-4 rounded-full bg-primary/10 text-primary">
                  <Share2 className="h-10 w-10" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">No Graph Built For {currentRepo?.name} Yet</h3>
                  <p className="text-sm text-muted-foreground max-w-md mt-1">
                    Click "Build This Graph" to parse AST entities, dependencies, files, and relationships into a dedicated graph for this repository.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Button onClick={() => syncSpecificMutation.mutate(false)} disabled={syncSpecificMutation.isPending}>
                    {syncSpecificMutation.isPending ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4 mr-2" />
                    )}
                    Build Knowledge Graph for {currentRepo?.name}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Inspection & Analytics Drawer */}
        <div className="w-80 md:w-96 border-l bg-card flex flex-col overflow-hidden">
          <Tabs defaultValue="overview" className="flex-1 flex flex-col">
            <div className="border-b px-4 py-2">
              <TabsList className="grid grid-cols-3 w-full">
                <TabsTrigger value="overview" className="text-xs">
                  Overview
                </TabsTrigger>
                <TabsTrigger value="repositories" className="text-xs">
                  Repositories
                </TabsTrigger>
                <TabsTrigger value="inspector" className="text-xs">
                  Inspector
                </TabsTrigger>
              </TabsList>
            </div>

            {/* TAB 1: OVERVIEW */}
            <TabsContent value="overview" className="flex-1 overflow-y-auto p-4 space-y-4 m-0">
              {/* Metric Cards */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-muted/40 border rounded-lg">
                  <p className="text-xs text-muted-foreground">Total Nodes</p>
                  <p className="text-2xl font-bold tracking-tight text-primary mt-1">
                    {statsData?.total_nodes || 0}
                  </p>
                </div>
                <div className="p-3 bg-muted/40 border rounded-lg">
                  <p className="text-xs text-muted-foreground">Relationships</p>
                  <p className="text-2xl font-bold tracking-tight text-emerald-400 mt-1">
                    {statsData?.total_relationships || 0}
                  </p>
                </div>
              </div>

              {/* Node Labels Breakdown */}
              <Card>
                <CardHeader className="p-3 pb-1">
                  <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
                    <span>Node Types ({nodeLabels.length})</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 space-y-1.5">
                  {nodeLabels.map((l: any) => {
                    const theme = LABEL_THEMES[l.label] || DEFAULT_THEME
                    const IconComponent = theme.icon
                    return (
                      <div
                        key={l.label}
                        onClick={() => setActiveFilter(l.label)}
                        className="flex items-center justify-between p-1.5 rounded-md hover:bg-muted/60 transition cursor-pointer text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <IconComponent className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="font-medium">{l.label}</span>
                        </div>
                        <Badge variant="outline" className={`text-xs ${theme.badge}`}>
                          {l.count}
                        </Badge>
                      </div>
                    )
                  })}
                </CardContent>
              </Card>

              {/* Relationship Types Breakdown */}
              <Card>
                <CardHeader className="p-3 pb-1">
                  <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Relationships ({relTypes.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 space-y-1.5">
                  {relTypes.map((r: any) => (
                    <div key={r.type} className="flex items-center justify-between p-1.5 rounded text-xs font-mono">
                      <span className="text-muted-foreground">{r.type}</span>
                      <Badge variant="secondary" className="text-xs">
                        {r.count}
                      </Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Most Connected Files */}
              <Card>
                <CardHeader className="p-3 pb-1">
                  <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <FileCode2 className="h-3.5 w-3.5 text-primary" /> Most Connected Files
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 space-y-2">
                  {connectedFilesQuery.data && connectedFilesQuery.data.length > 0 ? (
                    connectedFilesQuery.data.map((cf: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-muted/40 rounded border text-xs">
                        <div className="truncate max-w-[180px]">
                          <p className="font-medium truncate font-mono">{cf.path}</p>
                          <span className="text-[10px] text-muted-foreground uppercase">{cf.language || 'Code'}</span>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {cf.connections} rels
                        </Badge>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground italic">No file connectivity calculated yet.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB 2: REPOSITORIES MATRIX */}
            <TabsContent value="repositories" className="flex-1 overflow-y-auto p-4 space-y-3 m-0">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">All Repository Graphs</h4>
                  <p className="text-[11px] text-muted-foreground">Status across isolated graphs</p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs"
                  onClick={() => syncAllMutation.mutate(false)}
                  disabled={syncAllMutation.isPending}
                >
                  <Sparkles className="h-3 w-3 mr-1" /> Sync All
                </Button>
              </div>

              <div className="space-y-2.5">
                {allRepoStatuses.map((r: any) => {
                  const isCurrent = r.repository_id === repoId
                  return (
                    <div
                      key={r.repository_id}
                      className={`p-3 rounded-lg border transition-all ${
                        isCurrent
                          ? 'bg-primary/5 border-primary shadow-sm'
                          : 'bg-muted/30 border-muted hover:border-muted-foreground/40'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-xs text-foreground">{r.name}</span>
                            {isCurrent && (
                              <Badge variant="outline" className="text-[10px] bg-primary/10 text-primary border-primary/20">
                                Active
                              </Badge>
                            )}
                          </div>
                          <span className="text-[11px] text-muted-foreground font-mono">ID: {r.repository_id}</span>
                        </div>
                        {r.has_graph ? (
                          <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                            Built
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-[10px]">
                            Not Built
                          </Badge>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs py-1 border-t border-muted/50 text-muted-foreground font-mono">
                        <div>Nodes: <strong className="text-foreground">{r.total_nodes}</strong></div>
                        <div>Rels: <strong className="text-foreground">{r.total_relationships}</strong></div>
                      </div>

                      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-muted/50">
                        <Button
                          size="sm"
                          variant={isCurrent ? 'secondary' : 'outline'}
                          className="flex-1 h-7 text-xs"
                          onClick={() => {
                            setRepoId(r.repository_id)
                            setSelectedNode(null)
                          }}
                        >
                          {isCurrent ? 'Viewing' : 'Switch To'}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs px-2"
                          onClick={() => {
                            setRepoId(r.repository_id)
                            syncSpecificMutation.mutate(false)
                          }}
                          title="Rebuild this repository graph"
                        >
                          <RefreshCw className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </TabsContent>

            {/* TAB 3: NODE INSPECTOR */}
            <TabsContent value="inspector" className="flex-1 overflow-y-auto p-4 space-y-4 m-0">
              {selectedNode ? (
                <div className="space-y-4">
                  <div className="p-4 bg-muted/40 rounded-xl border space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        {(() => {
                          const theme = LABEL_THEMES[selectedNode.label] || DEFAULT_THEME
                          const IconComp = theme.icon
                          return (
                            <Badge variant="outline" className={`text-xs mb-1.5 flex items-center gap-1 w-fit ${theme.badge}`}>
                              <IconComp className="h-3 w-3" />
                              {selectedNode.label}
                            </Badge>
                          )
                        })()}
                        <h4 className="text-base font-bold text-foreground break-all">{selectedNode.name || selectedNode.id}</h4>
                      </div>
                    </div>

                    <div className="text-xs text-muted-foreground font-mono bg-background/60 p-2 rounded border truncate">
                      ID: {selectedNode.id}
                    </div>
                  </div>

                  {/* Properties table */}
                  <Card>
                    <CardHeader className="p-3 pb-1">
                      <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Properties
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 space-y-2 text-xs">
                      {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 ? (
                        Object.entries(selectedNode.properties).map(([k, v]: any) => {
                          if (['uid', 'name'].includes(k)) return null
                          return (
                            <div key={k} className="flex flex-col border-b border-muted/50 pb-1.5">
                              <span className="text-muted-foreground uppercase font-mono text-[10px] tracking-wider">{k}</span>
                              <span className="font-mono text-foreground break-all mt-0.5">{String(v)}</span>
                            </div>
                          )
                        })
                      ) : (
                        <p className="text-muted-foreground italic">No extra properties</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Connected Neighbors list */}
                  <Card>
                    <CardHeader className="p-3 pb-1">
                      <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Graph Neighbors ({neighborsQuery.data?.length || 0})
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 space-y-2">
                      {neighborsQuery.isLoading ? (
                        <p className="text-xs text-muted-foreground">Loading connected neighbors...</p>
                      ) : neighborsQuery.data && neighborsQuery.data.length > 0 ? (
                        neighborsQuery.data.map((nb: any, idx: number) => {
                          const nTheme = LABEL_THEMES[nb.labels?.[0]] || DEFAULT_THEME
                          return (
                            <div key={idx} className="p-2 bg-muted/30 rounded border text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <Badge variant="outline" className={`text-[10px] ${nTheme.badge}`}>
                                  {nb.labels?.[0] || 'Node'}
                                </Badge>
                                <span className="font-mono text-[10px] text-muted-foreground">{nb.relationship_type}</span>
                              </div>
                              <p className="font-medium text-foreground truncate">{nb.properties?.name || nb.properties?.path || nb.element_id}</p>
                            </div>
                          )
                        })
                      ) : (
                        <p className="text-xs text-muted-foreground italic">No direct neighbors found.</p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground space-y-2">
                  <Info className="h-8 w-8 mx-auto text-muted-foreground/60" />
                  <p className="text-sm font-medium">No Node Selected</p>
                  <p className="text-xs text-muted-foreground">Click on any node in the graph canvas to inspect its full properties, AST details, and neighbors.</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

export default function GraphPage() {
  return (
    <Suspense fallback={<div className="p-6 space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-[500px]" /></div>}>
      <GraphContent />
    </Suspense>
  )
}
