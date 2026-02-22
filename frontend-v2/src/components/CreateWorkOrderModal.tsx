import { useState } from 'react';
import { X } from 'lucide-react';
import apiClient from '../apiClient';

interface CreateWorkOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CreateWorkOrderModal = ({ isOpen, onClose, onSuccess }: CreateWorkOrderModalProps) => {
  const [formData, setFormData] = useState({
    sku: '',
    accessory_code: '',
    quantity: 1,
    customer_service_name: '',
    remark: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiClient.post('/work-orders', formData);
      if (response.data.success) {
        onSuccess();
        onClose();
        setFormData({
          sku: '',
          accessory_code: '',
          quantity: 1,
          customer_service_name: '',
          remark: ''
        });
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create work order');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-800 w-full max-w-md rounded-xl shadow-2xl border border-gray-700 overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Create Work Order</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">SKU</label>
            <input
              type="text"
              required
              value={formData.sku}
              onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter SKU"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Accessory Code</label>
            <input
              type="text"
              required
              value={formData.accessory_code}
              onChange={(e) => setFormData({ ...formData, accessory_code: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. partA"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Quantity</label>
            <input
              type="number"
              required
              min="1"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) })}
              className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">CS Name</label>
            <input
              type="text"
              value={formData.customer_service_name}
              onChange={(e) => setFormData({ ...formData, customer_service_name: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Customer Service Name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Remark</label>
            <textarea
              value={formData.remark}
              onChange={(e) => setFormData({ ...formData, remark: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
              placeholder="Optional remarks"
            />
          </div>

          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}

          <div className="pt-4 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateWorkOrderModal;
