import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Trash2, ExternalLink, RefreshCw } from 'lucide-react';
import apiClient from '../apiClient';
import Pagination from '../components/Pagination';
import SKUStatistics from '../components/SKUStatistics';
import AddAccessoryForm from '../components/AddAccessoryForm';

interface Accessory {
  id: number;
  sku: string;
  location: string;
  latest_remark: string;
  updated_at: string;
}

interface AccessoriesResponse {
  accessories: Accessory[];
  total: number;
  page: number;
  total_pages: number;
}

const AccessoriesPage = () => {
  const [accessories, setAccessories] = useState<Accessory[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchAccessories = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<AccessoriesResponse>(`/accessories?page=${page}&per_page=7`);
      setAccessories(response.data.accessories);
      setTotalPages(response.data.total_pages);
      setTotalItems(response.data.total);
    } catch (error) {
      console.error('Failed to fetch accessories:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccessories();
  }, [page, refreshKey]);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this accessory?')) return;

    try {
      await apiClient.delete(`/accessories/${id}`);
      fetchAccessories();
    } catch (error) {
      alert('Failed to delete accessory');
    }
  };

  const refresh = () => setRefreshKey(prev => prev + 1);

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-white">Accessory Management</h1>
        <button 
          onClick={refresh}
          className="p-2 hover:bg-gray-800 rounded-full transition-colors text-gray-400 hover:text-white"
          title="Refresh data"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <AddAccessoryForm onSuccess={() => {
        setPage(1);
        refresh();
      }} />

      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden mb-8 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 font-bold text-gray-300">SKU</th>
                <th className="px-6 py-4 font-bold text-gray-300">Location</th>
                <th className="px-6 py-4 font-bold text-gray-300">Latest Remark</th>
                <th className="px-6 py-4 font-bold text-gray-300">Updated</th>
                <th className="px-6 py-4 font-bold text-gray-300 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && accessories.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading accessories...</td>
                </tr>
              ) : accessories.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">No accessories found</td>
                </tr>
              ) : (
                accessories.map((item) => (
                  <tr key={item.id} className="border-t border-gray-700 hover:bg-gray-700/50 transition-colors">
                    <td className="px-6 py-4">
                      <Link 
                        to={`/sku/${item.sku}`}
                        className="font-semibold text-blue-400 hover:text-blue-300 hover:underline"
                      >
                        {item.sku}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-gray-300">{item.location}</td>
                    <td className="px-6 py-4">
                      <div className="max-w-xs truncate text-gray-400 text-sm" title={item.latest_remark}>
                        {item.latest_remark || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-500 text-xs">
                      {item.updated_at}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center gap-2">
                        <Link 
                          to={`/accessory/${item.id}`}
                          className="p-2 bg-green-600/20 text-green-500 hover:bg-green-600 hover:text-white rounded transition-colors"
                          title="Details"
                        >
                          <ExternalLink size={16} />
                        </Link>
                        <button 
                          className="p-2 bg-red-600/20 text-red-500 hover:bg-red-600 hover:text-white rounded transition-colors"
                          title="Delete"
                          onClick={() => handleDelete(item.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        <div className="bg-gray-900/30 px-6 py-3 flex justify-between items-center border-t border-gray-700">
          <span className="text-sm text-gray-500">
            Showing {(page - 1) * 7 + 1} - {Math.min(page * 7, totalItems)} of {totalItems} items
          </span>
          <Pagination 
            currentPage={page} 
            totalPages={totalPages} 
            onPageChange={setPage} 
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <SKUStatistics />
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 flex items-center justify-center text-gray-500 italic">
          More statistics coming soon...
        </div>
      </div>
    </div>
  );
};

export default AccessoriesPage;
