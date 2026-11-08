
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

export default function RegisterPage() {
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
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
      !/[^a-zA-Z0-9]/.test(password)
    ) {
      setError('Пароль: минимум 8 символов, заглавная и строчная буквы, цифра и спецсимвол')
      return
    }

    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        if (response.status === 409) {
          throw new Error('Этот логин уже занят')
        }
        if (response.status === 422) {
          throw new Error('Ошибка проверки введённых данных')
        }
        throw new Error('Не удалось зарегистрироваться')
      }

      setMessage(data.message || 'Регистрация успешна!')
      setPassword('')
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Backend пока недоступен. Подключим его следующим этапом.'
          : err instanceof Error
            ? err.message
            : 'Ошибка подключения'
      )
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
            required
          />

          {error && <div className="auth-error" role="alert">{error}</div>}
          {message && <div className="auth-success" role="status">{message}</div>}

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
