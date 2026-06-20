import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Github, Trash2, RefreshCw, CheckCircle, AlertCircle, Clock, Loader } from 'lucide-react'
import Layout from '../components/Layout'
import { getMe, getRepositories, addRepository, deleteRepository } from '../services/api'
import type { Repository } from '../types'

const StatusBadge = ({ status }: { status: Repository['status'] }) => {
  const config = {
    ready: { icon: CheckCircle, label: 'Ready', cls: 'text-green-400 bg-green-400/10' },
    indexing: { icon: Loader, label: 'Indexing...', cls: 'text-yellow-400 bg-yellow-400/10 animate-pulse' },
    pending: { icon: Clock, label: 'Pending', cls: 'text-gray-400 bg-gray-400/10' },
    failed: { icon: AlertCircle, label: 'Failed', cls: 'text-red-400 bg-red-400/10' },
  }
  const { icon: Icon, label, cls } = config[status]
  return (
    <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full font-medium ${cls}`}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  )
}

export default function DashboardPage() {
  const [url, setUrl] = useState('')
  const [adding, setAdding] = useState(false)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: user } = useQuery({ queryKey: ['me'], queryFn: () => getMe().then(r => r.data) })
  const { data: repos = [], isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => getRepositories().then(r => r.data),
    refetchInterval: (query) => {
      const data = query.state.data
      if (Array.isArray(data) && data.some(r => r.status === 'pending' || r.status === 'indexing')) return 3000
      return false
    },
  })

  const addMutation = useMutation({
    mutationFn: addRepository,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['repositories'] })
      setUrl('')
      setAdding(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteRepository,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['repositories'] }),
  })

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    addMutation.mutate(url.trim())
  }

  return (
    <Layout user={user}>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">My Repositories</h1>
            <p className="text-gray-500 text-sm mt-1">Paste a GitHub URL to start chatting with any codebase</p>
          </div>
          <button
            onClick={() => setAdding(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Repository
          </button>
        </div>

        {adding && (
          <div className="card mb-6">
            <h2 className="font-semibold mb-3">Add GitHub Repository</h2>
            <form onSubmit={handleAdd} className="flex gap-3">
              <input
                type="url"
                className="input flex-1"
                placeholder="https://github.com/owner/repository"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                autoFocus
              />
              <button type="submit" className="btn-primary" disabled={addMutation.isPending}>
                {addMutation.isPending ? 'Adding...' : 'Add'}
              </button>
              <button type="button" className="btn-ghost" onClick={() => setAdding(false)}>
                Cancel
              </button>
            </form>
            {addMutation.error && (
              <p className="text-red-400 text-sm mt-2">Failed to add repository. Check the URL and try again.</p>
            )}
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : repos.length === 0 ? (
          <div className="text-center py-24 text-gray-500">
            <Github className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="font-medium">No repositories yet</p>
            <p className="text-sm mt-1">Add a GitHub repository to get started</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {repos.map((repo) => (
              <div
                key={repo.id}
                className="card hover:border-gray-700 transition-colors cursor-pointer group"
                onClick={() => repo.status === 'ready' && navigate(`/repositories/${repo.id}`)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold truncate">{repo.name}</h3>
                      <StatusBadge status={repo.status} />
                    </div>
                    <a
                      href={repo.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-sm text-gray-500 hover:text-brand-400 truncate block"
                    >
                      {repo.github_url}
                    </a>
                    {repo.summary && (
                      <p className="text-sm text-gray-400 mt-2 line-clamp-2">{repo.summary}</p>
                    )}
                    {repo.tech_stack && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {repo.tech_stack.split(',').slice(0, 6).map(t => (
                          <span key={t} className="text-xs px-2 py-0.5 bg-gray-800 text-gray-300 rounded-full">
                            {t.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                    {repo.status === 'ready' && (
                      <p className="text-xs text-gray-600 mt-2">
                        {repo.file_count} files · {repo.chunk_count} chunks indexed
                      </p>
                    )}
                    {repo.status === 'failed' && repo.error_message && (
                      <p className="text-xs text-red-400 mt-1">{repo.error_message}</p>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (confirm('Delete this repository?')) deleteMutation.mutate(repo.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 btn-ghost p-2 text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
