import { useState, useEffect, useRef } from 'react';
import { Plus, Search } from 'lucide-react';
import apiClient from '../apiClient';

interface Location {
  id: number;
  name: string;
  usage_count: number;
}

interface AddAccessoryFormProps {
  onSuccess: () => void;
}

const AddAccessoryForm = ({ onSuccess }: AddAccessoryFormProps) => {
  const [sku, setSku] = useState('');
  const [location, setLocation] = useState('');
  const [remark, setRemark] = useState('');
  const [locations, setLocations] = useState<Location[]>([]);
  const [allSkus, setAllSkus] = useState<string[]>([]);
  const [filteredSkus, setFilteredSkus] = useState<string[]>([]);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const autocompleteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [locRes, skuRes] = await Promise.all([
          apiClient.get<Location[]>('/locations'),
          apiClient.get<string[]>('/skus')
        ]);
        setLocations(locRes.data);
        setAllSkus(skuRes.data);
      } catch (err) {
        console.error('Failed to fetch form data:', err);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (sku.trim()) {
      const matches = allSkus.filter(s => s.toLowerCase().includes(sku.toLowerCase()));
      setFilteredSkus(matches);
      setShowAutocomplete(matches.length > 0);
    } else {
      setShowAutocomplete(false);
    }
  }, [sku, allSkus]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowAutocomplete(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sku || !location) {
      setError('SKU and Location are required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiClient.post('/accessories', { sku, location, remark });
      if (response.data.success) {
        setSku('');
        setLocation('');
        setRemark('');
        onSuccess();
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to add accessory');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
      <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
        <Plus size={20} className="text-blue-500" />
        Add New Accessory
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-grow min-w-[200px] relative" ref={autocompleteRef}>
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
              <Search size={18} />
            </div>
            <input
              type="text"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              onFocus={() => sku && filteredSkus.length > 0 && setShowAutocomplete(true)}
              placeholder="SKU"
              className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 pl-10 pr-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            {showAutocomplete && (
              <div className="absolute top-full left-0 right-0 bg-gray-900 border border-gray-700 rounded-md mt-1 shadow-xl z-10 max-height-60 overflow-y-auto">
                {filteredSkus.map((s) => (
                  <div
                    key={s}
                    className="px-4 py-2 hover:bg-gray-800 cursor-pointer text-gray-300"
                    onClick={() => {
                      setSku(s);
                      setShowAutocomplete(false);
                    }}
                  >
                    {s}
                  </div>
                ))}
              </div>
            )}
          </div>

          <select
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="flex-grow min-w-[200px] bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Select Location</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.name}>
                {loc.name} ({loc.usage_count} uses)
              </option>
            ))}
          </select>

          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Adding...' : 'Add'}
          </button>
        </div>

        <textarea
          value={remark}
          onChange={(e) => setRemark(e.target.value)}
          placeholder="Remarks (Optional)"
          className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
        />

        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </form>
    </div>
  );
};

export default AddAccessoryForm;
