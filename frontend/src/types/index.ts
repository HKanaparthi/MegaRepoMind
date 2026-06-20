export interface User {
  id: string
  email: string
  name: string
}

export type RepoStatus = 'pending' | 'indexing' | 'ready' | 'failed'

export interface Repository {
  id: string
  name: string
  github_url: string
  description: string | null
  status: RepoStatus
  file_count: number
  chunk_count: number
  summary: string | null
  tech_stack: string | null
  error_message: string | null
  created_at: string
  indexed_at: string | null
}

export interface RepositoryFile {
  id: string
  file_path: string
  language: string
  size: number
  line_count: number
}

export interface ChatSession {
  id: string
  repository_id: string
  title: string
  created_at: string
}

export type MessageRole = 'user' | 'assistant'

export interface Citation {
  file_path: string
  start_line: number
  end_line: number
  snippet: string
  score: number
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  citations: Citation[] | null
  created_at: string
}
