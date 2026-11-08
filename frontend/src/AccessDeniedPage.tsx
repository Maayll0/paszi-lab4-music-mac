
import { Link } from 'react-router-dom'

export default function AccessDeniedPage() {
  return (
    <div className="denied-page">
      <div className="denied-card">
        <div className="denied-icon">🔒</div>

        <h1>403</h1>
        <h2>Доступ запрещён</h2>

        <p>
          Ваш уровень допуска недостаточен
          для доступа к запрашиваемому ресурсу.
        </p>

        <div className="denied-info">
          Доступ ограничен мандатной политикой
          безопасности MusicAccess.
        </div>

        <Link to="/" className="denied-button">
          Вернуться в каталог
        </Link>
      </div>
    </div>
  )
}
