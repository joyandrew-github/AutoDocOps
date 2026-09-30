'use client'
import { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  FileText,
  Download,
  Printer,
  RefreshCw,
  Loader2,
  FolderGit2,
  Sparkles,
  Copy,
  Check,
  BookOpen,
  Layers,
  Code2,
  Network,
  Boxes,
  Database,
  Terminal,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  FileCheck,
} from 'lucide-react'

function DocsContent() {
  const qc = useQueryClient()
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialRepoId = Number(searchParams.get('repoId')) || 10
  const [repoId, setRepoId] = useState<number>(initialRepoId)
  const [copied, setCopied] = useState(false)
  const [activeSection, setActiveSection] = useState<number>(0)

  // Fetch all repositories for repository selector
  const reposQuery = useQuery({
    queryKey: ['repositories'],
    queryFn: () => api.get('/api/v1/repositories'),
  })

  const repoList: any[] = reposQuery.data || []

  // Sync repoId with searchParams if present
  useEffect(() => {
    const urlRepoId = Number(searchParams.get('repoId'))
    if (urlRepoId && urlRepoId !== repoId) {
      setRepoId(urlRepoId)
    }
  }, [searchParams])

  // Select valid repo if current is not in list
  useEffect(() => {
    if (repoList.length > 0 && !repoList.some((r: any) => r.id === repoId)) {
      setRepoId(repoList[0].id)
    }
  }, [repoList, repoId])

  const currentRepo = repoList.find((r: any) => r.id === repoId)

  // Query master documentation for this repository
  const masterDocQuery = useQuery({
    queryKey: ['master-doc', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/documentation/master`),
    enabled: !!repoId,
  })

  const doc = masterDocQuery.data

  // Mutation to regenerate master documentation
  const generateMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/repositories/${repoId}/documentation/generate`, {}),
    onSuccess: (data: any) => {
      toast.success(`Master Documentation updated! 1 unified technical dossier is ready.`)
      qc.invalidateQueries({ queryKey: ['master-doc', repoId] })
      masterDocQuery.refetch()
    },
    onError: () => toast.error('Documentation generation failed'),
  })

  const handleRepoChange = (newId: number) => {
    setRepoId(newId)
    router.push(`/docs?repoId=${newId}`)
  }

  // Download as PDF (Opens print-optimized document view with auto-trigger print dialog)
  const downloadAsPDF = () => {
    const exportUrl = `http://localhost:8000/api/v1/repositories/${repoId}/documentation/master/export?format=html&print=true`
    const printWindow = window.open(exportUrl, '_blank')
    if (!printWindow) {
      // Fallback to in-page window.print
      window.print()
    }
    toast.success('Print-ready view opened. Select "Save as PDF" to save.')
  }

  // Download raw markdown file
  const downloadMarkdown = () => {
    if (!doc?.content) {
      toast.error('No documentation content to download')
      return
    }
    const filename = `${currentRepo?.name || 'repository'}_master_documentation.md`
    const blob = new Blob([doc.content], { type: 'text/markdown;charset=utf-8' })
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

  // Copy full markdown to clipboard
  const copyMarkdown = () => {
    if (!doc?.content) return
    navigator.clipboard.writeText(doc.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Complete documentation copied to clipboard')
  }

  // Smooth scroll to chapter
  const scrollToChapter = (index: number) => {
    setActiveSection(index)
    const el = document.getElementById(`chapter-${index}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const sections: any[] = doc?.sections || []

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Actions Bar */}
      <div className="no-print flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Master Project Documentation</h1>
            <Badge variant="secondary" className="text-xs bg-primary/10 text-primary border-primary/20">
              Unified Dossier
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Complete technical specification, tech stack matrix, API routes, functions, and architecture for{' '}
            <span className="font-semibold text-foreground">{currentRepo?.name || 'Repository'}</span>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Repository Selector Dropdown */}
          <div className="flex items-center gap-2 bg-card border rounded-md px-3 py-1.5 shadow-sm text-sm">
            <FolderGit2 className="h-4 w-4 text-primary shrink-0" />
            <select
              value={repoId}
              onChange={(e) => handleRepoChange(Number(e.target.value))}
              className="bg-transparent font-medium focus:outline-none cursor-pointer pr-2"
            >
              {repoList.map((r: any) => (
                <option key={r.id} value={r.id} className="bg-background text-foreground">
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          {/* Download as PDF Button */}
          <Button
            size="sm"
            onClick={downloadAsPDF}
            disabled={!doc?.content}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm flex items-center gap-1.5"
            title="Export as vector PDF via print engine"
          >
            <Printer className="h-4 w-4" />
            Download as PDF
          </Button>

          {/* Download Markdown Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={downloadMarkdown}
            disabled={!doc?.content}
            className="flex items-center gap-1.5"
            title="Download complete documentation as .md"
          >
            <Download className="h-4 w-4" />
            Download .md
          </Button>

          {/* Copy Markdown */}
          <Button
            size="sm"
            variant="outline"
            onClick={copyMarkdown}
            disabled={!doc?.content}
            title="Copy markdown text"
          >
            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </Button>

          {/* Regenerate Master Doc */}
          <Button
            size="sm"
            variant="secondary"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center gap-1.5"
          >
            {generateMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            ) : (
              <Sparkles className="h-4 w-4 text-primary" />
            )}
            {generateMutation.isPending ? 'Rebuilding...' : 'Regenerate'}
          </Button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {masterDocQuery.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="md:col-span-1 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
          <div className="md:col-span-3 space-y-4">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        </div>
      ) : !doc?.content ? (
        /* Empty State */
        <Card className="border-dashed">
          <CardContent className="p-12 text-center space-y-4">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto" />
            <div className="space-y-1">
              <h3 className="text-lg font-semibold">No Master Documentation Found</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Generate a unified, comprehensive technical dossier covering everything about{' '}
                <span className="font-semibold text-foreground">{currentRepo?.name}</span>.
              </p>
            </div>
            <Button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="gap-2"
            >
              {generateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Generate Master Project Documentation
            </Button>
          </CardContent>
        </Card>
      ) : (
        /* Main Two-Column Layout */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Sticky Table of Contents & Telemetry (lg:col-span-4) */}
          <div className="no-print lg:col-span-4 space-y-4 sticky top-6">
            {/* Quick Metadata Box */}
            <Card className="border-primary/20 shadow-sm bg-card/60 backdrop-blur-sm">
              <CardHeader className="pb-3 pt-4 px-4 border-b">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-primary" />
                  Repository Dossier Overview
                </CardTitle>
                <CardDescription className="text-xs">
                  Updated {doc.updated_at ? new Date(doc.updated_at).toLocaleString() : 'Recently'}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 bg-muted/50 rounded-lg">
                    <span className="text-muted-foreground block text-[11px]">Tracked Files</span>
                    <span className="text-sm font-bold text-foreground">
                      {currentRepo?.total_files || 'Cataloged'} files
                    </span>
                  </div>
                  <div className="p-2.5 bg-muted/50 rounded-lg">
                    <span className="text-muted-foreground block text-[11px]">Knowledge Graph</span>
                    <span className="text-sm font-bold text-primary">
                      {currentRepo?.graph_nodes || 0} entities
                    </span>
                  </div>
                  <div className="p-2.5 bg-muted/50 rounded-lg">
                    <span className="text-muted-foreground block text-[11px]">Graph Relations</span>
                    <span className="text-sm font-bold text-foreground">
                      {currentRepo?.graph_relationships || 0} edges
                    </span>
                  </div>
                  <div className="p-2.5 bg-muted/50 rounded-lg">
                    <span className="text-muted-foreground block text-[11px]">Documentation</span>
                    <span className="text-sm font-bold text-green-600 dark:text-green-400">
                      1 Master Doc
                    </span>
                  </div>
                </div>

                <div className="pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={downloadAsPDF}
                    className="w-full text-xs gap-1.5 border-blue-200 dark:border-blue-900 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50"
                  >
                    <Printer className="h-3.5 w-3.5" />
                    Download / Print as PDF
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Table of Contents Chapters */}
            <Card className="shadow-sm">
              <CardHeader className="pb-2 pt-4 px-4 border-b">
                <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center justify-between">
                  <span>Table of Contents</span>
                  <span className="font-mono text-[10px] lowercase text-primary font-normal">
                    {sections.length} chapters
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-2 max-h-[calc(100vh-320px)] overflow-y-auto space-y-0.5">
                {sections.length > 0 ? (
                  sections.map((sec: any, idx: number) => {
                    const isActive = activeSection === idx
                    return (
                      <button
                        key={sec.id || idx}
                        onClick={() => scrollToChapter(idx)}
                        className={`w-full text-left px-3 py-2 rounded-md text-xs font-medium transition-colors flex items-center justify-between group ${
                          isActive
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'text-muted-foreground hover:text-foreground hover:bg-muted/60'
                        }`}
                      >
                        <span className="truncate pr-2">{sec.title}</span>
                        <ChevronRight
                          className={`h-3 w-3 shrink-0 transition-transform ${
                            isActive ? 'text-primary-foreground' : 'opacity-0 group-hover:opacity-100'
                          }`}
                        />
                      </button>
                    )
                  })
                ) : (
                  <p className="text-xs text-muted-foreground p-3">Sections indexing...</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Full Master Document Reader (lg:col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            <Card className="border shadow-md">
              <CardHeader className="border-b bg-card pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-xl md:text-2xl font-bold flex items-center gap-2">
                      <FileCheck className="h-6 w-6 text-primary" />
                      {doc.title}
                    </CardTitle>
                    <CardDescription className="text-xs font-mono mt-1">
                      Repository ID: <code className="text-foreground">{doc.repository_id}</code> • Type:{' '}
                      <span className="text-foreground font-semibold uppercase">{doc.doc_type}</span> • Format:{' '}
                      <span className="text-foreground uppercase">{doc.format}</span>
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className="text-xs bg-muted">
                      v{doc.version || 1}.0
                    </Badge>
                    <Button size="sm" variant="ghost" onClick={copyMarkdown} title="Copy Markdown">
                      {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="p-6 md:p-8">
                {/* Render full Master Markdown Document */}
                <article className="prose dark:prose-invert max-w-none text-sm md:text-base leading-relaxed break-words
                  prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-foreground
                  prose-h1:text-2xl prose-h1:border-b prose-h1:pb-3 prose-h1:mb-6
                  prose-h2:text-xl prose-h2:border-b prose-h2:pb-2 prose-h2:mt-10 prose-h2:mb-4 prose-h2:text-primary
                  prose-h3:text-base prose-h3:mt-6 prose-h3:mb-2 prose-h3:text-foreground
                  prose-p:text-muted-foreground prose-p:leading-relaxed
                  prose-table:border prose-table:border-border prose-table:my-6 prose-table:text-xs md:prose-table:text-sm
                  prose-th:bg-muted/80 prose-th:p-2.5 prose-th:text-foreground prose-th:font-semibold prose-th:border prose-th:border-border
                  prose-td:p-2.5 prose-td:border prose-td:border-border prose-td:text-muted-foreground
                  prose-tr:even:bg-muted/20
                  prose-code:text-primary prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:text-xs
                  prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-pre:p-4 prose-pre:rounded-lg prose-pre:border prose-pre:border-border
                  prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:bg-muted/30 prose-blockquote:py-2 prose-blockquote:px-4 prose-blockquote:rounded-r prose-blockquote:italic
                  prose-li:text-muted-foreground prose-li:my-1
                  prose-hr:my-8 prose-hr:border-border">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h2: ({ node, children, ...props }) => {
                        // Extract chapter index to provide anchor id for Table of Contents
                        const text = String(children || '')
                        const match = text.match(/^(\d+)\./)
                        const chapterIdx = match ? parseInt(match[1], 10) - 1 : undefined
                        return (
                          <h2
                            id={chapterIdx !== undefined ? `chapter-${chapterIdx}` : undefined}
                            className="scroll-mt-20 group flex items-center justify-between"
                            {...props}
                          >
                            <span>{children}</span>
                            <a
                              href={`#chapter-${chapterIdx}`}
                              className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-primary text-xs"
                              title="Direct link to chapter"
                            >
                              #
                            </a>
                          </h2>
                        )
                      },
                    }}
                  >
                    {doc.content}
                  </ReactMarkdown>
                </article>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

export default function DocsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 space-y-4">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-96 w-full" />
        </div>
      }
    >
      <DocsContent />
    </Suspense>
  )
}
