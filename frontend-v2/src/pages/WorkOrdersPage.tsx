import { useState, useEffect } from 'react';
import { Plus, CheckCircle, XCircle, Trash2, Clock, Check, AlertTriangle, RefreshCw, Eye } from 'lucide-react';
import apiClient from '../apiClient';
import Pagination from '../components/Pagination';
import CreateWorkOrderModal from '../components/CreateWorkOrderModal';
import WorkOrderDetailModal from '../components/WorkOrderDetailModal';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface WorkOrder {
  id: number;
  sku: string;
  accessory_code: string;
  quantity: number;
  status: 'pending' | 'completed' | 'cancelled';
  match_status: 'matched' | 'new_one';
  location: string | null;
  customer_service_name: string | null;
  remark: string;
  created_at: string;
  completed_at: string | null;
}

interface WorkOrdersResponse {
  work_orders: WorkOrder[];
  counts: {
    pending: number;
    completed: number;
    cancelled: number;
  };
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}

const WorkOrdersPage = () => {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [counts, setCounts] = useState({ pending: 0, completed: 0, cancelled: 0 });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [status, setStatus] = useState<'all' | 'pending' | 'completed' | 'cancelled'>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState<WorkOrder | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchWorkOrders = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<WorkOrdersResponse>(`/work-orders?status=${status}&page=${page}&per_page=10`);
      setWorkOrders(response.data.work_orders);
      setCounts(response.data.counts);
      setTotalPages(response.data.pagination.total_pages);
    } catch (error) {
      console.error('Failed to fetch work orders:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkOrders();
  }, [page, status, refreshKey]);

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    try {
      await apiClient.put(`/work-orders/${id}`, { status: newStatus });
      fetchWorkOrders();
    } catch (error) {
      alert('Failed to update work order status');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this work order?')) return;
    try {
      await apiClient.delete(`/work-orders/${id}`);
      fetchWorkOrders();
    } catch (error) {
      alert('Failed to delete work order');
    }
  };

  const refresh = () => setRefreshKey(prev => prev + 1);

  const openDetail = (order: WorkOrder) => {
    setSelectedWorkOrder(order);
    setIsDetailModalOpen(true);
  };

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Work Orders</h1>
          <p className="text-gray-400">Manage and track accessory work orders</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={refresh}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors text-gray-400 hover:text-white border border-gray-700"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-colors shadow-lg"
          >
            <Plus size={20} />
            New Order
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {[
          { label: 'All', value: 'all', count: counts.pending + counts.completed + counts.cancelled },
          { label: 'Pending', value: 'pending', count: counts.pending, color: 'text-yellow-500' },
          { label: 'Completed', value: 'completed', count: counts.completed, color: 'text-green-500' },
          { label: 'Cancelled', value: 'cancelled', count: counts.cancelled, color: 'text-red-500' },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => { setStatus(tab.value as any); setPage(1); }}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-all border',
              status === tab.value
                ? 'bg-gray-700 text-white border-blue-500 shadow-md'
                : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-gray-600'
            )}
          >
            {tab.label}
            <span className={cn('ml-2 px-2 py-0.5 rounded-full bg-gray-900 text-xs', tab.color)}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 font-bold text-gray-300">Order ID</th>
                <th className="px-6 py-4 font-bold text-gray-300">SKU / Code</th>
                <th className="px-6 py-4 font-bold text-gray-300 text-center">Qty</th>
                <th className="px-6 py-4 font-bold text-gray-300">Status</th>
                <th className="px-6 py-4 font-bold text-gray-300">Match Status</th>
                <th className="px-6 py-4 font-bold text-gray-300 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && workOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500 italic">
                    <div className="flex flex-col items-center gap-2">
                      <RefreshCw className="animate-spin text-blue-500" />
                      <span>Loading work orders...</span>
                    </div>
                  </td>
                </tr>
              ) : workOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500 italic">No work orders found</td>
                </tr>
              ) : (
                workOrders.map((order) => (
                  <tr key={order.id} className="border-t border-gray-700 hover:bg-gray-700/30 transition-colors group">
                    <td className="px-6 py-4">
                      <button 
                        onClick={() => openDetail(order)}
                        className="text-left block group/id"
                      >
                        <span className="font-mono text-gray-400 group-hover/id:text-blue-500 transition-colors">#{order.id}</span>
                        <div className="text-[10px] text-gray-600 mt-1 flex items-center gap-1">
                          <Clock size={10} />
                          {order.created_at}
                        </div>
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <button 
                        onClick={() => openDetail(order)}
                        className="text-left group/sku"
                      >
                        <div className="font-bold text-white group-hover/sku:text-blue-400 transition-colors">{order.sku}</div>
                        <div className="text-sm text-blue-400">{order.accessory_code}</div>
                      </button>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="px-2 py-1 bg-gray-900 rounded text-sm text-gray-300">{order.quantity}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider',
                        order.status === 'pending' ? 'bg-yellow-500/10 text-yellow-500' :
                        order.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                        'bg-red-500/10 text-red-500'
                      )}>
                        {order.status === 'pending' && <Clock size={12} />}
                        {order.status === 'completed' && <CheckCircle size={12} />}
                        {order.status === 'cancelled' && <XCircle size={12} />}
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold',
                        order.match_status === 'matched' ? 'bg-blue-500/10 text-blue-400' : 'bg-orange-500/10 text-orange-400'
                      )}>
                        {order.match_status === 'matched' ? (
                          <>
                            <Check size={14} />
                            Matched
                          </>
                        ) : (
                          <>
                            <AlertTriangle size={14} />
                            New One
                          </>
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => openDetail(order)}
                          className="p-2 bg-blue-600/20 text-blue-500 hover:bg-blue-600 hover:text-white rounded transition-colors"
                          title="View Details"
                        >
                          <Eye size={16} />
                        </button>
                        {order.status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleUpdateStatus(order.id, 'completed')}
                              className="p-2 bg-green-600/20 text-green-500 hover:bg-green-600 hover:text-white rounded transition-colors"
                              title="Complete"
                            >
                              <Check size={16} />
                            </button>
                            <button
                              onClick={() => handleUpdateStatus(order.id, 'cancelled')}
                              className="p-2 bg-red-600/20 text-red-500 hover:bg-red-600 hover:text-white rounded transition-colors"
                              title="Cancel"
                            >
                              <XCircle size={16} />
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDelete(order.id)}
                          className="p-2 bg-gray-600/20 text-gray-400 hover:bg-red-600 hover:text-white rounded transition-colors"
                          title="Delete"
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
        
        <div className="bg-gray-900/30 px-6 py-3 flex justify-end items-center border-t border-gray-700">
          <Pagination 
            currentPage={page} 
            totalPages={totalPages} 
            onPageChange={setPage} 
          />
        </div>
      </div>

      <CreateWorkOrderModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => { refresh(); setPage(1); }}
      />

      <WorkOrderDetailModal
        isOpen={isDetailModalOpen}
        workOrder={selectedWorkOrder}
        onClose={() => { setIsDetailModalOpen(false); setSelectedWorkOrder(null); }}
      />
    </div>
  );
};

export default WorkOrdersPage;
