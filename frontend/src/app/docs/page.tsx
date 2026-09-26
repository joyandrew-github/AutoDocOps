'use client'
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  FileText, Download, RefreshCw, Search, Loader2, FolderGit2, Sparkles,
  Copy, Check, Eye, X, BookOpen, Layers
} from 'lucide-react'

export default function DocsPage() {
  const qc = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [repoId, setRepoId] = useState<number>(10)
  const [selectedDoc, setSelectedDoc] = useState<any>(null)
  const [copied, setCopied] = useState(false)

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

  const docs = useQuery({
    queryKey: ['docs', repoId],
    queryFn: () => api.get(`/api/v1/repositories/${repoId}/documentation`).catch(() => []),
    enabled: !!repoId,
  })

  const generateMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/repositories/${repoId}/documentation/generate`, {}),
    onSuccess: (data: any) => {
      toast.success(`Documentation generated! ${data.documents_created + data.documents_updated} documents ready.`)
      qc.invalidateQueries({ queryKey: ['docs', repoId] })
    },
    onError: () => toast.error('Generation failed'),
  })

  const docList: any[] = docs.data || []
  const filtered = docList.filter((d: any) =>
    !searchTerm ||
    d.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.doc_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.file_path?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const docTypes = [...new Set(docList.map((d: any) => d.doc_type || 'other'))]
  const currentRepo = repoList.find((r: any) => r.id === repoId)

  // Download a single document as markdown
  const downloadDoc = (doc: any) => {
    const filename = `${doc.slug || doc.title.replace(/[^a-zA-Z0-9_-]/g, '_')}.md`
    const blob = new Blob([doc.content || `# ${doc.title}\n\n${doc.summary || ''}`], { type: 'text/markdown;charset=utf-8' })
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

  // Download all docs combined as a complete repository documentation bundle
  const downloadAllDocs = () => {
    if (docList.length === 0) {
      toast.error('No documentation to export')
      return
    }
    const combinedContent = docList.map(doc =>
      `---\n# ${doc.title}\n**Type:** ${doc.doc_type} | **Path:** ${doc.file_path || 'N/A'}\n\n${doc.content || doc.summary || ''}\n\n`
    ).join('\n---\n\n')

    const filename = `${currentRepo?.name || 'repository'}_complete_docs.md`
    const blob = new Blob([combinedContent], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success(`Exported complete documentation bundle (${docList.length} documents)`)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Copied to clipboard')
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Documentation Intelligence</h1>
          <p className="text-muted-foreground">Auto-generated API reference, file docs, and architectural guides for {currentRepo?.name}</p>
        </div>
        <div className="flex items-center gap-2">
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

          <Button variant="outline" size="sm" onClick={downloadAllDocs} disabled={docList.length === 0}>
            <Download className="h-4 w-4 mr-1.5" />Export All ({docList.length})
          </Button>

          <Button variant="outline" size="sm" onClick={() => docs.refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" />Refresh
          </Button>

          <Button
            size="sm"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center gap-1.5"
          >
            {generateMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Sparkles className="h-4 w-4 mr-1" />}
            Generate Docs
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder={`Search ${docList.length} documents across ${currentRepo?.name || 'repository'}...`}
          className="w-full pl-9 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      {/* Document Detail Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-4xl max-h-[88vh] flex flex-col shadow-2xl border-primary/30">
            <CardHeader className="flex flex-row items-center justify-between border-b pb-4">
              <div>
                <CardTitle className="text-xl flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  {selectedDoc.title}
                </CardTitle>
                <CardDescription className="font-mono text-xs mt-1">
                  Type: <span className="text-foreground capitalize">{selectedDoc.doc_type}</span> • Path: <code className="bg-muted px-1.5 py-0.5 rounded">{selectedDoc.file_path || 'Root'}</code>
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => copyToClipboard(selectedDoc.content || '')} title="Copy Markdown">
                  {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </Button>
                <Button size="sm" variant="outline" onClick={() => downloadDoc(selectedDoc)} title="Download Markdown File">
                  <Download className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setSelectedDoc(null)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="overflow-y-auto p-6 flex-1 space-y-4">
              <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed prose-table:border prose-table:border-border prose-th:bg-muted/50 prose-th:p-2 prose-td:p-2 prose-td:border-t prose-td:border-border prose-pre:bg-muted prose-pre:text-foreground prose-code:text-primary prose-headings:text-foreground">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {selectedDoc.content || selectedDoc.summary || 'No detailed content available for this document.'}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {docs.isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : (
        <Tabs defaultValue="all">
          <TabsList className="flex flex-wrap h-auto gap-1">
            <TabsTrigger value="all">All ({filtered.length})</TabsTrigger>
            {docTypes.map(t => (
              <TabsTrigger key={t} value={t} className="capitalize">
                {t} ({docList.filter((d: any) => d.doc_type === t).length})
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="all" className="space-y-4 mt-4">
            {filtered.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center space-y-3">
                  <FileText className="h-10 w-10 text-muted-foreground mx-auto" />
                  <p className="text-muted-foreground font-medium">No documentation found for {currentRepo?.name}.</p>
                  <Button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
                    {generateMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
                    Generate Full Documentation Now
                  </Button>
                </CardContent>
              </Card>
            ) : filtered.map((doc: any) => (
              <Card key={doc.id} className="hover:border-primary/50 transition-colors">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                      <BookOpen className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        {doc.title}
                      </CardTitle>
                      <CardDescription className="text-xs font-mono">
                        {doc.file_path || doc.entity_name || 'Repository Root'}
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="capitalize">{doc.doc_type}</Badge>
                    <Button size="sm" variant="outline" onClick={() => downloadDoc(doc)} title="Download Markdown">
                      <Download className="h-3.5 w-3.5 mr-1" />Download .md
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => setSelectedDoc(doc)}>
                      <Eye className="h-3.5 w-3.5 mr-1" />Read Full Doc
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-2">
                  <div className="text-xs text-muted-foreground line-clamp-2 bg-muted/30 p-2.5 rounded font-mono">
                    {doc.summary || doc.content?.split('\n').filter((l: string) => l.trim() && !l.startsWith('#')).slice(0, 2).join(' ') || 'Documentation generated from AST parsing.'}
                  </div>
                  <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                    <span>Target: <code className="text-foreground">{doc.file_path || 'Repository root'}</code></span>
                    <span>v{doc.version || 1} • {doc.created_at?.slice(0, 10)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {docTypes.map(t => (
            <TabsContent key={t} value={t} className="space-y-4 mt-4">
              {filtered.filter((d: any) => d.doc_type === t).map((doc: any) => (
                <Card key={doc.id} className="hover:border-primary/50 transition-colors">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <BookOpen className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{doc.title}</CardTitle>
                        <CardDescription className="text-xs font-mono">{doc.file_path || 'Root'}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" onClick={() => downloadDoc(doc)}>
                        <Download className="h-3.5 w-3.5 mr-1" />Download
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setSelectedDoc(doc)}>
                        <Eye className="h-3.5 w-3.5 mr-1" />Read
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-2">
                    <div className="text-xs text-muted-foreground line-clamp-2 bg-muted/30 p-2.5 rounded font-mono">
                      {doc.summary || doc.content?.split('\n').filter((l: string) => l.trim() && !l.startsWith('#')).slice(0, 2).join(' ') || 'Documentation generated from AST parsing.'}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  )
}
