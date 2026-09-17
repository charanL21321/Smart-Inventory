import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { forecastApi } from '../api/forecast';
import { DemandForecast } from '../types';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/common/StatusBadge';
import { ForecastChart } from '../components/common/ForecastChart';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import {
  ArrowLeft,
  Calendar,
  Layers,
  Calculator,
  Info,
  Clock,
} from 'lucide-react';

export const ForecastDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [forecast, setForecast] = useState<DemandForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await forecastApi.getById(Number(id));
      setForecast(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load forecast detail.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [id]);

  if (loading) {
    return <Spinner size="lg" message="Loading forecast data & chart..." className="py-20" />;
  }

  if (error || !forecast) {
    return (
      <div className="space-y-4">
        <Link to="/forecasts" className="btn btn-secondary btn-sm inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" /> Back to Forecasts
        </Link>
        <ErrorAlert message={error || 'Forecast record not found.'} onRetry={loadForecast} />
      </div>
    );
  }

  const values = forecast.values || [];

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/forecasts"
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-900">
                {forecast.product_name || `Product #${forecast.product_id}`}
              </h2>
              <StatusBadge status={forecast.forecast_method} />
              <StatusBadge status={forecast.status} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Generated on {new Date(forecast.generated_at).toLocaleString()} • Engine v{forecast.model_version}
            </p>
          </div>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-1">
            <Calculator className="h-4 w-4 text-indigo-600" /> Projected Total
          </div>
          <div className="text-3xl font-bold text-indigo-600 mt-1">
            {Math.round(forecast.total_forecast_quantity)}
          </div>
          <p className="text-xs text-slate-400 mt-1">Across {forecast.forecast_horizon_days} day horizon</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-1">
            <Layers className="h-4 w-4 text-indigo-600" /> Daily Demand Rate
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">
            {Number(forecast.average_daily_forecast).toFixed(2)}
          </div>
          <p className="text-xs text-slate-400 mt-1">Units per day average</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-1">
            <Clock className="h-4 w-4 text-indigo-600" /> Historical Lookback
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">
            {forecast.history_days} Days
          </div>
          <p className="text-xs text-slate-400 mt-1">Aggregated sales observations</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 text-slate-500 text-xs font-semibold uppercase mb-1">
            <Calendar className="h-4 w-4 text-indigo-600" /> Projection Horizon
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">
            {forecast.forecast_horizon_days} Days
          </div>
          <p className="text-xs text-slate-400 mt-1">Daily forward projection</p>
        </div>
      </div>

      {/* Interactive SVG Line Chart */}
      <div className="card">
        <ForecastChart
          values={values}
          title={`Forecast Projection Trend (${forecast.forecast_method})`}
          height={300}
        />
      </div>

      {/* Two Column Details: Math Explanation & Values Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model Explanation */}
        <div className="card lg:col-span-1">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-indigo-600" />
            <h4 className="text-sm font-bold text-slate-900">Forecasting Methodology</h4>
          </div>
          <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
            <p>
              <strong>Method:</strong> {forecast.forecast_method === 'SMA' ? 'Simple Moving Average' : 'Weighted Moving Average'}
            </p>
            {forecast.forecast_method === 'SMA' ? (
              <p>
                Calculates daily demand by averaging all sales volume over the preceding {forecast.history_days} days equally.
                Ideal for stable products with steady consumer velocity.
              </p>
            ) : (
              <p>
                Applies linearly increasing weights to historical sales over the preceding {forecast.history_days} days,
                giving higher significance to recent trends.
              </p>
            )}
            {forecast.explanation && (
              <div className="bg-slate-50 p-3 rounded-lg border text-slate-700 font-mono text-[11px]">
                {forecast.explanation}
              </div>
            )}
          </div>
        </div>

        {/* Daily Values Table */}
        <div className="card p-0 overflow-hidden lg:col-span-2">
          <div className="p-4 border-b border-slate-200 flex justify-between items-center">
            <h4 className="text-sm font-bold text-slate-900">Day-by-Day Forecast Breakdown</h4>
            <span className="text-xs text-slate-500">{values.length} Daily Projections</span>
          </div>
          <div className="table-container border-0 rounded-none max-h-80 overflow-y-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Forecast Date</th>
                  <th>Day of Week</th>
                  <th className="text-right">Projected Quantity</th>
                </tr>
              </thead>
              <tbody>
                {values.map((val) => {
                  const d = new Date(val.forecast_date);
                  return (
                    <tr key={val.id}>
                      <td className="font-medium text-slate-900">
                        {d.toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td className="text-xs text-slate-500">
                        {d.toLocaleDateString(undefined, { weekday: 'long' })}
                      </td>
                      <td className="text-right font-bold text-indigo-600">
                        {val.forecast_quantity} units
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
