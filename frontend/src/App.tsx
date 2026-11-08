
import './index.css'
import { Link, Route, Routes } from 'react-router-dom'
import RegisterPage from './RegisterPage'

const tracks = [
  {
    id: 1,
    title: 'Night Drive',
    artist: 'Electronic Waves',
    level: 'Public',
    description: 'Доступно всем пользователям',
  },
  {
    id: 2,
    title: 'Deep Ocean',
    artist: 'Ambient Project',
    level: 'Confidential',
    description: 'Доступно с Premium-допуском',
  },
  {
    id: 3,
    title: 'Secret Sessions',
    artist: 'Studio X',
    level: 'Secret',
    description: 'Закрытый материал',
  }
]

function Catalog() {
  return (
    <div className="app">
      <header className="header">
        <div className="logo">♫ MusicAccess</div>
        <Link to="/register" className="login-button">
          Регистрация
        </Link>
      </header>

      <main>
        <section className="hero">
          <p className="eyebrow">MUSIC ACCESS CONTROL</p>
          <h1>Музыка с новым уровнем доступа</h1>
          <p>
            Слушайте любимые композиции.
            Доступ к контенту определяется уровнем допуска.
          </p>
        </section>

        <section className="catalog">
          <h2>Каталог музыки</h2>
          <div className="tracks">
            {tracks.map((track) => (
              <article className="track-card" key={track.id}>
                <div className="cover">♫</div>
                <div className="track-info">
                  <span className="level">{track.level}</span>
                  <h3>{track.title}</h3>
                  <p>{track.artist}</p>
                  <small>{track.description}</small>
                </div>
                <button disabled>▶ Слушать</button>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
function App() {
  return (
    <Routes>
      <Route path="/" element={<Catalog />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}

export default App
