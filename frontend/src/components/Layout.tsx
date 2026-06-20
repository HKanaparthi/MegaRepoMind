import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { logout } from '../services/api'
import { LogOut, GitBranch } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
  user?: { name: string; email: string }
}

export default function Layout({ children, user }: LayoutProps) {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => { qc.clear(); navigate('/login') },
  })

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2 font-bold text-lg">
            <GitBranch className="w-5 h-5 text-brand-500" />
            <span className="text-white">MegaRepoMind</span>
          </Link>
          {user && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">{user.name}</span>
              <button
                onClick={() => logoutMutation.mutate()}
                className="btn-ghost flex items-center gap-1.5 text-sm"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {children}
      </main>
    </div>
  )
}
