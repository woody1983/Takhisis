import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../apiClient';

type SkuStat = [string, number];

const SKUStatistics = () => {
  const [stats, setStats] = useState<SkuStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get<SkuStat[]>('/sku-stats');
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch SKU statistics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-400">Loading statistics...</div>;
  if (stats.length === 0) return <div className="p-8 text-center text-gray-400">No SKU statistics available</div>;

  const maxCount = stats[0][1];

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-bold mb-6 text-white border-b-2 border-blue-500 pb-2 inline-block">
        SKU Statistics (Grouped by Base SKU)
      </h2>
      <div className="space-y-4">
        {stats.map(([sku, count]) => (
          <Link key={sku} to={`/sku/${sku}`} className="group block">
            <div className="flex items-center gap-4 mb-1">
              <span className="text-sm font-medium text-gray-300 w-32 truncate text-right" title={sku}>
                {sku}
              </span>
              <div className="flex-grow bg-gray-700 h-8 rounded overflow-hidden relative">
                <div
                  className="bg-blue-600 h-full transition-all duration-500 ease-out group-hover:bg-blue-500"
                  style={{ width: `${(count / maxCount) * 100}%` }}
                >
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-white">
                    {count}
                  </span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default SKUStatistics;
