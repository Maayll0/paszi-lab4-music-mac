import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError, errorMessage } from './api'
import { useAuth } from './AuthContext'
import type { Track } from './Catalog'

export default function AudioPlayer({ track }: { track: Track }) {
  const { session, setSession, refresh } = useAuth()
  const [source, setSource] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [available, setAvailable] = useState<Track[]>([])
  const audio = useRef<HTMLAudioElement>(null)
  const pending = useRef<AbortController | null>(null)
  const navigate = useNavigate()
  const userId = session?.user.id
  const index = available.findIndex(item => item.id === track.id)

  useEffect(() => {
    setSource(''); setError(''); setBusy(false)
    return () => { pending.current?.abort() }
  }, [track.id, userId])

  useEffect(() => {
    if (!userId) { setAvailable([]); return }
    const controller = new AbortController()
    api<Track[]>('/me/tracks', { signal: controller.signal }).then(setAvailable)
      .catch(err => { if (!controller.signal.aborted) setError(errorMessage(err)) })
    return () => controller.abort()
  }, [userId, track.id])

  useEffect(() => {
    const element = audio.current
    if (source && element) {
      element.volume = 0.6
      void element.play().catch(() => { /* Native play control remains available. */ })
    }
    return () => { if (element) { element.pause(); element.removeAttribute('src'); element.load() } }
  }, [source])

  async function prepare() {
    pending.current?.abort()
    const controller = new AbortController()
    pending.current = controller
    setBusy(true); setError('')
    try {
      // Probe the actual protected endpoint; never infer authorization from UI labels.
      const response = await fetch(`/api/tracks/${track.id}/stream`, {
        credentials: 'same-origin', headers: { Range: 'bytes=0-0' }, signal: controller.signal,
      })
      if (response.status === 403) { navigate('/access-denied'); return }
      if (response.status === 401) { setSession(null); navigate('/login'); return }
      if (!response.ok) throw new ApiError(response.status, 'Аудиофайл недоступен')
      await response.arrayBuffer()
      setSource(`/api/tracks/${track.id}/stream`)
    } catch (err) { if (!controller.signal.aborted) setError(errorMessage(err)) }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }

  async function mediaError() {
    setSource('')
    setError('Не удалось воспроизвести аудио. Попробуйте открыть трек снова.')
    await refresh()
    // A later Range request may fail after clearance changes or session expiry.
    try {
      const response = await fetch(`/api/tracks/${track.id}/stream`, { headers: { Range: 'bytes=0-0' } })
      await response.body?.cancel()
      if (response.status === 403) navigate('/access-denied')
      if (response.status === 401) { setSession(null); navigate('/login') }
    } catch { /* Keep the actionable network error above. */ }
  }

  if (!session) return <p><Link to="/login">Войдите</Link>, чтобы слушать музыку.</p>
  return <section className="player" aria-label={`Плеер: ${track.title}`}>
    {!source && <button className="login-button" disabled={busy} onClick={prepare}>{busy ? 'Открываем аудио…' : '▶ Слушать'}</button>}
    {source && <audio ref={audio} src={source} controls preload="metadata" onError={() => void mediaError()} />}
    {error && <p role="alert" className="auth-error">{error}</p>}
    <div className="player-navigation">
      <button disabled={index <= 0} onClick={() => navigate(`/music/${available[index - 1].id}`)}>← Предыдущий</button>
      <button disabled={index < 0 || index >= available.length - 1} onClick={() => navigate(`/music/${available[index + 1].id}`)}>Следующий →</button>
    </div>
    <small>Переключение между композициями, доступными вашему аккаунту.</small>
  </section>
}
