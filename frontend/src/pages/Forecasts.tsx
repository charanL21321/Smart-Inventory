import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { forecastApi } from '../api/forecast';
import { productsApi } from '../api/products';
import { DemandForecast, Product, ForecastMethod, ForecastStatus } from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { Modal } from '../components/common/Modal';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { TrendingUp, Sparkles, RefreshCw, Eye } from 'lucide-react';

export const Forecasts: React.FC = () => {
  const { hasRole } = useAuth();
  const canGenerate = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [forecasts, setForecasts] = useState<DemandForecast[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [methodFilter, setMethodFilter] = useState<string>('');
  const [selectedProduct, setSelectedProduct] = useState<string>('');

  // Generation Modal State
  const [isGenModalOpen, setIsGenModalOpen] = useState(false);
  const [genMethod, setGenMethod] = useState<ForecastMethod>('SMA');
  const [genTarget, setGenTarget] = useState<'ALL' | 'SINGLE'>('ALL');
  const [singleProductId, setSingleProductId] = useState<number | ''>('');
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const loadForecasts = async () => {
    try {
      setLoading(true);
      setError(null);
      const [fData, pData] = await Promise.all([
        forecastApi.getAll({
          method: (methodFilter as ForecastMethod) || undefined,
          product_id: selectedProduct ? Number(selectedProduct) : undefined,
        }),
        productsApi.getAll({ is_active: true }),
      ]);
      setForecasts(fData);
      setProducts(pData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load demand forecasts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecasts();
  }, [methodFilter, selectedProduct]);

  const openGenerateModal = (productId?: number) => {
    if (productId) {
      setGenTarget('SINGLE');
      setSingleProductId(productId);
    } else {
      setGenTarget('ALL');
      setSingleProductId(products[0]?.id || '');
    }
    setGenMethod('SMA');
    setGenError(null);
    setIsGenModalOpen(true);
  };

  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setGenerating(true);
      setGenError(null);

      if (genTarget === 'ALL') {
        await forecastApi.generateAll(genMethod);
      } else {
        if (!singleProductId) {
          setGenError('Please select a product.');
          return;
        }
        await forecastApi.generateProduct(Number(singleProductId), genMethod);
      }

      setIsGenModalOpen(false);
      loadForecasts();
    } catch (err: any) {
      setGenError(err?.message || 'Forecast computation failed.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Demand Analysis & Forecasting</h2>
          <p className="text-sm text-slate-500">
            Time-series mathematical forecasting utilizing Simple Moving Average (SMA) and Weighted Moving Average (WMA).
          </p>
        </div>
        {canGenerate && (
          <Button onClick={() => openGenerateModal()} icon={<Sparkles className="h-4 w-4" />}>
            Generate Forecasts
          </Button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="card p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <Select
            options={[
              { value: 'SMA', label: 'Simple Moving Average (SMA)' },
              { value: 'WMA', label: 'Weighted Moving Average (WMA)' },
            ]}
            placeholder="All Forecasting Algorithms"
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
          />
        </div>
        <div>
          <Select
            options={products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
            placeholder="All Products"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
          />
        </div>
        <div className="flex items-center justify-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadForecasts}
            icon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh Forecasts
          </Button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadForecasts} />}

      {/* Table */}
      {loading ? (
        <Spinner size="lg" message="Loading forecasts..." className="py-12" />
      ) : forecasts.length === 0 ? (
        <EmptyState
          title="No demand forecasts found"
          description="Generate automated time-series projections for active products."
          icon={<TrendingUp className="h-10 w-10" />}
          actionLabel={canGenerate ? 'Run Forecasting Model' : undefined}
          onAction={() => openGenerateModal()}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Method</th>
                <th>Parameters</th>
                <th>Projected Total</th>
                <th>Daily Rate</th>
                <th>Run Date</th>
                <th>Status</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {forecasts.map((f) => (
                <tr key={f.id}>
                  <td className="font-semibold text-slate-900">
                    <Link to={`/forecasts/${f.id}`} className="hover:underline text-indigo-600">
                      {f.product_name || `Product #${f.product_id}`}
                    </Link>
                    <div className="text-xs text-slate-400 font-normal">
                      Model {f.model_version}
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={f.forecast_method} />
                  </td>
                  <td className="text-xs text-slate-600">
                    <div>History: {f.history_days}d</div>
                    <div>Horizon: {f.forecast_horizon_days}d</div>
                  </td>
                  <td className="font-bold text-slate-900">
                    {Math.round(f.total_forecast_quantity)} units
                  </td>
                  <td className="font-medium text-indigo-600">
                    {Number(f.average_daily_forecast).toFixed(2)}/day
                  </td>
                  <td className="text-xs text-slate-500 whitespace-nowrap">
                    {new Date(f.generated_at).toLocaleString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td>
                    <StatusBadge status={f.status} />
                  </td>
                  <td className="text-right">
                    <div className="inline-flex gap-2">
                      <Link
                        to={`/forecasts/${f.id}`}
                        className="btn btn-secondary btn-sm"
                        title="View Forecast Chart"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" /> Chart
                      </Link>
                      {canGenerate && (
                        <button
                          onClick={() => openGenerateModal(f.product_id)}
                          className="btn btn-secondary btn-sm"
                          title="Rerun Forecast"
                        >
                          <RefreshCw className="h-3.5 w-3.5" />
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

      {/* Generate Forecast Modal */}
      <Modal
        isOpen={isGenModalOpen}
        onClose={() => setIsGenModalOpen(false)}
        title="Generate Demand Forecast"
      >
        {genError && <ErrorAlert message={genError} className="mb-4" />}
        <form onSubmit={handleGenerateSubmit} className="space-y-4">
          <Select
            label="Target Scope"
            required
            options={[
              { value: 'ALL', label: 'All Active Products' },
              { value: 'SINGLE', label: 'Specific Product' },
            ]}
            value={genTarget}
            onChange={(e) => setGenTarget(e.target.value as 'ALL' | 'SINGLE')}
            disabled={generating}
          />

          {genTarget === 'SINGLE' && (
            <Select
              label="Select Product"
              required
              options={products.map((p) => ({
                value: p.id,
                label: `${p.name} (${p.sku})`,
              }))}
              value={singleProductId}
              onChange={(e) => setSingleProductId(Number(e.target.value))}
              disabled={generating}
            />
          )}

          <Select
            label="Forecasting Model / Algorithm"
            required
            options={[
              {
                value: 'SMA',
                label: 'Simple Moving Average (SMA) — Equal historical weighting',
              },
              {
                value: 'WMA',
                label: 'Weighted Moving Average (WMA) — Linear recency-weighted',
              },
            ]}
            value={genMethod}
            onChange={(e) => setGenMethod(e.target.value as ForecastMethod)}
            disabled={generating}
          />

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
            <strong>Model Parameters:</strong> 30-day historical demand lookback, 14-day future
            projection horizon. Any previous active forecast for the selected scope will be archived.
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsGenModalOpen(false)}
              disabled={generating}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={generating}>
              Run Forecast
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
