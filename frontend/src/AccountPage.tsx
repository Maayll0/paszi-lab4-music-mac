import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, errorMessage, levels } from './api'
import { useAuth } from './AuthContext'

export default function AccountPage() {
  const { session, loading, setSession } = useAuth()
  const [password, setPassword] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  if (loading) return <p role="status">Загрузка…</p>
  if (!session) return <Navigate to="/login" replace />
  async function remove(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!confirmed || !session) return
    setBusy(true); setError('')
    try {
      await api('/me', { method: 'DELETE', body: JSON.stringify({ password }) })
      setSession(null); navigate('/login', { replace: true })
    } catch (err) { setError(errorMessage(err)) }
    finally { setBusy(false) }
  }
  return <div className="auth-page"><div className="auth-card">
    <Link className="back-link" to="/music">← В каталог</Link>
    <h1>{session.user.login}</h1><p>Допуск: {levels[session.user.clearance_level]}</p>
    <h2>Удалить аккаунт</h2><p>Профиль будет удалён без возможности восстановления. Все сеансы будут завершены.</p>
    <form onSubmit={remove}>
      <label htmlFor="delete-password">Подтвердите пароль</label>
      <input id="delete-password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required maxLength={128} />
      <label className="checkbox-label"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} required /> Я подтверждаю удаление аккаунта</label>
      {error && <p role="alert" className="auth-error">{error}</p>}
      <button className="danger" disabled={busy || !confirmed}>{busy ? 'Удаление…' : 'Удалить аккаунт'}</button>
    </form>
  </div></div>
}
