import { BrowserRouter, Routes, Route } from 'react-router-dom'
import NotesToAnki from './pages/NotesToAnki'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<NotesToAnki />} />
      </Routes>
    </BrowserRouter>
  )
}
