import './App.css'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import ServersPage from './pages/ServersPage'
import CustomersPage from './pages/CustomersPage'
import GatewaysPage from './pages/GatewaysPage'
import NumberLookupPage from './pages/NumberLookupPage'
import CleanupPage from './pages/CleanupPage'

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Servers</Link> |{' '}
        <Link to="/customers">Customers</Link> |{' '}
        <Link to="/gateways">Gateways</Link> |{' '}
        <Link to="/numbers">Number Lookup</Link> |{' '}
        <Link to="/cleanup">Cleanup</Link>
      </nav>
      <Routes>
        <Route path="/" element={<ServersPage />} />
        <Route path="/customers" element={<CustomersPage />} />
        <Route path="/gateways" element={<GatewaysPage />} />
        <Route path="/numbers" element={<NumberLookupPage />} />
        <Route path="/cleanup" element={<CleanupPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
