import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, ApiError, errorMessage } from './api'
import type { Session } from './api'

type Auth = { session: Session | null; loading: boolean; error: string; refresh: () => Promise<void>; setSession: (value: Session | null) => void; logout: () => Promise<void> }
const Context = createContext<Auth | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  async function refresh() {
    setError('')
    try { setSession(await api<Session>('/me')) }
    catch (err) {
      if (err instanceof ApiError && err.status === 401) setSession(null)
      else setError(errorMessage(err))
    } finally { setLoading(false) }
  }
  useEffect(() => { void refresh() }, [])
  useEffect(() => {
    const update = () => { void refresh() }
    window.addEventListener('focus', update)
    return () => window.removeEventListener('focus', update)
  }, [])
  async function logout() {
    try { await api('/logout', { method: 'POST' }) }
    catch (err) { if (!(err instanceof ApiError && err.status === 401)) throw err }
    setSession(null)
  }
  return <Context.Provider value={{ session, loading, error, refresh, setSession, logout }}>{children}</Context.Provider>
}

export function useAuth() {
  const auth = useContext(Context)
  if (!auth) throw new Error('AuthProvider required')
  return auth
}
