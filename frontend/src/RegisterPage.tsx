
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from './api'

export default function RegisterPage() {
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setMessage('')
    setError('')

    if (!/^[a-zA-Z0-9._-]{3,32}$/.test(login)) {
      setError('Логин: от 3 до 32 символов, латиница, цифры, . _ -')
      return
    }

    if (
      password.length < 8 ||
      !/[A-Z]/.test(password) ||
      !/[a-z]/.test(password) ||
      !/[0-9]/.test(password) ||
      !/[^\w\s]|_/.test(password)
    ) {
      setError('Пароль: минимум 8 символов, заглавная и строчная буквы, цифра и спецсимвол')
      return
    }

    setLoading(true)

    try {
      const data = await api<{ message: string }>('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password, email: email || null }),
      })

      setMessage(data.message || 'Регистрация успешна!')
      setPassword('')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link to="/" className="back-link">← На главную</Link>

        <h1>Регистрация</h1>
        <p>Создайте аккаунт MusicAccess</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="login">Логин</label>
          <input
            id="login"
            type="text"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            placeholder="Введите логин"
            autoComplete="username"
            minLength={3}
            maxLength={32}
            required
          />

          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Введите пароль"
            autoComplete="new-password"
            maxLength={128}
            required
          />

          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="email" maxLength={320} value={email} onChange={e => setEmail(e.target.value)} required />
          {error && <div className="auth-error" role="alert">{error}</div>}
          {message && <div className="auth-success" role="status">{message}</div>}
          {message && <Link to="/login">Перейти ко входу →</Link>}

          <button type="submit" disabled={loading}>
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>

        <div className="auth-footer">
          После регистрации назначается уровень Public
        </div>
      </div>
    </div>
  )
}
