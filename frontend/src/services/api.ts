import axios from 'axios'
import type { User, Repository, RepositoryFile, ChatSession, Message } from '../types'

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`,
  withCredentials: true,
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const url: string = error.config?.url ?? ''
    const isAuthEndpoint = url.includes('/auth/')
    if (error.response?.status === 401 && !error.config._retry && !isAuthEndpoint) {
      error.config._retry = true
      try {
        await api.post('/auth/refresh')
        return api(error.config)
      } catch {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth
export const register = (name: string, email: string, password: string) =>
  api.post<{ user: User }>('/auth/register', { name, email, password })

export const login = (email: string, password: string) =>
  api.post<{ user: User }>('/auth/login', { email, password })

export const logout = () => api.post('/auth/logout')

export const getMe = () => api.get<User>('/auth/me')

// Repositories
export const getRepositories = () => api.get<Repository[]>('/repositories')

export const addRepository = (github_url: string) =>
  api.post<Repository>('/repositories', { github_url })

export const getRepository = (id: string) =>
  api.get<Repository>(`/repositories/${id}`)

export const deleteRepository = (id: string) =>
  api.delete(`/repositories/${id}`)

export const getFiles = (id: string) =>
  api.get<RepositoryFile[]>(`/repositories/${id}/files`)

// Chat
export const getSessions = (repoId: string) =>
  api.get<ChatSession[]>(`/repositories/${repoId}/sessions`)

export const createSession = (repoId: string, title = 'New Chat') =>
  api.post<ChatSession>(`/repositories/${repoId}/sessions`, { title })

export const getMessages = (sessionId: string) =>
  api.get<Message[]>(`/sessions/${sessionId}/messages`)

export const sendMessage = (sessionId: string, content: string) =>
  api.post<Message>(`/sessions/${sessionId}/messages`, { content })
