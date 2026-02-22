import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, MapPin, Tag, Trash2 } from 'lucide-react';
import apiClient from '../apiClient';

interface Remark {
  id: number;
  content: string;
  created_at: string;
}

interface Accessory {
  id: number;
  sku: string;
  location: string;
  updated_at: string;
}

const AccessoryDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [accessory, setAccessory] = useState<Accessory | null>(null);
  const [remarks, setRemarks] = useState<Remark[]>([]);
  const [newRemark, setNewRemark] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchDetails = async () => {
    try {
      const response = await apiClient.get(`/accessories/${id}`);
      setAccessory(response.data.accessory);
      setRemarks(response.data.remarks);
      setNewLocation(response.data.accessory.location);
    } catch (error) {
      console.error('Failed to fetch details:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    try {
      await apiClient.put(`/accessories/${id}`, {
        location: newLocation,
        new_remark: newRemark
      });
      setNewRemark('');
      fetchDetails();
    } catch (error) {
      alert('Failed to update accessory');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteRemark = async (remarkId: number) => {
    if (!confirm('Delete this remark?')) return;
    try {
      await apiClient.delete(`/remarks/${remarkId}`);
      fetchDetails();
    } catch (error) {
      alert('Failed to delete remark');
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading details...</div>;
  if (!accessory) return <div className="p-8 text-center text-gray-400">Accessory not found</div>;

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        Back to Dashboard
      </button>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Main Info */}
        <div className="md:col-span-2 space-y-8">
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-xl">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
              <Tag className="text-blue-500" />
              {accessory.sku}
            </h1>

            <form onSubmit={handleUpdate} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1 flex items-center gap-2">
                    <MapPin size={14} />
                    Location
                  </label>
                  <input
                    type="text"
                    value={newLocation}
                    onChange={(e) => setNewLocation(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex flex-col justify-end">
                  <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                    <Clock size={12} />
                    Last updated: {accessory.updated_at}
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Add Remark</label>
                <textarea
                  value={newRemark}
                  onChange={(e) => setNewRemark(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                  placeholder="Type a new remark here..."
                />
              </div>

              <button
                type="submit"
                disabled={isUpdating}
                className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-8 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {isUpdating ? 'Updating...' : 'Save Changes'}
              </button>
            </form>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-xl">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Clock className="text-blue-500" />
              Remark History
            </h2>
            <div className="space-y-4">
              {remarks.length === 0 ? (
                <p className="text-gray-500 italic">No remarks yet</p>
              ) : (
                remarks.map((remark) => (
                  <div key={remark.id} className="group bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs text-gray-500 font-mono">{remark.created_at}</span>
                      <button
                        onClick={() => handleDeleteRemark(remark.id)}
                        className="text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                    <p className="text-gray-300 whitespace-pre-wrap">{remark.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-blue-600/10 rounded-xl p-6 border border-blue-500/20">
            <h3 className="text-blue-400 font-bold mb-2">Inventory Stats</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              This accessory is currently stored in <span className="text-white font-bold">{accessory.location}</span>.
              There are {remarks.length} remarks on record.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessoryDetailPage;
