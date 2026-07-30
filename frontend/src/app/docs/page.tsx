'use client'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { FileText, Download, RefreshCw, Search, Loader2 } from 'lucide-react'

export default function DocsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [repoId] = useState(1)
  const docs = useQuery({ queryKey: ['docs', repoId], queryFn: () => api.get(`/api/v1/repositories/${repoId}/documentation`).catch(() => []) })

  const generateMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/repositories/${repoId}/documentation/generate`, {}),
    onSuccess: () => { toast.success('Documentation generated'); docs.refetch() },
    onError: () => toast.error('Generation failed'),
  })

  const docList: any[] = docs.data || []
  const filtered = docList.filter((d: any) =>
    !searchTerm || d.title?.toLowerCase().includes(searchTerm.toLowerCase()) || d.doc_type?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const docTypes = [...new Set(docList.map((d: any) => d.doc_type || 'unknown'))]

  if (docs.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-8 w-48" />{[1, 2, 3].map(i => <Skeleton key={i} className="h-32" />)}</div>
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Documentation</h1>
          <p className="text-muted-foreground">Browse, search, and export generated documentation</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => docs.refetch()}><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
          <Button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
            {generateMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <FileText className="h-4 w-4 mr-1" />}
            Generate
          </Button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder="Search documentation..."
          className="w-full pl-9 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All ({filtered.length})</TabsTrigger>
          {docTypes.map(t => <TabsTrigger key={t} value={t}>{t}</TabsTrigger>)}
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-4">
          {filtered.length === 0 ? (
            <Card><CardContent className="p-8 text-center text-muted-foreground">No documentation found. Generate docs to get started.</CardContent></Card>
          ) : filtered.map((doc: any) => (
            <Card key={doc.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base flex items-center gap-2"><FileText className="h-4 w-4" />{doc.title}</CardTitle>
                  <CardDescription>{doc.summary || 'No summary available'}</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{doc.doc_type}</Badge>
                  <Button variant="ghost" size="icon"><Download className="h-4 w-4" /></Button>
                </div>
              </CardHeader>
            </Card>
          ))}
        </TabsContent>

        {docTypes.map(t => (
          <TabsContent key={t} value={t} className="space-y-4 mt-4">
            {filtered.filter((d: any) => d.doc_type === t).map((doc: any) => (
              <Card key={doc.id}>
                <CardHeader>
                  <CardTitle className="text-base">{doc.title}</CardTitle>
                  <CardDescription>{doc.summary}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
