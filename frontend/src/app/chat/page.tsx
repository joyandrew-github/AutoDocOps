'use client'
import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Send, Bot, User, Loader2, Trash2 } from 'lucide-react'

interface Message {
  role: 'user' | 'agent'
  content: string
  agent?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const agents = useQuery({ queryKey: ['agents'], queryFn: () => api.get('/api/v1/ai/agents') })
  const agentList = agents.data || []

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)
    setStreaming(true)

    try {
      const res = await fetch(`${API_URL}/api/v1/ai/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, repository_id: 1, conversation_id: conversationId }),
      })

      if (!res.ok) throw new Error('Stream failed')

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      let content = ''

      setMessages(prev => [...prev, { role: 'agent', content: '', agent: 'AI' }])

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          content += decoder.decode(value, { stream: true })
          setMessages(prev => {
            const next = [...prev]
            next[next.length - 1] = { role: 'agent', content, agent: 'AI' }
            return next
          })
        }
      }
    } catch {
      try {
        const data = await api.post('/api/v1/ai/chat', { message: userMsg, repository_id: 1, conversation_id: conversationId })
        if (data.conversation_id) setConversationId(data.conversation_id)
        setMessages(prev => [...prev, { role: 'agent', content: data.content, agent: data.agent_name }])
      } catch {
        setMessages(prev => [...prev, { role: 'agent', content: 'Failed to get response. Check backend connection.', agent: 'system' }])
      }
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="border-b p-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">AI Chat</h1>
            <p className="text-sm text-muted-foreground">Multi-agent conversation with streaming</p>
          </div>
          <div className="flex gap-2">
            {conversationId && <Badge variant="outline" className="text-xs">Session: {conversationId.slice(0, 8)}</Badge>}
            <Button variant="ghost" size="icon" onClick={() => { setMessages([]); setConversationId(null) }}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <Bot className="h-12 w-12 text-muted-foreground" />
              <div>
                <h2 className="text-lg font-semibold">Start a conversation</h2>
                <p className="text-sm text-muted-foreground max-w-md">Ask about code, architecture, impact analysis, documentation, or search your codebase.</p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center">
                {['Explain the architecture', 'Search for authentication', 'What is the impact of changes?', 'Generate documentation'].map(q => (
                  <Button key={q} variant="outline" size="sm" onClick={() => { setInput(q); }}>{q}</Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'agent' && (
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div className={`max-w-[70%] rounded-lg px-4 py-3 text-sm ${
                msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}>
                {msg.agent && msg.role === 'agent' && (
                  <div className="text-xs font-medium mb-1 opacity-70">{msg.agent.replace(/_/g, ' ')}</div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
              {msg.role === 'user' && (
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                  <User className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
          {streaming && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" />Streaming...</div>}
          <div ref={bottomRef} />
        </div>

        <div className="border-t p-4">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage() }} className="flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about your codebase..."
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </div>
      </div>

      <div className="hidden lg:block w-64 border-l p-4 overflow-y-auto">
        <h3 className="font-semibold text-sm mb-3">Available Agents</h3>
        <div className="space-y-2">
          {agentList.map((a: any) => (
            <Card key={a.name} className="p-3">
              <div className="text-sm font-medium">{a.name.replace(/_/g, ' ')}</div>
              <div className="text-xs text-muted-foreground mt-1">{a.description}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {(a.capabilities || []).slice(0, 3).map((c: string) => (
                  <Badge key={c} variant="secondary" className="text-[10px]">{c}</Badge>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
