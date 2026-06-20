import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMe, login, logout, register } from '../services/api'
import { useNavigate } from 'react-router-dom'

export function useAuth() {
  const qc = useQueryClient()
  const navigate = useNavigate()

  const { data: user, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => getMe().then((r) => r.data),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      login(email, password).then((r) => r.data.user),
    onSuccess: (user) => {
      qc.setQueryData(['me'], user)
      navigate('/dashboard')
    },
  })

  const registerMutation = useMutation({
    mutationFn: ({ name, email, password }: { name: string; email: string; password: string }) =>
      register(name, email, password).then((r) => r.data.user),
    onSuccess: (user) => {
      qc.setQueryData(['me'], user)
      navigate('/dashboard')
    },
  })

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      qc.clear()
      navigate('/login')
    },
  })

  return { user, isLoading, loginMutation, registerMutation, logoutMutation }
}
