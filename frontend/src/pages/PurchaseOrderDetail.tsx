import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { purchaseOrdersApi } from '../api/purchaseOrders';
import { PurchaseOrder, PurchaseOrderStatus, PurchaseOrderReceiveItem } from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Modal } from '../components/common/Modal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import {
  ArrowLeft,
  CheckCircle,
  Truck,
  Send,
  XCircle,
  PackageCheck,
  Calendar,
  Building,
  DollarSign,
} from 'lucide-react';

export const PurchaseOrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();

  const canManageStatus = hasRole('ADMIN', 'INVENTORY_MANAGER');
  const canReceive = hasRole('ADMIN', 'INVENTORY_MANAGER', 'WAREHOUSE_STAFF');

  const [order, setOrder] = useState<PurchaseOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status Action State
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmStatusModal, setConfirmStatusModal] = useState<PurchaseOrderStatus | null>(null);

  // Receive Modal State
  const [isReceiveModalOpen, setIsReceiveModalOpen] = useState(false);
  const [receiveInputs, setReceiveInputs] = useState<Record<number, number>>({});
  const [receiveSubmitting, setReceiveSubmitting] = useState(false);
  const [receiveError, setReceiveError] = useState<string | null>(null);

  const loadOrderDetail = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await purchaseOrdersApi.getById(Number(id));
      setOrder(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load purchase order details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrderDetail();
  }, [id]);

  const handleStatusTransition = async (newStatus: PurchaseOrderStatus) => {
    if (!order) return;
    try {
      setActionLoading(true);
      await purchaseOrdersApi.updateStatus(order.id, { status: newStatus });
      setConfirmStatusModal(null);
      loadOrderDetail();
    } catch (err: any) {
      setError(err?.message || `Failed to transition status to ${newStatus}.`);
    } finally {
      setActionLoading(false);
    }
  };

  const openReceiveModal = () => {
    if (!order) return;
    const initialInputs: Record<number, number> = {};
    order.items.forEach((item) => {
      const remaining = Math.max(0, item.quantity - item.received_quantity);
      initialInputs[item.product_id] = remaining;
    });
    setReceiveInputs(initialInputs);
    setReceiveError(null);
    setIsReceiveModalOpen(true);
  };

  const handleReceiveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!order) return;

    const itemsToReceive: PurchaseOrderReceiveItem[] = [];
    for (const [prodIdStr, qty] of Object.entries(receiveInputs)) {
      const numQty = Number(qty);
      if (numQty > 0) {
        itemsToReceive.push({
          product_id: Number(prodIdStr),
          received_quantity: numQty,
        });
      }
    }

    if (itemsToReceive.length === 0) {
      setReceiveError('Please specify at least 1 unit to receive.');
      return;
    }

    try {
      setReceiveSubmitting(true);
      setReceiveError(null);
      await purchaseOrdersApi.receive(order.id, { items: itemsToReceive });
      setIsReceiveModalOpen(false);
      loadOrderDetail();
    } catch (err: any) {
      setReceiveError(err?.message || 'Failed to receive purchase order items.');
    } finally {
      setReceiveSubmitting(false);
    }
  };

  if (loading) {
    return <Spinner size="lg" message="Loading purchase order..." className="py-20" />;
  }

  if (error || !order) {
    return (
      <div className="space-y-4">
        <Link to="/purchase-orders" className="btn btn-secondary btn-sm inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" /> Back to Orders
        </Link>
        <ErrorAlert
          message={error || 'Purchase order not found.'}
          onRetry={loadOrderDetail}
        />
      </div>
    );
  }

  const isReceivable =
    (order.status === 'ORDERED' || order.status === 'PARTIALLY_RECEIVED') && canReceive;

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/purchase-orders"
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-900">{order.order_number}</h2>
              <StatusBadge status={order.status} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Created on {new Date(order.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Workflow Actions */}
        <div className="flex gap-2 flex-wrap">
          {canManageStatus && order.status === 'DRAFT' && (
            <>
              <Button
                variant="primary"
                onClick={() => setConfirmStatusModal('PENDING_APPROVAL')}
                icon={<Send className="h-4 w-4" />}
              >
                Submit for Approval
              </Button>
              <Button
                variant="danger"
                onClick={() => setConfirmStatusModal('CANCELLED')}
                icon={<XCircle className="h-4 w-4" />}
              >
                Cancel Order
              </Button>
            </>
          )}

          {canManageStatus && order.status === 'PENDING_APPROVAL' && (
            <>
              <Button
                variant="primary"
                onClick={() => setConfirmStatusModal('APPROVED')}
                icon={<CheckCircle className="h-4 w-4" />}
              >
                Approve Order
              </Button>
              <Button
                variant="danger"
                onClick={() => setConfirmStatusModal('CANCELLED')}
                icon={<XCircle className="h-4 w-4" />}
              >
                Cancel Order
              </Button>
            </>
          )}

          {canManageStatus && order.status === 'APPROVED' && (
            <>
              <Button
                variant="primary"
                onClick={() => setConfirmStatusModal('ORDERED')}
                icon={<Truck className="h-4 w-4" />}
              >
                Place Order with Supplier
              </Button>
              <Button
                variant="danger"
                onClick={() => setConfirmStatusModal('CANCELLED')}
                icon={<XCircle className="h-4 w-4" />}
              >
                Cancel Order
              </Button>
            </>
          )}

          {isReceivable && (
            <Button
              variant="primary"
              onClick={openReceiveModal}
              icon={<PackageCheck className="h-4 w-4" />}
            >
              Receive Goods
            </Button>
          )}
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-2">
            <Building className="h-4 w-4 text-indigo-600" /> Supplier Information
          </div>
          <h4 className="text-base font-bold text-slate-900">{order.supplier?.name}</h4>
          <p className="text-xs text-slate-600 mt-1">
            Contact: {order.supplier?.contact_person || 'N/A'}
          </p>
          <p className="text-xs text-slate-600">Email: {order.supplier?.email}</p>
          <p className="text-xs text-slate-600">Phone: {order.supplier?.phone}</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-2">
            <Calendar className="h-4 w-4 text-indigo-600" /> Schedule & Delivery
          </div>
          <div className="space-y-1 text-xs">
            <p className="text-slate-600">
              <span className="font-semibold text-slate-700">Expected Delivery:</span>{' '}
              {order.expected_delivery_date
                ? new Date(order.expected_delivery_date).toLocaleDateString()
                : 'Not specified'}
            </p>
            <p className="text-slate-600">
              <span className="font-semibold text-slate-700">Ordered Date:</span>{' '}
              {order.ordered_at ? new Date(order.ordered_at).toLocaleDateString() : 'Pending order'}
            </p>
            <p className="text-slate-600">
              <span className="font-semibold text-slate-700">Final Received Date:</span>{' '}
              {order.received_at
                ? new Date(order.received_at).toLocaleDateString()
                : 'Pending receipt'}
            </p>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-2">
            <DollarSign className="h-4 w-4 text-indigo-600" /> Procurement Value
          </div>
          <div className="text-2xl font-bold text-slate-900">
            ${Number(order.total_amount).toFixed(2)}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Created by user #{order.created_by}
            {order.approved_by && ` • Approved by user #${order.approved_by}`}
          </p>
          {order.notes && (
            <p className="text-xs text-slate-600 mt-2 bg-slate-50 p-2 rounded border">
              "{order.notes}"
            </p>
          )}
        </div>
      </div>

      {/* Line Items Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <h3 className="text-base font-bold text-slate-900">Order Line Items</h3>
        </div>
        <div className="table-container border-0 rounded-none">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Ordered Qty</th>
                <th>Received Qty</th>
                <th>Fulfillment Progress</th>
                <th>Unit Cost</th>
                <th className="text-right">Total Line Cost</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => {
                const percent = Math.min(
                  100,
                  Math.round((item.received_quantity / item.quantity) * 100)
                );
                return (
                  <tr key={item.id}>
                    <td className="font-semibold text-slate-900">
                      {item.product?.name || `Product #${item.product_id}`}
                      <div className="text-xs text-slate-400 font-normal">
                        {item.product?.sku}
                      </div>
                    </td>
                    <td className="font-medium text-slate-800">{item.quantity}</td>
                    <td className="font-bold text-indigo-600">{item.received_quantity}</td>
                    <td className="w-48">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              percent === 100 ? 'bg-emerald-500' : 'bg-indigo-600'
                            }`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-slate-600 w-10 text-right">
                          {percent}%
                        </span>
                      </div>
                    </td>
                    <td>${Number(item.unit_cost).toFixed(2)}</td>
                    <td className="text-right font-bold text-slate-900">
                      ${Number(item.total_cost).toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Transition Confirmation Modal */}
      <ConfirmDialog
        isOpen={confirmStatusModal !== null}
        onClose={() => setConfirmStatusModal(null)}
        onConfirm={() => confirmStatusModal && handleStatusTransition(confirmStatusModal)}
        title={`Advance Order to ${confirmStatusModal}?`}
        message={`Are you sure you want to transition ${order.order_number} to status "${confirmStatusModal}"? This step cannot be reversed.`}
        confirmLabel="Confirm Transition"
        variant={confirmStatusModal === 'CANCELLED' ? 'danger' : 'primary'}
        loading={actionLoading}
      />

      {/* Receive Modal */}
      <Modal
        isOpen={isReceiveModalOpen}
        onClose={() => setIsReceiveModalOpen(false)}
        title={`Receive Goods — ${order.order_number}`}
        maxWidth="lg"
      >
        {receiveError && <ErrorAlert message={receiveError} className="mb-4" />}
        <form onSubmit={handleReceiveSubmit} className="space-y-4">
          <p className="text-xs text-slate-600 mb-2">
            Enter the physical quantity received at warehouse for each product line. Stock
            balances will be atomically incremented.
          </p>

          <div className="space-y-3">
            {order.items.map((item) => {
              const remaining = Math.max(0, item.quantity - item.received_quantity);
              return (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200"
                >
                  <div className="flex-1 pr-4">
                    <div className="font-semibold text-sm text-slate-900">
                      {item.product?.name || `Product #${item.product_id}`}
                    </div>
                    <div className="text-xs text-slate-500">
                      Ordered: {item.quantity} | Already Received: {item.received_quantity} | Remaining: {remaining}
                    </div>
                  </div>
                  <div className="w-32">
                    <Input
                      type="number"
                      min="0"
                      max={remaining}
                      value={receiveInputs[item.product_id] ?? 0}
                      onChange={(e) =>
                        setReceiveInputs({
                          ...receiveInputs,
                          [item.product_id]: Number(e.target.value),
                        })
                      }
                      disabled={receiveSubmitting || remaining === 0}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsReceiveModalOpen(false)}
              disabled={receiveSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={receiveSubmitting}>
              Accept Stock Receipt
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
