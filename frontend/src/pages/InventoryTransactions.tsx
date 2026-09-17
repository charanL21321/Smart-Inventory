import React, { useEffect, useState } from 'react';
import { inventoryApi } from '../api/inventory';
import { productsApi } from '../api/products';
import { InventoryTransaction, Product, TransactionType } from '../types';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { Modal } from '../components/common/Modal';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Receipt, RefreshCw, Eye } from 'lucide-react';

export const InventoryTransactions: React.FC = () => {
  const [transactions, setTransactions] = useState<InventoryTransaction[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  // Selected for Detail Modal
  const [activeTx, setActiveTx] = useState<InventoryTransaction | null>(null);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const [txData, pData] = await Promise.all([
        inventoryApi.getTransactions({
          product_id: selectedProduct ? Number(selectedProduct) : undefined,
          transaction_type: (selectedType as TransactionType) || undefined,
        }),
        productsApi.getAll(),
      ]);
      setTransactions(txData);
      setProducts(pData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load transaction ledger.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [selectedProduct, selectedType]);

  const isPositiveDelta = (type: TransactionType) =>
    type === 'STOCK_IN' || type === 'ADJUSTMENT_IN';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Inventory Ledger Audit Trail</h2>
          <p className="text-sm text-slate-500">
            Immutable historical record of every stock movement, sale dispatch, and manual reconciliation.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={loadTransactions} icon={<RefreshCw className="h-3.5 w-3.5" />}>
          Refresh Ledger
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="card p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Select
            options={products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
            placeholder="All Products"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
          />
        </div>
        <div>
          <Select
            options={[
              { value: 'STOCK_IN', label: 'Stock In' },
              { value: 'STOCK_OUT', label: 'Stock Out' },
              { value: 'ADJUSTMENT_IN', label: 'Adjustment In' },
              { value: 'ADJUSTMENT_OUT', label: 'Adjustment Out' },
            ]}
            placeholder="All Transaction Types"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          />
        </div>
        <div className="flex items-center text-xs text-slate-500">
          Showing {transactions.length} audit entries
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadTransactions} />}

      {loading ? (
        <Spinner size="lg" message="Loading transaction audit trail..." className="py-12" />
      ) : transactions.length === 0 ? (
        <EmptyState
          title="No transactions logged"
          description="No inventory transactions match your criteria."
          icon={<Receipt className="h-10 w-10" />}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Product</th>
                <th>Type</th>
                <th>Quantity Delta</th>
                <th>Stock Before &rarr; After</th>
                <th>Reason / Reference</th>
                <th>User ID</th>
                <th className="text-right">Detail</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => {
                const positive = isPositiveDelta(tx.transaction_type);
                return (
                  <tr key={tx.id}>
                    <td className="text-xs text-slate-500 whitespace-nowrap">
                      {new Date(tx.created_at).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="font-semibold text-slate-900">
                      {tx.product?.name || `Product #${tx.product_id}`}
                      <div className="text-xs text-slate-400 font-normal">
                        {tx.product?.sku}
                      </div>
                    </td>
                    <td>
                      <StatusBadge status={tx.transaction_type} />
                    </td>
                    <td className={`font-bold ${positive ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {positive ? `+${tx.quantity}` : `-${tx.quantity}`}
                    </td>
                    <td className="text-xs text-slate-600">
                      <span className="text-slate-400">{tx.previous_stock}</span> &rarr;{' '}
                      <span className="font-semibold text-slate-800">{tx.resulting_stock}</span>
                    </td>
                    <td className="text-xs text-slate-600 max-w-xs truncate">
                      {tx.reason || tx.reference || '—'}
                    </td>
                    <td className="text-xs text-slate-500">#{tx.performed_by}</td>
                    <td className="text-right">
                      <button
                        onClick={() => setActiveTx(tx)}
                        className="p-1 text-slate-400 hover:text-indigo-600 rounded transition-colors"
                        title="View Full Ledger Detail"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      <Modal
        isOpen={!!activeTx}
        onClose={() => setActiveTx(null)}
        title="Transaction Audit Record"
      >
        {activeTx && (
          <div className="space-y-4 text-sm">
            <div className="flex items-center justify-between pb-3 border-b">
              <span className="text-slate-500">Transaction ID:</span>
              <span className="font-mono font-bold text-slate-900">#{activeTx.id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Product:</span>
              <span className="font-semibold text-slate-900">
                {activeTx.product?.name || `Product #${activeTx.product_id}`}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Type:</span>
              <StatusBadge status={activeTx.transaction_type} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Quantity:</span>
              <span className="font-bold text-slate-900">{activeTx.quantity} units</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Stock Transition:</span>
              <span className="font-mono">
                {activeTx.previous_stock} &rarr; {activeTx.resulting_stock}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Logged By (User ID):</span>
              <span className="font-medium text-slate-800">#{activeTx.performed_by}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Recorded At:</span>
              <span className="text-slate-700">{new Date(activeTx.created_at).toLocaleString()}</span>
            </div>
            {activeTx.reference && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Document Reference:</span>
                <span className="font-mono text-slate-800">{activeTx.reference}</span>
              </div>
            )}
            <div className="pt-2">
              <span className="block text-slate-500 mb-1">Reason / Notes:</span>
              <p className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-700 text-xs">
                {activeTx.reason || 'No audit note specified.'}
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
