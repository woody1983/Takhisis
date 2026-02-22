import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Box, Eye } from 'lucide-react';
import apiClient from '../apiClient';
import AccessoryDetailModal from '../components/AccessoryDetailModal';

interface Accessory {
  id: number;
  sku: string;
  location: string;
  latest_remark: string;
  updated_at: string;
}

interface SkuDetail {
  base_sku: string;
  accessories: Accessory[];
  locations: string[];
  total_count: number;
}

const SKUDetailPage = () => {
  const { sku } = useParams<{ sku: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SkuDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAccessoryId, setSelectedAccessoryId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchSkuDetail = async () => {
    try {
      const response = await apiClient.get<SkuDetail>(`/sku/${sku}`);
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch SKU details:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkuDetail();
  }, [sku]);

  const openAccessoryDetail = (id: number) => {
    setSelectedAccessoryId(id);
    setIsModalOpen(true);
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading SKU details...</div>;
  if (!data) return <div className="p-8 text-center text-gray-400">SKU not found</div>;

  return (
    <div className="container mx-auto p-4 max-w-5xl">
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        Back to Dashboard
      </button>

      <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 shadow-xl mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="bg-blue-600 p-3 rounded-lg">
              <Box size={32} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">{data.base_sku}</h1>
              <p className="text-gray-400">Base SKU Information</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-gray-900 px-6 py-3 rounded-lg border border-gray-700 text-center">
              <div className="text-2xl font-bold text-blue-500">{data.total_count}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Total Units</div>
            </div>
            <div className="bg-gray-900 px-6 py-3 rounded-lg border border-gray-700 text-center">
              <div className="text-2xl font-bold text-green-500">{data.locations.length}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Locations</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <MapPin size={14} />
              Found at
            </h2>
            <div className="flex flex-wrap gap-2">
              {data.locations.map(loc => (
                <span key={loc} className="px-3 py-1 bg-gray-900 text-gray-300 rounded-md border border-gray-700 text-sm">
                  {loc}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 bg-gray-900/30">
              <h2 className="font-bold text-white">Associated Accessories</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-gray-900/50">
                  <tr>
                    <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase">Specific SKU</th>
                    <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase">Location</th>
                    <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase text-center">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.accessories.map((item) => (
                    <tr key={item.id} className="border-t border-gray-700 hover:bg-gray-700/50 transition-colors">
                      <td className="px-6 py-4">
                        <span className="font-mono text-blue-400 font-medium">{item.sku}</span>
                      </td>
                      <td className="px-6 py-4 text-gray-300">
                        <div className="flex items-center gap-2">
                          <MapPin size={14} className="text-gray-600" />
                          {item.location}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => openAccessoryDetail(item.id)}
                          className="inline-flex items-center gap-1 text-sm text-blue-500 hover:text-blue-400 font-medium"
                        >
                          View Details
                          <Eye size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <AccessoryDetailModal
        isOpen={isModalOpen}
        accessoryId={selectedAccessoryId}
        onClose={() => setIsModalOpen(false)}
        onUpdate={fetchSkuDetail}
      />
    </div>
  );
};

export default SKUDetailPage;
