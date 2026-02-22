import { useState, useEffect } from 'react';
import { MapPin, Plus, RefreshCw, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../apiClient';

interface Location {
  id: number;
  name: string;
  usage_count: number;
}

function LocationsPage() {
  const navigate = useNavigate();
  const [locations, setLocations] = useState<Location[]>([]);
  const [newLocationName, setNewLocationName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchLocations = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<Location[]>('/locations');
      setLocations(response.data);
    } catch (err) {
      setError('Failed to fetch locations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  const handleAddLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLocationName.trim()) {
      setError('Location name cannot be empty.');
      return;
    }
    setError(null);
    setSuccess(null);

    try {
      const response = await apiClient.post('/locations', { name: newLocationName });
      if (response.data.success) {
        setNewLocationName('');
        setSuccess(response.data.message);
        fetchLocations();
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to add location. Please try again.');
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-3xl font-bold text-white">Location Management</h1>
        </div>
        <button
          onClick={fetchLocations}
          className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl mb-8">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
          <Plus size={20} className="text-blue-500" />
          Add New Location
        </h3>
        <form onSubmit={handleAddLocation} className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            value={newLocationName}
            onChange={(e) => setNewLocationName(e.target.value)}
            placeholder="Enter new location name (e.g. A-1-1)"
            className="flex-grow bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Plus size={18} />
            Add Location
          </button>
        </form>
        {error && <p className="text-red-500 mt-3 text-sm">{error}</p>}
        {success && <p className="text-green-500 mt-3 text-sm">{success}</p>}
      </div>

      <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-900/50">
            <tr>
              <th className="px-6 py-4 font-bold text-gray-300">Location Name</th>
              <th className="px-6 py-4 font-bold text-gray-300">Usage Count</th>
            </tr>
          </thead>
          <tbody>
            {loading && locations.length === 0 ? (
              <tr>
                <td colSpan={2} className="px-6 py-8 text-center text-gray-500">Loading locations...</td>
              </tr>
            ) : (
              locations.map((location) => (
                <tr key={location.id} className="border-t border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className="px-6 py-4 flex items-center gap-3">
                    <MapPin size={16} className="text-blue-500" />
                    <span className="text-white font-medium">{location.name}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-3 py-1 bg-gray-900 rounded-full text-sm text-gray-400 border border-gray-700">
                      {location.usage_count} accessories
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default LocationsPage;
