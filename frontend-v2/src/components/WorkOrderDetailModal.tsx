import { useState, useEffect } from 'react';
import { X, MapPin, Tag, Clock, User, ClipboardList } from 'lucide-react';
import apiClient from '../apiClient';

interface Remark {
  id: number;
  content: string;
  created_at: string;
}

interface AccessoryDetail {
  id: number;
  sku: string;
  location: string;
  updated_at: string;
}

interface WorkOrder {
  id: number;
  sku: string;
  accessory_code: string;
  quantity: number;
  status: string;
  match_status: string;
  location: string | null;
  customer_service_name: string | null;
  remark: string;
  created_at: string;
  completed_at: string | null;
}

interface WorkOrderDetailModalProps {
  workOrder: WorkOrder | null;
  isOpen: boolean;
  onClose: () => void;
}

const WorkOrderDetailModal = ({ workOrder, isOpen, onClose }: WorkOrderDetailModalProps) => {
  const [accessory, setAccessory] = useState<AccessoryDetail | null>(null);
  const [remarks, setRemarks] = useState<Remark[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && workOrder && workOrder.match_status === 'matched' && workOrder.location) {
      const fetchAccessoryDetails = async () => {
        setLoading(true);
        try {
          // Find accessory by SKU and Location to get full details and remarks
          // Since the API doesn't have a direct "find by sku+loc", we'll use the SKU detail API
          const response = await apiClient.get(`/sku/${workOrder.sku}`);
          const match = response.data.accessories.find((a: any) => a.location === workOrder.location);
          
          if (match) {
            // Get full details including all remarks
            const detailRes = await apiClient.get(`/accessories/${match.id}`);
            setAccessory(detailRes.data.accessory);
            setRemarks(detailRes.data.remarks);
          }
        } catch (error) {
          console.error('Failed to fetch matched accessory details:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchAccessoryDetails();
    } else {
      setAccessory(null);
      setRemarks([]);
    }
  }, [isOpen, workOrder]);

  if (!isOpen || !workOrder) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-800 w-full max-w-2xl rounded-xl shadow-2xl border border-gray-700 overflow-hidden max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-6 border-b border-gray-700 bg-gray-900/50">
          <div className="flex items-center gap-3">
            <ClipboardList className="text-blue-500" size={24} />
            <h2 className="text-xl font-bold text-white">Work Order #{workOrder.id}</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-6">
          {/* Work Order Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1">Item Details</label>
              <div className="flex items-center gap-2 text-white font-bold text-lg mb-1">
                <Tag size={18} className="text-blue-500" />
                {workOrder.sku}
              </div>
              <div className="text-blue-400 text-sm">{workOrder.accessory_code} (Qty: {workOrder.quantity})</div>
            </div>
            
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1">Status & Assignment</label>
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase ${
                  workOrder.status === 'pending' ? 'bg-yellow-500/10 text-yellow-500' :
                  workOrder.status === 'completed' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                }`}>
                  {workOrder.status}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                  workOrder.match_status === 'matched' ? 'bg-blue-500/10 text-blue-400' : 'bg-orange-500/10 text-orange-400'
                }`}>
                  {workOrder.match_status === 'matched' ? '✓ Matched' : '⚠ New One Required'}
                </span>
              </div>
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <User size={14} />
                {workOrder.customer_service_name || 'Unassigned'}
              </div>
            </div>
          </div>

          {workOrder.remark && (
            <div className="bg-blue-900/10 p-4 rounded-lg border border-blue-900/30">
              <label className="text-xs font-bold text-blue-500 uppercase tracking-wider block mb-1">Order Remark</label>
              <p className="text-gray-300 italic">"{workOrder.remark}"</p>
            </div>
          )}

          {/* Matched Inventory Info */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white border-b border-gray-700 pb-2">Inventory Matching</h3>
            
            {workOrder.match_status === 'matched' ? (
              <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 space-y-4">
                <div className="flex flex-wrap justify-between items-center gap-4">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-600/20 p-2 rounded-lg">
                      <MapPin size={24} className="text-blue-500" />
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 font-bold uppercase">Stored At</div>
                      <div className="text-xl font-bold text-white">{workOrder.location}</div>
                    </div>
                  </div>
                  {accessory && (
                    <div className="text-right">
                      <div className="text-xs text-gray-500 font-bold uppercase">Inventory ID</div>
                      <div className="font-mono text-gray-300">#{accessory.id}</div>
                    </div>
                  )}
                </div>

                {loading ? (
                  <div className="py-4 text-center text-gray-500 animate-pulse">Fetching inventory history...</div>
                ) : accessory ? (
                  <div className="space-y-3 pt-4 border-t border-gray-800">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Clock size={12} />
                      Last inventory update: {accessory.updated_at}
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-bold text-gray-500 uppercase">Accessory Remarks</label>
                      <div className="space-y-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                        {remarks.length > 0 ? remarks.map(r => (
                          <div key={r.id} className="text-sm bg-gray-800 p-2 rounded border border-gray-700/50 text-gray-400">
                            <span className="text-[10px] text-gray-600 block mb-1">{r.created_at}</span>
                            {r.content}
                          </div>
                        )) : (
                          <div className="text-sm text-gray-600 italic">No remarks found for this unit</div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-red-900/10 border border-red-900/20 rounded-lg text-red-400 text-sm">
                    Warning: Inventory record not found. It might have been deleted.
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-orange-900/10 p-8 rounded-lg border border-orange-900/20 text-center space-y-3">
                <AlertTriangle size={32} className="mx-auto text-orange-500" />
                <div className="text-orange-400 font-bold uppercase tracking-widest text-xs">New Unit Required</div>
                <p className="text-gray-400 text-sm max-w-sm mx-auto">
                  No matching inventory was found for this accessory code. A new unit needs to be added to the system.
                </p>
              </div>
            )}
          </div>
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

export default WorkOrderDetailModal;

import { AlertTriangle } from 'lucide-react';
