import { useState, useEffect } from 'react';
import apiClient from '../apiClient';

interface SKUOrderStat {
    sku: string;
    inventory: number;
    pending: number;
    completed: number;
}

const SKUOrderAnalytics = ({ refreshKey = 0 }: { refreshKey?: number }) => {
    const [stats, setStats] = useState<SKUOrderStat[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            setLoading(true);
            try {
                const response = await apiClient.get<SKUOrderStat[]>('/sku-order-stats');
                setStats(response.data);
            } catch (error) {
                console.error('Failed to fetch SKU order analytics:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [refreshKey]);

    if (loading) return <div className="bg-gray-800 rounded-lg p-6 border border-gray-700"><div className="p-8 text-center text-gray-400">Loading analytics...</div></div>;
    if (stats.length === 0) return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-bold mb-6 text-white border-b-2 border-emerald-500 pb-2 inline-block">
                Inventory vs Work Orders
            </h2>
            <div className="p-8 text-center text-gray-400">No data available yet</div>
        </div>
    );

    const maxTotal = Math.max(...stats.map(s => s.inventory + s.pending + s.completed), 1);

    return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-bold mb-6 text-white border-b-2 border-emerald-500 pb-2 inline-block">
                Inventory vs Work Orders (Stacked)
            </h2>

            {/* Legend */}
            <div className="flex gap-4 mb-6 text-xs justify-end">
                <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-blue-500 inline-block"></span>
                    <span className="text-gray-400">Inventory</span>
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-amber-500 inline-block"></span>
                    <span className="text-gray-400">Pending</span>
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-emerald-500 inline-block"></span>
                    <span className="text-gray-400">Completed</span>
                </span>
            </div>

            <div className="space-y-6">
                {stats.map((item) => {
                    const total = item.inventory + item.pending + item.completed;
                    return (
                        <div key={item.sku} className="group">
                            <div className="flex justify-between items-end mb-1">
                                <span className="text-xs font-bold text-gray-300 truncate" title={item.sku}>
                                    {item.sku}
                                </span>
                                <span className="text-[10px] text-gray-500 font-mono">
                                    Total: {total}
                                </span>
                            </div>
                            <div className="flex-grow bg-gray-900/50 h-6 rounded-md overflow-hidden flex border border-gray-700 shadow-inner">
                                {/* Inventory segment */}
                                {item.inventory > 0 && (
                                    <div
                                        className="bg-blue-500 h-full transition-all duration-500 ease-out border-r border-black/10 flex items-center justify-center"
                                        style={{ width: `${(item.inventory / maxTotal) * 100}%` }}
                                        title={`Inventory: ${item.inventory}`}
                                    >
                                        {(item.inventory / maxTotal) > 0.05 && (
                                            <span className="text-[10px] font-bold text-white drop-shadow-sm">{item.inventory}</span>
                                        )}
                                    </div>
                                )}
                                {/* Pending segment */}
                                {item.pending > 0 && (
                                    <div
                                        className="bg-amber-500 h-full transition-all duration-500 ease-out border-r border-black/10 flex items-center justify-center"
                                        style={{ width: `${(item.pending / maxTotal) * 100}%` }}
                                        title={`Pending: ${item.pending}`}
                                    >
                                        {(item.pending / maxTotal) > 0.05 && (
                                            <span className="text-[10px] font-bold text-white drop-shadow-sm">{item.pending}</span>
                                        )}
                                    </div>
                                )}
                                {/* Completed segment */}
                                {item.completed > 0 && (
                                    <div
                                        className="bg-emerald-500 h-full transition-all duration-500 ease-out flex items-center justify-center"
                                        style={{ width: `${(item.completed / maxTotal) * 100}%` }}
                                        title={`Completed: ${item.completed}`}
                                    >
                                        {(item.completed / maxTotal) > 0.05 && (
                                            <span className="text-[10px] font-bold text-white drop-shadow-sm">{item.completed}</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default SKUOrderAnalytics;
