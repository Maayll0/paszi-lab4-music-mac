import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { errorMessage, levels } from './api'

export default function Header() {
  const { session, loading, error: authError, logout } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function leave() {
    setBusy(true); setError('')
    try { await logout() } catch (err) { setError(errorMessage(err)) }
    finally { setBusy(false) }
  }
  return <><header className="header">
    <Link className="logo" to="/">♫ MusicAccess</Link>
    <nav aria-label="Аккаунт">
      {loading ? <span role="status">Загрузка…</span> : session ? <>
        <Link to="/account">{session.user.login}</Link>
        <span className="level">Допуск: {levels[session.user.clearance_level]}</span>
        <button className="login-button" onClick={leave} disabled={busy}>Выйти</button>
      </> : <><Link to="/login">Войти</Link><Link className="login-button" to="/register">Регистрация</Link></>}
    </nav>
  </header>{(error || authError) && <p className="auth-error page-message" role="alert">{error || authError}</p>}</>
}
