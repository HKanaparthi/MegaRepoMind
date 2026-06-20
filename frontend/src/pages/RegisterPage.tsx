import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { registerMutation } = useAuth()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    registerMutation.mutate({ name, email, password })
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <GitBranch className="w-7 h-7 text-brand-500" />
          <span className="text-2xl font-bold">MegaRepoMind</span>
        </div>
        <div className="card">
          <h1 className="text-xl font-semibold mb-6 text-center">Create account</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name</label>
              <input
                type="text"
                className="input"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                className="input"
                placeholder="Min. 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            {registerMutation.error && (
              <p className="text-red-400 text-sm">Registration failed. Email may already be in use.</p>
            )}
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={registerMutation.isPending}
            >
              {registerMutation.isPending ? 'Creating account...' : 'Create account'}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-500 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
