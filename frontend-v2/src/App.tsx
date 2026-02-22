import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import LocationsPage from './pages/LocationsPage';
import AccessoriesPage from './pages/AccessoriesPage';
import WorkOrdersPage from './pages/WorkOrdersPage';
import AccessoryDetailPage from './pages/AccessoryDetailPage';
import SKUDetailPage from './pages/SKUDetailPage';
import DataExportPage from './pages/DataExportPage';

function App() {
  return (
    <Router>
      <div className="bg-gray-900 text-white min-h-screen">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<AccessoriesPage />} />
            <Route path="/work-orders" element={<WorkOrdersPage />} />
            <Route path="/locations" element={<LocationsPage />} />
            <Route path="/accessory/:id" element={<AccessoryDetailPage />} />
            <Route path="/sku/:sku" element={<SKUDetailPage />} />
            <Route path="/data" element={<DataExportPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
