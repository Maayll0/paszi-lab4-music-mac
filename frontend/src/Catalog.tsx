import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, errorMessage, levels } from './api'
import Header from './Header'

export type Track = { id: number; title: string; artist: string; security_level: number; duration: number }

export default function Catalog() {
  const [params, setParams] = useSearchParams()
  const query = params.toString()
  const [draft, setDraft] = useState({ q: params.get('q') ?? '', title: params.get('title') ?? '', artist: params.get('artist') ?? '' })
  const [tracks, setTracks] = useState<Track[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [focused, setFocused] = useState(false)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const search = new URLSearchParams(query)
    setDraft({ q: search.get('q') ?? '', title: search.get('title') ?? '', artist: search.get('artist') ?? '' })
  }, [query])

  useEffect(() => {
    const next = new URLSearchParams()
    for (const [key, value] of Object.entries(draft)) if (value.trim()) next.set(key, value.trim())
    if (next.toString() === query) return
    const timer = window.setTimeout(() => setParams(next), 350)
    return () => window.clearTimeout(timer)
  }, [draft, query, setParams])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    api<Track[]>(`/tracks?${query}`, { signal: controller.signal })
      .then(setTracks)
      .catch(err => { if (!controller.signal.aborted) setError(errorMessage(err)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [query, retry])

  const suggestions = focused && Object.values(draft).some(Boolean) && !loading && !error
  return <div className="app"><Header /><main>
    <section className="hero"><p className="eyebrow">MUSIC ACCESS CONTROL</p>
      <h1>Музыка с новым уровнем доступа</h1><p>Слушайте любимые композиции. Доступ к контенту определяется уровнем допуска.</p>
    </section>
    <section className="catalog"><h2>Каталог музыки</h2>
      <div className="search-area" onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setFocused(false) }}>
        <label htmlFor="search">Название или исполнитель</label>
        <input id="search" type="search" maxLength={100} autoComplete="off" placeholder="Например, Night" value={draft.q} onFocus={() => setFocused(true)} onKeyDown={e => { if (e.key === 'Escape') setFocused(false) }} onChange={e => { setDraft({ ...draft, q: e.target.value }); setFocused(true) }} />
        {suggestions && <ul className="suggestions" aria-label="Поисковые подсказки">
          {tracks.slice(0, 5).map(track => <li key={track.id}><Link to={`/music/${track.id}`}>{track.title} <span>— {track.artist}</span></Link></li>)}
          {!tracks.length && <li>Ничего не найдено</li>}
        </ul>}
      </div>
      <div className="filters">
        <label>Название<input maxLength={100} value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} /></label>
        <label>Исполнитель<input maxLength={100} value={draft.artist} onChange={e => setDraft({ ...draft, artist: e.target.value })} /></label>
        <button className="login-button" onClick={() => { setDraft({ q: '', title: '', artist: '' }); setParams({}); setFocused(false) }}>Сбросить</button>
      </div>
      {loading && <p role="status">Загрузка композиций…</p>}
      {error && <p role="alert" className="auth-error">{error} <button onClick={() => setRetry(retry + 1)}>Повторить</button></p>}
      {!loading && !error && !tracks.length && <p role="status">Композиции не найдены. Попробуйте изменить запрос.</p>}
      {!loading && !error && <div className="tracks">{tracks.map(track => <article className="track-card" key={track.id}>
        <div className="cover" aria-hidden="true">♫</div>
        <div className="track-info"><span className="level">{levels[track.security_level]}</span><h3>{track.title}</h3><p>{track.artist}</p><small>{track.duration} сек. · Демонстрационная композиция</small></div>
        <Link className="login-button" to={`/music/${track.id}`}>Открыть трек →</Link>
      </article>)}</div>}
    </section>
  </main></div>
}
