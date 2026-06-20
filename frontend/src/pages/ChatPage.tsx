import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Send, Loader } from 'lucide-react'
import Layout from '../components/Layout'
import ChatMessage from '../components/ChatMessage'
import { getMe, getRepository, getMessages, sendMessage } from '../services/api'
import type { Message } from '../types'

const SUGGESTED_QUESTIONS = [
  'How does authentication work?',
  'What is the overall architecture?',
  'Where is the database configured?',
  'How are API routes structured?',
  'What are the main dependencies?',
]

export default function ChatPage() {
  const { repoId, sessionId } = useParams<{ repoId: string; sessionId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { data: user } = useQuery({ queryKey: ['me'], queryFn: () => getMe().then(r => r.data) })
  const { data: repo } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => getRepository(repoId!).then(r => r.data),
  })
  const { data: messages = [] } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => getMessages(sessionId!).then(r => r.data),
  })

  const sendMutation = useMutation({
    mutationFn: (content: string) => sendMessage(sessionId!, content),
    onMutate: async (content) => {
      await qc.cancelQueries({ queryKey: ['messages', sessionId] })
      const optimistic: Message = {
        id: 'optimistic-' + Date.now(),
        role: 'user',
        content,
        citations: null,
        created_at: new Date().toISOString(),
      }
      qc.setQueryData(['messages', sessionId], (old: Message[] = []) => [...old, optimistic])
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['messages', sessionId] })
      qc.invalidateQueries({ queryKey: ['sessions', repoId] })
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const content = input.trim()
    if (!content || sendMutation.isPending) return
    setInput('')
    sendMutation.mutate(content)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Layout user={user}>
      <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 shrink-0">
          <button
            onClick={() => navigate(`/repositories/${repoId}`)}
            className="btn-ghost flex items-center gap-1 text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            {repo?.name}
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4">
          {messages.length === 0 && (
            <div className="text-center pt-8">
              <p className="text-gray-400 mb-6">
                Ask anything about <span className="text-brand-400 font-medium">{repo?.name}</span>
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTED_QUESTIONS.map(q => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); textareaRef.current?.focus() }}
                    className="text-sm px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full border border-gray-700 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {sendMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3">
                <Loader className="w-4 h-4 text-brand-400 animate-spin" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="shrink-0 bg-gray-950 pt-3 border-t border-gray-800">
          <div className="flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              className="input flex-1 resize-none min-h-[44px] max-h-32"
              placeholder="Ask about the codebase..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sendMutation.isPending}
              className="btn-primary p-2.5 aspect-square flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-1.5">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </Layout>
  )
}
