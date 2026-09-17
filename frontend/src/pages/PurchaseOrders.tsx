import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { purchaseOrdersApi } from '../api/purchaseOrders';
import { suppliersApi } from '../api/suppliers';
import { productsApi } from '../api/products';
import {
  PurchaseOrder,
  Supplier,
  Product,
  PurchaseOrderStatus,
  PurchaseOrderCreate,
  PurchaseOrderItemCreate,
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
import { ClipboardList, Plus, Search, Trash2, Eye } from 'lucide-react';

export const PurchaseOrders: React.FC = () => {
  const { hasRole } = useAuth();
  const canCreate = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedSupplier, setSelectedSupplier] = useState<string>('');

  // Create PO Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [formSupplierId, setFormSupplierId] = useState<number | ''>('');
  const [formExpectedDate, setFormExpectedDate] = useState('');
  const [formNotes, setFormNotes] = useState('');
  const [formItems, setFormItems] = useState<PurchaseOrderItemCreate[]>([
    { product_id: 0, quantity: 10, unit_cost: 10.0 },
  ]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ordersData, sData, pData] = await Promise.all([
        purchaseOrdersApi.getAll({
          status: (selectedStatus as PurchaseOrderStatus) || undefined,
          supplier_id: selectedSupplier ? Number(selectedSupplier) : undefined,
        }),
        suppliersApi.getAll(true),
        productsApi.getAll({ is_active: true }),
      ]);
      setOrders(ordersData);
      setSuppliers(sData);
      setProducts(pData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load purchase orders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [selectedStatus, selectedSupplier]);

  const openCreateModal = () => {
    setFormSupplierId(suppliers[0]?.id || '');
    setFormExpectedDate('');
    setFormNotes('');
    setFormItems([
      {
        product_id: products[0]?.id || 0,
        quantity: 10,
        unit_cost: products[0]?.price || 10,
      },
    ]);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleAddItemRow = () => {
    setFormItems([
      ...formItems,
      {
        product_id: products[0]?.id || 0,
        quantity: 10,
        unit_cost: products[0]?.price || 10,
      },
    ]);
  };

  const handleRemoveItemRow = (index: number) => {
    if (formItems.length === 1) return;
    setFormItems(formItems.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: keyof PurchaseOrderItemCreate, val: any) => {
    const updated = [...formItems];
    updated[index] = { ...updated[index], [field]: val };
    if (field === 'product_id') {
      const p = products.find((prod) => prod.id === val);
      if (p) {
        updated[index].unit_cost = p.price;
      }
    }
    setFormItems(updated);
  };

  const calculateTotal = () => {
    return formItems.reduce((acc, item) => acc + item.quantity * item.unit_cost, 0);
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formSupplierId) {
      setFormError('Please select a supplier.');
      return;
    }
    if (formItems.length === 0 || formItems.some((i) => !i.product_id || i.quantity <= 0 || i.unit_cost < 0)) {
      setFormError('Please provide valid product items, positive quantities, and unit costs.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      const payload: PurchaseOrderCreate = {
        supplier_id: Number(formSupplierId),
        notes: formNotes || undefined,
        expected_delivery_date: formExpectedDate || undefined,
        items: formItems.map((i) => ({
          product_id: Number(i.product_id),
          quantity: Number(i.quantity),
          unit_cost: Number(i.unit_cost),
        })),
      };
      await purchaseOrdersApi.create(payload);
      setIsModalOpen(false);
      loadOrders();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create purchase order.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Purchase Orders</h2>
          <p className="text-sm text-slate-500">
            Procurement workflow from Draft creation to approval, supplier ordering, and goods receipt.
          </p>
        </div>
        {canCreate && (
          <Button onClick={openCreateModal} icon={<Plus className="h-4 w-4" />}>
            New Purchase Order
          </Button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="card p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Select
            options={[
              { value: 'DRAFT', label: 'Draft' },
              { value: 'PENDING_APPROVAL', label: 'Pending Approval' },
              { value: 'APPROVED', label: 'Approved' },
              { value: 'ORDERED', label: 'Ordered' },
              { value: 'PARTIALLY_RECEIVED', label: 'Partially Received' },
              { value: 'RECEIVED', label: 'Received' },
              { value: 'CANCELLED', label: 'Cancelled' },
            ]}
            placeholder="All Statuses"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          />
        </div>
        <div>
          <Select
            options={suppliers.map((s) => ({ value: s.id, label: s.name }))}
            placeholder="All Suppliers"
            value={selectedSupplier}
            onChange={(e) => setSelectedSupplier(e.target.value)}
          />
        </div>
        <div className="flex items-center text-xs text-slate-500">
          Showing {orders.length} orders
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadOrders} />}

      {loading ? (
        <Spinner size="lg" message="Loading purchase orders..." className="py-12" />
      ) : orders.length === 0 ? (
        <EmptyState
          title="No purchase orders found"
          description="No purchase orders match your filter criteria."
          icon={<ClipboardList className="h-10 w-10" />}
          actionLabel={canCreate ? 'Create Purchase Order' : undefined}
          onAction={openCreateModal}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Order Number</th>
                <th>Supplier</th>
                <th>Status</th>
                <th>Items Count</th>
                <th>Total Value</th>
                <th>Expected Delivery</th>
                <th>Created Date</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id}>
                  <td className="font-mono font-bold text-indigo-600">
                    <Link to={`/purchase-orders/${order.id}`} className="hover:underline">
                      {order.order_number}
                    </Link>
                  </td>
                  <td className="font-medium text-slate-900">
                    {order.supplier?.name || `Supplier #${order.supplier_id}`}
                  </td>
                  <td>
                    <StatusBadge status={order.status} />
                  </td>
                  <td>{order.items?.length || 0} line items</td>
                  <td className="font-bold text-slate-900">
                    ${Number(order.total_amount).toFixed(2)}
                  </td>
                  <td className="text-xs text-slate-500">
                    {order.expected_delivery_date
                      ? new Date(order.expected_delivery_date).toLocaleDateString()
                      : '—'}
                  </td>
                  <td className="text-xs text-slate-500">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                  <td className="text-right">
                    <Link
                      to={`/purchase-orders/${order.id}`}
                      className="btn btn-secondary btn-sm"
                    >
                      <Eye className="h-3.5 w-3.5 mr-1" /> View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Purchase Order Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Purchase Order (Draft)"
        maxWidth="xl"
      >
        {formError && <ErrorAlert message={formError} className="mb-4" />}
        <form onSubmit={handleCreateOrder} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Supplier"
              required
              options={suppliers.map((s) => ({ value: s.id, label: s.name }))}
              value={formSupplierId}
              onChange={(e) => setFormSupplierId(Number(e.target.value))}
              disabled={submitting}
            />
            <Input
              label="Expected Delivery Date"
              type="date"
              value={formExpectedDate}
              onChange={(e) => setFormExpectedDate(e.target.value)}
              disabled={submitting}
            />
          </div>

          <div>
            <label className="label">Notes / Instructions</label>
            <textarea
              className="textarea"
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Terms, freight instructions, delivery contact..."
              disabled={submitting}
            />
          </div>

          {/* Line Items Section */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-slate-800">Order Line Items</h4>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={handleAddItemRow}
                icon={<Plus className="h-3.5 w-3.5" />}
              >
                Add Item
              </Button>
            </div>

            <div className="space-y-3">
              {formItems.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200"
                >
                  <div className="flex-1">
                    <Select
                      options={products.map((p) => ({
                        value: p.id,
                        label: `${p.name} (${p.sku})`,
                      }))}
                      value={item.product_id}
                      onChange={(e) =>
                        handleItemChange(idx, 'product_id', Number(e.target.value))
                      }
                      disabled={submitting}
                    />
                  </div>
                  <div className="w-24">
                    <Input
                      type="number"
                      min="1"
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={(e) =>
                        handleItemChange(idx, 'quantity', Number(e.target.value))
                      }
                      disabled={submitting}
                    />
                  </div>
                  <div className="w-28">
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Unit Cost"
                      value={item.unit_cost}
                      onChange={(e) =>
                        handleItemChange(idx, 'unit_cost', Number(e.target.value))
                      }
                      disabled={submitting}
                    />
                  </div>
                  <div className="w-24 text-right font-semibold text-xs text-slate-800">
                    ${(item.quantity * item.unit_cost).toFixed(2)}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveItemRow(idx)}
                    disabled={formItems.length === 1 || submitting}
                    className="p-1.5 text-slate-400 hover:text-rose-600 disabled:opacity-30 rounded transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            <div className="mt-4 p-3 bg-indigo-50 rounded-lg flex items-center justify-between text-sm font-semibold text-indigo-950 border border-indigo-100">
              <span>Estimated Order Total:</span>
              <span className="text-base font-bold text-indigo-700">
                ${calculateTotal().toFixed(2)}
              </span>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={submitting}>
              Create Draft PO
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
