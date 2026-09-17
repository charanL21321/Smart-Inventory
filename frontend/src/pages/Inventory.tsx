import React, { useEffect, useState } from 'react';
import { inventoryApi } from '../api/inventory';
import { productsApi } from '../api/products';
import {
  Inventory,
  Product,
  StockInRequest,
  StockOutRequest,
  StockAdjustmentRequest,
  AdjustmentType,
} from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Modal } from '../components/common/Modal';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import {
  Warehouse,
  ArrowDownLeft,
  ArrowUpRight,
  Sliders,
  Filter,
  RefreshCw,
} from 'lucide-react';

export const InventoryPage: React.FC = () => {
  const { hasRole } = useAuth();
  const canAdjust = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [inventoryList, setInventoryList] = useState<Inventory[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterLowStock, setFilterLowStock] = useState(false);
  const [filterOutOfStock, setFilterOutOfStock] = useState(false);

  // Operation Modals State
  const [modalType, setModalType] = useState<'IN' | 'OUT' | 'ADJUST' | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<number | ''>('');
  const [opQuantity, setOpQuantity] = useState<number>(1);
  const [opReason, setOpReason] = useState('');
  const [opReference, setOpReference] = useState('');
  const [adjustmentType, setAdjustmentType] = useState<AdjustmentType>('IN');
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [invData, pData] = await Promise.all([
        inventoryApi.getAll({
          low_stock: filterLowStock || undefined,
          out_of_stock: filterOutOfStock || undefined,
        }),
        productsApi.getAll({ is_active: true }),
      ]);
      setInventoryList(invData);
      setProducts(pData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load inventory balances.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterLowStock, filterOutOfStock]);

  const openOperationModal = (
    type: 'IN' | 'OUT' | 'ADJUST',
    productId?: number
  ) => {
    setModalType(type);
    setSelectedProductId(productId || (products[0]?.id ?? ''));
    setOpQuantity(1);
    setOpReason('');
    setOpReference('');
    setAdjustmentType('IN');
    setModalError(null);
  };

  const handleOperationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId) {
      setModalError('Please select a product.');
      return;
    }
    if (opQuantity <= 0) {
      setModalError('Quantity must be greater than 0.');
      return;
    }

    try {
      setSubmitting(true);
      setModalError(null);

      if (modalType === 'IN') {
        const payload: StockInRequest = {
          product_id: Number(selectedProductId),
          quantity: Number(opQuantity),
          reason: opReason || undefined,
          reference: opReference || undefined,
        };
        await inventoryApi.stockIn(payload);
      } else if (modalType === 'OUT') {
        const payload: StockOutRequest = {
          product_id: Number(selectedProductId),
          quantity: Number(opQuantity),
          reason: opReason || undefined,
          reference: opReference || undefined,
        };
        await inventoryApi.stockOut(payload);
      } else if (modalType === 'ADJUST') {
        if (!opReason.trim()) {
          setModalError('Adjustment reason is strictly required for audit ledger.');
          setSubmitting(false);
          return;
        }
        const payload: StockAdjustmentRequest = {
          product_id: Number(selectedProductId),
          adjustment_type: adjustmentType,
          quantity: Number(opQuantity),
          reason: opReason,
        };
        await inventoryApi.adjustment(payload);
      }

      setModalType(null);
      loadData();
    } catch (err: any) {
      setModalError(err?.message || 'Operation failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Inventory Stock Balances</h2>
          <p className="text-sm text-slate-500">
            Real-time tracking of current, reserved, and available stock units.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="secondary"
            onClick={() => openOperationModal('IN')}
            icon={<ArrowDownLeft className="h-4 w-4 text-emerald-600" />}
          >
            Stock In
          </Button>
          <Button
            variant="secondary"
            onClick={() => openOperationModal('OUT')}
            icon={<ArrowUpRight className="h-4 w-4 text-rose-600" />}
          >
            Stock Out
          </Button>
          {canAdjust && (
            <Button
              variant="primary"
              onClick={() => openOperationModal('ADJUST')}
              icon={<Sliders className="h-4 w-4" />}
            >
              Manual Adjustment
            </Button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5" /> Filters:
          </span>
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={filterLowStock}
              onChange={(e) => {
                setFilterLowStock(e.target.checked);
                if (e.target.checked) setFilterOutOfStock(false);
              }}
              className="rounded text-indigo-600"
            />
            Low Stock Only
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={filterOutOfStock}
              onChange={(e) => {
                setFilterOutOfStock(e.target.checked);
                if (e.target.checked) setFilterLowStock(false);
              }}
              className="rounded text-indigo-600"
            />
            Out of Stock Only
          </label>
        </div>
        <Button variant="secondary" size="sm" onClick={loadData} icon={<RefreshCw className="h-3.5 w-3.5" />}>
          Refresh
        </Button>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadData} />}

      {/* Table */}
      {loading ? (
        <Spinner size="lg" message="Loading inventory balances..." className="py-12" />
      ) : inventoryList.length === 0 ? (
        <EmptyState
          title="No inventory records"
          description="No stock balance records found for the selected filter."
          icon={<Warehouse className="h-10 w-10" />}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Current Stock</th>
                <th>Reserved Stock</th>
                <th>Available Stock</th>
                <th>Status</th>
                <th>Last Restocked</th>
                <th className="text-right">Quick Actions</th>
              </tr>
            </thead>
            <tbody>
              {inventoryList.map((inv) => (
                <tr key={inv.id}>
                  <td className="font-semibold text-slate-900">
                    {inv.product?.name || `Product #${inv.product_id}`}
                  </td>
                  <td className="font-mono text-xs text-slate-600">{inv.product?.sku || '—'}</td>
                  <td>{inv.current_stock}</td>
                  <td>{inv.reserved_stock}</td>
                  <td className="font-bold text-slate-900">{inv.available_stock}</td>
                  <td>
                    <StatusBadge status={inv.status} />
                  </td>
                  <td className="text-xs text-slate-500">
                    {inv.last_restocked_at
                      ? new Date(inv.last_restocked_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })
                      : 'Never'}
                  </td>
                  <td className="text-right">
                    <div className="inline-flex gap-1.5">
                      <button
                        onClick={() => openOperationModal('IN', inv.product_id)}
                        className="btn btn-secondary btn-sm p-1.5"
                        title="Stock In"
                      >
                        <ArrowDownLeft className="h-3.5 w-3.5 text-emerald-600" />
                      </button>
                      <button
                        onClick={() => openOperationModal('OUT', inv.product_id)}
                        className="btn btn-secondary btn-sm p-1.5"
                        title="Stock Out"
                      >
                        <ArrowUpRight className="h-3.5 w-3.5 text-rose-600" />
                      </button>
                      {canAdjust && (
                        <button
                          onClick={() => openOperationModal('ADJUST', inv.product_id)}
                          className="btn btn-secondary btn-sm p-1.5"
                          title="Adjust"
                        >
                          <Sliders className="h-3.5 w-3.5 text-indigo-600" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stock Operation Modal */}
      <Modal
        isOpen={modalType !== null}
        onClose={() => setModalType(null)}
        title={
          modalType === 'IN'
            ? 'Receive Stock (Stock In)'
            : modalType === 'OUT'
            ? 'Dispatch Stock (Stock Out)'
            : 'Audit Stock Adjustment'
        }
      >
        {modalError && <ErrorAlert message={modalError} className="mb-4" />}
        <form onSubmit={handleOperationSubmit} className="space-y-4">
          <Select
            label="Target Product"
            required
            options={products.map((p) => ({
              value: p.id,
              label: `${p.name} (${p.sku})`,
            }))}
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(Number(e.target.value))}
            disabled={submitting}
          />

          {modalType === 'ADJUST' && (
            <Select
              label="Adjustment Direction"
              required
              options={[
                { value: 'IN', label: 'IN (Increment count)' },
                { value: 'OUT', label: 'OUT (Decrement count)' },
              ]}
              value={adjustmentType}
              onChange={(e) => setAdjustmentType(e.target.value as AdjustmentType)}
              disabled={submitting}
            />
          )}

          <Input
            label="Quantity"
            type="number"
            min="1"
            required
            value={opQuantity}
            onChange={(e) => setOpQuantity(Number(e.target.value))}
            disabled={submitting}
          />

          {modalType === 'ADJUST' ? (
            <div>
              <label className="label">
                Mandatory Audit Reason <span className="text-rose-600">*</span>
              </label>
              <textarea
                className="textarea"
                rows={3}
                required
                value={opReason}
                onChange={(e) => setOpReason(e.target.value)}
                placeholder="Explain why manual correction is being performed (e.g., Physical count discrepancy, damaged packaging)..."
                disabled={submitting}
              />
            </div>
          ) : (
            <>
              <Input
                label="Reason / Notes (Optional)"
                value={opReason}
                onChange={(e) => setOpReason(e.target.value)}
                placeholder="e.g. Returned goods, internal requisition"
                disabled={submitting}
              />
              <Input
                label="Document Reference (Optional)"
                value={opReference}
                onChange={(e) => setOpReference(e.target.value)}
                placeholder="e.g. DOC-9821, Delivery Slip #4"
                disabled={submitting}
              />
            </>
          )}

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setModalType(null)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant={modalType === 'OUT' ? 'danger' : 'primary'}
              loading={submitting}
            >
              Confirm {modalType}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
