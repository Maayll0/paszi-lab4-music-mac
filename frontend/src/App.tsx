import './index.css'
import { Link, Route, Routes } from 'react-router-dom'
import RegisterPage from './RegisterPage'
import AccessDeniedPage from './AccessDeniedPage'
import LoginPage from './LoginPage'
import AccountPage from './AccountPage'
import Catalog from './Catalog'
import TrackPage from './TrackPage'

export default function App() {
  return <Routes>
    <Route path="/" element={<Catalog />} />
    <Route path="/music" element={<Catalog />} />
    <Route path="/music/:id" element={<TrackPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/account" element={<AccountPage />} />
    <Route path="/access-denied" element={<AccessDeniedPage />} />
    <Route path="*" element={<main className="catalog"><h1>Страница не найдена</h1><Link to="/music">В каталог</Link></main>} />
  </Routes>
}
