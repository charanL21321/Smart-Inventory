import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { inventoryApi } from '../api/inventory';
import { replenishmentApi } from '../api/replenishment';
import { purchaseOrdersApi } from '../api/purchaseOrders';
import { Inventory, ReplenishmentRecommendation, PurchaseOrder } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import {
  Boxes,
  AlertTriangle,
  AlertOctagon,
  Sparkles,
  ClipboardList,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [inventoryList, setInventoryList] = useState<Inventory[]>([]);
  const [recommendations, setRecommendations] = useState<ReplenishmentRecommendation[]>([]);
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [invData, recData, poData] = await Promise.all([
        inventoryApi.getAll(),
        replenishmentApi.getAll({ status: 'PENDING' }),
        purchaseOrdersApi.getAll(),
      ]);
      setInventoryList(invData);
      setRecommendations(recData);
      setOrders(poData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return <Spinner size="lg" message="Loading operations dashboard..." className="py-20" />;
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={fetchDashboardData} className="my-8" />;
  }

  const lowStockCount = inventoryList.filter((i) => i.status === 'LOW_STOCK').length;
  const outOfStockCount = inventoryList.filter((i) => i.status === 'OUT_OF_STOCK').length;
  const criticalItems = inventoryList.filter(
    (i) => i.status === 'LOW_STOCK' || i.status === 'OUT_OF_STOCK'
  );
  const activeOrdersCount = orders.filter(
    (o) => !['RECEIVED', 'CANCELLED'].includes(o.status)
  ).length;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Inventory Operations Dashboard</h2>
          <p className="text-sm text-slate-500 mt-1">
            Real-time stock monitoring, replenishment recommendations, and order status.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/inventory"
            className="btn btn-secondary btn-sm"
          >
            Manage Inventory
          </Link>
          <Link
            to="/replenishment"
            className="btn btn-primary btn-sm"
          >
            Replenishment Engine
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Tracked Items
              </p>
              <h3 className="text-3xl font-bold text-slate-900 mt-2">{inventoryList.length}</h3>
            </div>
            <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600">
              <Boxes className="h-6 w-6" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">Active catalog stock items</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Low Stock Alert
              </p>
              <h3 className="text-3xl font-bold text-amber-600 mt-2">{lowStockCount}</h3>
            </div>
            <div className="rounded-xl bg-amber-50 p-3 text-amber-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">At or below reorder threshold</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Out of Stock
              </p>
              <h3 className="text-3xl font-bold text-rose-600 mt-2">{outOfStockCount}</h3>
            </div>
            <div className="rounded-xl bg-rose-50 p-3 text-rose-600">
              <AlertOctagon className="h-6 w-6" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">Zero inventory units available</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Pending Actions
              </p>
              <h3 className="text-3xl font-bold text-indigo-600 mt-2">
                {recommendations.length}
              </h3>
            </div>
            <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600">
              <Sparkles className="h-6 w-6" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">Replenishment suggestions pending review</p>
        </div>
      </div>

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Critical Stock Items */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-base font-bold text-slate-900">Critical Stock Attention</h4>
              <p className="text-xs text-slate-500">Items requiring immediate reorder review</p>
            </div>
            <Link
              to="/inventory"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1"
            >
              View All <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {criticalItems.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500">
              All stock balances are currently healthy.
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Current</th>
                    <th>Available</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {criticalItems.slice(0, 5).map((item) => (
                    <tr key={item.id}>
                      <td className="font-medium text-slate-900">
                        {item.product?.name || `Product #${item.product_id}`}
                        <div className="text-xs text-slate-400 font-normal">
                          {item.product?.sku}
                        </div>
                      </td>
                      <td>{item.current_stock}</td>
                      <td className="font-semibold">{item.available_stock}</td>
                      <td>
                        <StatusBadge status={item.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Priority Replenishment Recommendations */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-base font-bold text-slate-900">Top Replenishment Alerts</h4>
              <p className="text-xs text-slate-500">Rule-based recommendations engine</p>
            </div>
            <Link
              to="/replenishment"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1"
            >
              View All <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {recommendations.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500">
              No pending replenishment recommendations.
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Priority</th>
                    <th>Recommended Qty</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.slice(0, 5).map((rec) => (
                    <tr key={rec.id}>
                      <td className="font-medium text-slate-900">
                        {rec.product?.name || `Product #${rec.product_id}`}
                        <div className="text-xs text-slate-400 font-normal">
                          Stock: {rec.current_stock} / ROP: {rec.reorder_point}
                        </div>
                      </td>
                      <td>
                        <StatusBadge status={rec.priority} />
                      </td>
                      <td className="font-bold text-indigo-600">
                        +{rec.recommended_quantity}
                      </td>
                      <td>
                        <Link
                          to="/replenishment"
                          className="btn btn-secondary btn-sm"
                        >
                          Review
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
