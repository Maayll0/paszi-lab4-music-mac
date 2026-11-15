import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorMessage } from './api'
import type { Session } from './api'
import { useAuth } from './AuthContext'

export default function LoginPage() {
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setSession } = useAuth()
  const navigate = useNavigate()
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError('')
    try {
      setSession(await api<Session>('/login', { method: 'POST', body: JSON.stringify({ login, password }) }))
      setPassword(''); navigate('/music')
    } catch (err) { setError(errorMessage(err)) }
    finally { setLoading(false) }
  }
  return <div className="auth-page"><div className="auth-card">
    <Link className="back-link" to="/">← На главную</Link>
    <h1>Вход</h1><p>Добро пожаловать в MusicAccess</p>
    <form onSubmit={submit}>
      <label htmlFor="login">Логин</label><input id="login" autoComplete="username" required maxLength={32} value={login} onChange={e => setLogin(e.target.value)} />
      <label htmlFor="password">Пароль</label><input id="password" type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={e => setPassword(e.target.value)} />
      {error && <div role="alert" className="auth-error">{error}</div>}
      <button disabled={loading}>{loading ? 'Вход…' : 'Войти'}</button>
    </form>
    <p className="auth-footer">Нет аккаунта? <Link to="/register">Регистрация</Link></p>
  </div></div>
}
