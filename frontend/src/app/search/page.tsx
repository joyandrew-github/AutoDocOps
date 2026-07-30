'use client'
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Search, Code, FileText, Boxes, Loader2, ArrowRight } from 'lucide-react'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [entityType, setEntityType] = useState<string>('all')
  const [repoId] = useState(1)

  const searchMutation = useMutation({
    mutationFn: (q: string) => api.post('/api/v1/search/semantic', { query: q, repository_id: repoId, entity_type: entityType === 'all' ? undefined : entityType, top_k: 20 }),
  })

  const results: any[] = searchMutation.data?.results || []

  const doSearch = () => {
    if (query.trim()) searchMutation.mutate(query.trim())
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Semantic Search</h1>
        <p className="text-muted-foreground">Search across your codebase using natural language</p>
      </div>

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && doSearch()}
            placeholder="Search with natural language (e.g., 'authentication handler')..."
            className="w-full pl-9 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <select
          value={entityType}
          onChange={e => setEntityType(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="all">All Types</option>
          <option value="function">Functions</option>
          <option value="class">Classes</option>
          <option value="file">Files</option>
          <option value="documentation">Documentation</option>
        </select>
        <Button onClick={doSearch} disabled={searchMutation.isPending || !query.trim()}>
          {searchMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
        </Button>
      </div>

      {searchMutation.isPending && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Searching...</div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">{results.length} results for &quot;{query}&quot;</p>
          {results.map((r: any, i: number) => (
            <Card key={i} className="hover:border-primary/50 transition-colors cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  {r.entity_type === 'function' ? <Code className="h-4 w-4 text-blue-500" /> :
                   r.entity_type === 'class' ? <Boxes className="h-4 w-4 text-purple-500" /> :
                   <FileText className="h-4 w-4 text-green-500" />}
                  <div>
                    <CardTitle className="text-sm">{r.name || r.title || 'Untitled'}</CardTitle>
                    <CardDescription className="text-xs">{r.file_path || r.description || ''}</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{r.entity_type}</Badge>
                  <Badge variant="outline">{(r.score * 100).toFixed(0)}% match</Badge>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
              </CardHeader>
              {r.content && (
                <CardContent className="pt-0">
                  <pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-24">{r.content.slice(0, 300)}{r.content.length > 300 ? '...' : ''}</pre>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}

      {searchMutation.isSuccess && results.length === 0 && (
        <Card><CardContent className="p-8 text-center text-muted-foreground">No results found for &quot;{query}&quot;. Try a different query.</CardContent></Card>
      )}

      {!searchMutation.isSuccess && !searchMutation.isPending && (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
          <Search className="h-12 w-12 text-muted-foreground" />
          <div>
            <h2 className="text-lg font-semibold">Search your codebase</h2>
            <p className="text-sm text-muted-foreground max-w-md">Use natural language to find functions, classes, files, and documentation across your repositories.</p>
          </div>
        </div>
      )}
    </div>
  )
}
