import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Plus, File, ChevronRight, ArrowLeft } from 'lucide-react'
import Layout from '../components/Layout'
import { getMe, getRepository, getSessions, createSession, getFiles } from '../services/api'

export default function RepositoryPage() {
  const { repoId } = useParams<{ repoId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState<'chat' | 'files'>('chat')

  const { data: user } = useQuery({ queryKey: ['me'], queryFn: () => getMe().then(r => r.data) })
  const { data: repo } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => getRepository(repoId!).then(r => r.data),
  })
  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions', repoId],
    queryFn: () => getSessions(repoId!).then(r => r.data),
  })
  const { data: files = [] } = useQuery({
    queryKey: ['files', repoId],
    queryFn: () => getFiles(repoId!).then(r => r.data),
    enabled: activeTab === 'files',
  })

  const newSessionMutation = useMutation({
    mutationFn: () => createSession(repoId!),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['sessions', repoId] })
      navigate(`/repositories/${repoId}/chat/${res.data.id}`)
    },
  })

  if (!repo) return null

  return (
    <Layout user={user}>
      <div className="max-w-5xl mx-auto">
        <button onClick={() => navigate('/dashboard')} className="btn-ghost flex items-center gap-1 text-sm mb-4 -ml-1">
          <ArrowLeft className="w-4 h-4" />
          Dashboard
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold">{repo.name}</h1>
          {repo.summary && <p className="text-gray-400 mt-1">{repo.summary}</p>}
          {repo.tech_stack && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {repo.tech_stack.split(',').map(t => (
                <span key={t} className="text-xs px-2 py-0.5 bg-gray-800 text-gray-300 rounded-full">
                  {t.trim()}
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-4 text-xs text-gray-500 mt-2">
            <span>{repo.file_count} files</span>
            <span>{repo.chunk_count} chunks indexed</span>
          </div>
        </div>

        <div className="flex gap-1 mb-6 border-b border-gray-800">
          {(['chat', 'files'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors ${
                activeTab === tab
                  ? 'border-brand-500 text-brand-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab === 'chat' ? 'Chat Sessions' : 'Files'}
            </button>
          ))}
        </div>

        {activeTab === 'chat' && (
          <div className="space-y-3">
            <button
              onClick={() => newSessionMutation.mutate()}
              disabled={newSessionMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Chat
            </button>

            {sessions.length === 0 ? (
              <div className="text-center py-16 text-gray-500">
                <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No chats yet. Start one above.</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {sessions.map(session => (
                  <button
                    key={session.id}
                    onClick={() => navigate(`/repositories/${repoId}/chat/${session.id}`)}
                    className="card text-left hover:border-gray-700 flex items-center justify-between group transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <MessageSquare className="w-4 h-4 text-brand-400 shrink-0" />
                      <span className="text-sm truncate">{session.title}</span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 shrink-0" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'files' && (
          <div className="space-y-1">
            {files.map(file => (
              <div key={file.id} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 group">
                <File className="w-4 h-4 text-gray-500 shrink-0" />
                <span className="text-sm text-gray-300 font-mono flex-1 truncate">{file.file_path}</span>
                <span className="text-xs text-gray-600">{file.line_count} lines</span>
                <span className="text-xs px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded group-hover:bg-gray-700">
                  {file.language}
                </span>
              </div>
            ))}
            {files.length === 0 && (
              <p className="text-center text-gray-500 py-8">Loading files...</p>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}
