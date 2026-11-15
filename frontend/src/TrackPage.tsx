import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorMessage, levels } from './api'
import type { Track } from './Catalog'
import Header from './Header'
import AudioPlayer from './AudioPlayer'

export default function TrackPage() {
  const { id } = useParams()
  const [track, setTrack] = useState<Track | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setTrack(null); setError('')
    api<Track>(`/tracks/${id}`, { signal: controller.signal }).then(setTrack)
      .catch(err => { if (!controller.signal.aborted) setError(errorMessage(err)) })
    return () => controller.abort()
  }, [id])
  return <><Header /><main className="catalog"><Link to="/music">← В каталог</Link>
    {error ? <p className="auth-error" role="alert">{error}</p> : track ? <article className="track-card track-detail">
      <div className="cover">♫</div><h1>{track.title}</h1><p>{track.artist}</p><p className="level">{levels[track.security_level]}</p>
      <AudioPlayer key={track.id} track={track} />
    </article> : <p role="status">Загрузка…</p>}
  </main></>
}
