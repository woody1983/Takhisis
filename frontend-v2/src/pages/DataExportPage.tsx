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
    // Force download attribute with a generic filename to guide Chrome
    // The server-side Content-Disposition should still override this in many browsers,
    // but providing it here helps Chrome identify the file type.
    link.download = 'accessories_export.csv';
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
    // Force download attribute with a generic filename to guide Chrome
    link.download = 'work-orders_export.csv';
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
        <h1 className="text-3xl font-bold text-white mb-2">Data Export</h1>
        <p className="text-gray-400">Download system data as CSV files</p>
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
              <p className="text-gray-400 text-sm">Accessory inventory data</p>
            </div>
          </div>

          <p className="text-gray-400 text-sm mb-6">
            Export all accessory information, including: ID, SKU, Location, Update Time, and Latest Remark
          </p>

          <button
            onClick={handleExportAccessories}
            disabled={exportStatus.accessories === 'loading'}
            className={`w-full py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${exportStatus.accessories === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
          >
            {exportStatus.accessories === 'success' ? (
              <>
                <CheckCircle size={20} />
                Download Successful
              </>
            ) : (
              <>
                <Download size={20} />
                {exportStatus.accessories === 'loading' ? 'Exporting...' : 'Export Accessories (CSV)'}
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
              <p className="text-gray-400 text-sm">Work Order data</p>
            </div>
          </div>

          <p className="text-gray-400 text-sm mb-6">
            Export all work order information, including: ID, SKU, Accessory Code, Quantity, Status, Match Status, etc.
          </p>

          <button
            onClick={handleExportWorkOrders}
            disabled={exportStatus.workOrders === 'loading'}
            className={`w-full py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${exportStatus.workOrders === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
              }`}
          >
            {exportStatus.workOrders === 'success' ? (
              <>
                <CheckCircle size={20} />
                Download Successful
              </>
            ) : (
              <>
                <Download size={20} />
                {exportStatus.workOrders === 'loading' ? 'Exporting...' : 'Export Work Orders (CSV)'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Info Section */}
      <div className="mt-8 bg-gray-800/50 rounded-xl border border-gray-700 p-6">
        <h3 className="text-lg font-bold text-white mb-4">Export Instructions</h3>
        <ul className="space-y-2 text-gray-400 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">•</span>
            <span>CSV files can be opened with Excel, Google Sheets, or any text editor</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">•</span>
            <span>Data is sorted by update time in reverse order, with the latest records first</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">•</span>
            <span>Import functionality will be added in a future version</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default DataExportPage;
