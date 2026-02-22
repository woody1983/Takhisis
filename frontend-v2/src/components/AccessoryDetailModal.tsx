import { useState, useEffect } from 'react';
import { X, Clock, MapPin, Tag, Trash2, Save } from 'lucide-react';
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

interface AccessoryDetailModalProps {
  accessoryId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate?: () => void;
}

const AccessoryDetailModal = ({ accessoryId, isOpen, onClose, onUpdate }: AccessoryDetailModalProps) => {
  const [accessory, setAccessory] = useState<Accessory | null>(null);
  const [remarks, setRemarks] = useState<Remark[]>([]);
  const [newRemark, setNewRemark] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchDetails = async () => {
    if (!accessoryId) return;
    setLoading(true);
    try {
      const response = await apiClient.get(`/accessories/${accessoryId}`);
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
    if (isOpen && accessoryId) {
      fetchDetails();
    } else {
      setAccessory(null);
      setRemarks([]);
      setNewRemark('');
    }
  }, [isOpen, accessoryId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessoryId) return;
    setIsUpdating(true);
    try {
      await apiClient.put(`/accessories/${accessoryId}`, {
        location: newLocation,
        new_remark: newRemark
      });
      setNewRemark('');
      fetchDetails();
      if (onUpdate) onUpdate();
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

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="bg-gray-800 w-full max-w-3xl rounded-xl shadow-2xl border border-gray-700 overflow-hidden max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-6 border-b border-gray-700 bg-gray-900/50">
          <div className="flex items-center gap-3">
            <Tag className="text-blue-500" size={24} />
            <h2 className="text-xl font-bold text-white">
              {loading ? 'Loading...' : accessory?.sku || 'Accessory Details'}
            </h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-8 flex-grow">
          {loading ? (
            <div className="py-20 text-center text-gray-500 italic">Loading details...</div>
          ) : accessory ? (
            <>
              <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700 shadow-inner">
                <form onSubmit={handleUpdate} className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <MapPin size={14} />
                        Location
                      </label>
                      <input
                        type="text"
                        value={newLocation}
                        onChange={(e) => setNewLocation(e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                      />
                    </div>
                    <div className="flex flex-col justify-end pb-1">
                      <p className="text-[10px] text-gray-500 font-bold uppercase flex items-center gap-1">
                        <Clock size={12} />
                        Last updated
                      </p>
                      <p className="text-sm text-gray-400">{accessory.updated_at}</p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Add New Remark</label>
                    <textarea
                      value={newRemark}
                      onChange={(e) => setNewRemark(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-28 transition-all shadow-sm resize-none"
                      placeholder="Enter update details, removal notes, or other information..."
                    />
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={isUpdating}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-bold py-2.5 px-8 rounded-lg transition-all shadow-lg flex items-center gap-2"
                    >
                      {isUpdating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Updating...
                        </>
                      ) : (
                        <>
                          <Save size={18} />
                          Save Changes
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white border-b border-gray-700 pb-2 flex items-center gap-2 uppercase tracking-widest">
                  <Clock size={16} className="text-blue-500" />
                  Remark History
                </h3>
                <div className="space-y-3">
                  {remarks.length === 0 ? (
                    <div className="bg-gray-900/30 rounded-lg p-8 text-center text-gray-600 italic border border-dashed border-gray-700">
                      No remarks recorded for this item
                    </div>
                  ) : (
                    remarks.map((remark) => (
                      <div key={remark.id} className="group bg-gray-900/40 rounded-xl p-4 border border-gray-700/50 hover:border-gray-600 transition-all">
                        <div className="flex justify-between items-start mb-3">
                          <span className="text-[10px] font-bold text-gray-500 uppercase font-mono bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
                            {remark.created_at}
                          </span>
                          <button
                            onClick={() => handleDeleteRemark(remark.id)}
                            className="text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-1 hover:bg-red-500/10 rounded"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{remark.content}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="py-20 text-center text-red-400">Accessory not found</div>
          )}
        </div>

        <div className="p-6 bg-gray-900/50 border-t border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white font-bold rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccessoryDetailModal;
