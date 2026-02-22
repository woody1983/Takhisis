import { useState } from 'react';
import { Download, FileSpreadsheet, CheckCircle } from 'lucide-react';

const DataExportPage = () => {
  const [exportStatus, setExportStatus] = useState<{
    accessories: 'idle' | 'loading' | 'success';
    workOrders: 'idle' | 'loading' | 'success';
  }>({
    accessories: 'idle',
    workOrders: 'idle',
  });

  const handleExportAccessories = () => {
    setExportStatus((prev) => ({ ...prev, accessories: 'loading' }));
    
    // Trigger download via anchor tag
    const link = document.createElement('a');
    link.href = '/api/export/accessories';
    link.download = 'accessories.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show success message briefly
    setTimeout(() => {
      setExportStatus((prev) => ({ ...prev, accessories: 'success' }));
      setTimeout(() => {
        setExportStatus((prev) => ({ ...prev, accessories: 'idle' }));
      }, 2000);
    }, 500);
  };

  const handleExportWorkOrders = () => {
    setExportStatus((prev) => ({ ...prev, workOrders: 'loading' }));
    
    // Trigger download via anchor tag
    const link = document.createElement('a');
    link.href = '/api/export/work-orders';
    link.download = 'work-orders.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show success message briefly
    setTimeout(() => {
      setExportStatus((prev) => ({ ...prev, workOrders: 'success' }));
      setTimeout(() => {
        setExportStatus((prev) => ({ ...prev, workOrders: 'idle' }));
      }, 2000);
    }, 500);
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">数据导出</h1>
        <p className="text-gray-400">下载系统数据为 CSV 格式文件</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Accessories Export Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 shadow-xl">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-blue-600/20 rounded-lg">
              <FileSpreadsheet size={28} className="text-blue-500" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Accessories</h3>
              <p className="text-gray-400 text-sm">配件库存数据</p>
            </div>
          </div>
          
          <p className="text-gray-400 text-sm mb-6">
            导出所有配件信息，包括：ID、SKU、位置、更新时间、最新备注
          </p>
          
          <button
            onClick={handleExportAccessories}
            disabled={exportStatus.accessories === 'loading'}
            className={`w-full py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${
              exportStatus.accessories === 'success'
                ? 'bg-green-600 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {exportStatus.accessories === 'success' ? (
              <>
                <CheckCircle size={20} />
                下载成功
              </>
            ) : (
              <>
                <Download size={20} />
                {exportStatus.accessories === 'loading' ? '导出中...' : 'Export Accessories (CSV)'}
              </>
            )}
          </button>
        </div>

        {/* Work Orders Export Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 shadow-xl">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-emerald-600/20 rounded-lg">
              <FileSpreadsheet size={28} className="text-emerald-500" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Work Orders</h3>
              <p className="text-gray-400 text-sm">工单数据</p>
            </div>
          </div>
          
          <p className="text-gray-400 text-sm mb-6">
            导出所有工单信息，包括：ID、SKU、配件代码、数量、状态、匹配状态等
          </p>
          
          <button
            onClick={handleExportWorkOrders}
            disabled={exportStatus.workOrders === 'loading'}
            className={`w-full py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${
              exportStatus.workOrders === 'success'
                ? 'bg-green-600 text-white'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
            }`}
          >
            {exportStatus.workOrders === 'success' ? (
              <>
                <CheckCircle size={20} />
                下载成功
              </>
            ) : (
              <>
                <Download size={20} />
                {exportStatus.workOrders === 'loading' ? '导出中...' : 'Export Work Orders (CSV)'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Info Section */}
      <div className="mt-8 bg-gray-800/50 rounded-xl border border-gray-700 p-6">
        <h3 className="text-lg font-bold text-white mb-4">导出说明</h3>
        <ul className="space-y-2 text-gray-400 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">•</span>
            <span>CSV 文件可用 Excel、Google Sheets 或任何文本编辑器打开</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">•</span>
            <span>数据按更新时间倒序排列，最新的记录在前</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">•</span>
            <span>导入功能将在后续版本中添加</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default DataExportPage;
