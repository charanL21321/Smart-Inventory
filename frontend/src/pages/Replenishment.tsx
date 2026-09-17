import React, { useEffect, useState } from 'react';
import { replenishmentApi } from '../api/replenishment';
import {
  ReplenishmentRecommendation,
  RecommendationPriority,
  RecommendationStatus,
} from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { Modal } from '../components/common/Modal';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Sparkles, Check, X, RefreshCw, Info } from 'lucide-react';

export const Replenishment: React.FC = () => {
  const { hasRole } = useAuth();
  const canManage = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [recommendations, setRecommendations] = useState<ReplenishmentRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [priorityFilter, setPriorityFilter] = useState<string>('');

  // Dismiss Modal State
  const [dismissTargetId, setDismissTargetId] = useState<number | null>(null);
  const [dismissReason, setDismissReason] = useState('');
  const [dismissSubmitting, setDismissSubmitting] = useState(false);
  const [dismissError, setDismissError] = useState<string | null>(null);

  // Review Submitting state map
  const [reviewingId, setReviewingId] = useState<number | null>(null);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await replenishmentApi.getAll({
        status: (statusFilter as RecommendationStatus) || undefined,
        priority: (priorityFilter as RecommendationPriority) || undefined,
      });
      setRecommendations(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load replenishment recommendations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecommendations();
  }, [statusFilter, priorityFilter]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      await replenishmentApi.generate();
      loadRecommendations();
    } catch (err: any) {
      setError(err?.message || 'Replenishment calculation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleReview = async (id: number) => {
    try {
      setReviewingId(id);
      await replenishmentApi.review(id);
      loadRecommendations();
    } catch (err: any) {
      setError(err?.message || 'Failed to review recommendation.');
    } finally {
      setReviewingId(null);
    }
  };

  const openDismissModal = (id: number) => {
    setDismissTargetId(id);
    setDismissReason('');
    setDismissError(null);
  };

  const handleDismissSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dismissTargetId) return;
    if (!dismissReason.trim()) {
      setDismissError('A detailed reason for dismissal is strictly required.');
      return;
    }

    try {
      setDismissSubmitting(true);
      setDismissError(null);
      await replenishmentApi.dismiss(dismissTargetId, { reason: dismissReason });
      setDismissTargetId(null);
      loadRecommendations();
    } catch (err: any) {
      setDismissError(err?.message || 'Failed to dismiss recommendation.');
    } finally {
      setDismissSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Smart Replenishment Engine</h2>
          <p className="text-sm text-slate-500">
            Rule-based reorder analysis evaluating inventory position, sales velocity, lead-time demand, and MOQs.
          </p>
        </div>
        {canManage && (
          <Button
            onClick={handleGenerate}
            loading={generating}
            icon={<Sparkles className="h-4 w-4" />}
          >
            Run Replenishment Engine
          </Button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="card p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <Select
            options={[
              { value: 'PENDING', label: 'Pending Review' },
              { value: 'REVIEWED', label: 'Reviewed' },
              { value: 'DISMISSED', label: 'Dismissed' },
            ]}
            placeholder="All Statuses"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          />
        </div>
        <div>
          <Select
            options={[
              { value: 'HIGH', label: 'High Priority' },
              { value: 'MEDIUM', label: 'Medium Priority' },
              { value: 'LOW', label: 'Low Priority' },
            ]}
            placeholder="All Priorities"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          />
        </div>
        <div className="flex items-center justify-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadRecommendations}
            icon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh List
          </Button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadRecommendations} />}

      {/* Table */}
      {loading ? (
        <Spinner size="lg" message="Loading replenishment recommendations..." className="py-12" />
      ) : recommendations.length === 0 ? (
        <EmptyState
          title="No recommendations found"
          description="All stock inventory levels are adequate, or recommendations match no current filter."
          icon={<Sparkles className="h-10 w-10" />}
          actionLabel={canManage ? 'Run Engine Now' : undefined}
          onAction={handleGenerate}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Priority</th>
                <th>Current / IP</th>
                <th>ROP / Target</th>
                <th>Velocity / LT</th>
                <th>Recommended Qty</th>
                <th>Reasoning Explanation</th>
                <th>Status</th>
                {canManage && <th className="text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {recommendations.map((rec) => (
                <tr key={rec.id}>
                  <td className="font-semibold text-slate-900">
                    {rec.product?.name || `Product #${rec.product_id}`}
                    <div className="text-xs text-slate-400 font-normal">
                      {rec.product?.sku} • {rec.supplier?.name}
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={rec.priority} />
                  </td>
                  <td className="text-xs">
                    <div>
                      Current: <span className="font-semibold">{rec.current_stock}</span>
                    </div>
                    <div className="text-slate-500">IP: {rec.inventory_position}</div>
                  </td>
                  <td className="text-xs">
                    <div>
                      ROP: <span className="font-semibold text-slate-700">{rec.reorder_point}</span>
                    </div>
                    <div className="text-slate-500">Target: {rec.target_stock}</div>
                  </td>
                  <td className="text-xs">
                    <div>{rec.average_daily_demand.toFixed(2)}/day</div>
                    <div className="text-slate-500">{rec.lead_time_days} days lead</div>
                  </td>
                  <td className="font-bold text-base text-indigo-600">
                    +{rec.recommended_quantity}
                    <div className="text-[10px] text-slate-400 font-normal">
                      MOQ: {rec.minimum_order_quantity}
                    </div>
                  </td>
                  <td className="text-xs text-slate-600 max-w-xs">
                    <p className="line-clamp-2">{rec.reason}</p>
                    {rec.dismissal_reason && (
                      <p className="text-rose-600 mt-1 italic">
                        Dismissed: "{rec.dismissal_reason}"
                      </p>
                    )}
                  </td>
                  <td>
                    <StatusBadge status={rec.status} />
                  </td>
                  {canManage && (
                    <td className="text-right whitespace-nowrap">
                      {rec.status === 'PENDING' ? (
                        <div className="inline-flex gap-1.5">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleReview(rec.id)}
                            loading={reviewingId === rec.id}
                            icon={<Check className="h-3.5 w-3.5 text-emerald-600" />}
                          >
                            Review
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => openDismissModal(rec.id)}
                            icon={<X className="h-3.5 w-3.5 text-rose-600" />}
                          >
                            Dismiss
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">Processed</span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Dismiss Modal */}
      <Modal
        isOpen={dismissTargetId !== null}
        onClose={() => setDismissTargetId(null)}
        title="Dismiss Replenishment Recommendation"
      >
        {dismissError && <ErrorAlert message={dismissError} className="mb-4" />}
        <form onSubmit={handleDismissSubmit} className="space-y-4">
          <p className="text-xs text-slate-600">
            Please document a business reason for dismissing this automated suggestion (e.g.
            upcoming supplier discontinuation, budget pause, duplicate offline order).
          </p>

          <div>
            <label className="label">
              Mandatory Dismissal Reason <span className="text-rose-600">*</span>
            </label>
            <textarea
              className="textarea"
              rows={3}
              required
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
              placeholder="State why this reorder recommendation is being dismissed..."
              disabled={dismissSubmitting}
            />
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setDismissTargetId(null)}
              disabled={dismissSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" variant="danger" loading={dismissSubmitting}>
              Confirm Dismissal
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
