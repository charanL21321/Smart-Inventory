import React, { useState } from 'react';
import { DemandForecastValue } from '../../types';

interface ForecastChartProps {
  values: DemandForecastValue[];
  title?: string;
  height?: number;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  values,
  title = 'Demand Projection',
  height = 260,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<{
    date: string;
    value: number;
    x: number;
    y: number;
  } | null>(null);

  if (!values || values.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-400">
        No forecast data points available for projection chart.
      </div>
    );
  }

  const sortedValues = [...values].sort(
    (a, b) => new Date(a.forecast_date).getTime() - new Date(b.forecast_date).getTime()
  );

  const paddingLeft = 45;
  const paddingRight = 25;
  const paddingTop = 25;
  const paddingBottom = 40;
  const width = 650;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const rawMax = Math.max(...sortedValues.map((v) => v.forecast_quantity), 10);
  const maxVal = Math.ceil(rawMax * 1.15); // Add headroom
  const minVal = 0;

  const getX = (index: number) => {
    if (sortedValues.length <= 1) return paddingLeft + chartWidth / 2;
    return paddingLeft + (index / (sortedValues.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    return paddingTop + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;
  };

  // Generate line points and area path
  const points = sortedValues.map((v, i) => `${getX(i)},${getY(v.forecast_quantity)}`).join(' ');

  const areaPath = `
    M ${getX(0)},${getY(minVal)}
    L ${sortedValues.map((v, i) => `${getX(i)},${getY(v.forecast_quantity)}`).join(' L ')}
    L ${getX(sortedValues.length - 1)},${getY(minVal)}
    Z
  `;

  // Grid lines
  const gridSteps = 4;
  const gridLines = Array.from({ length: gridSteps + 1 }, (_, i) => {
    const val = Math.round((maxVal / gridSteps) * i);
    const y = getY(val);
    return { val, y };
  });

  return (
    <div className="w-full">
      {title && (
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
          <span className="text-xs text-slate-500">{sortedValues.length} Days Horizon</span>
        </div>
      )}
      <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible"
          style={{ minHeight: `${height}px` }}
        >
          <defs>
            <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines & Y-axis labels */}
          {gridLines.map((line, idx) => (
            <g key={idx}>
              <line
                x1={paddingLeft}
                y1={line.y}
                x2={width - paddingRight}
                y2={line.y}
                stroke="#e2e8f0"
                strokeDasharray={idx === 0 ? undefined : '4 4'}
                strokeWidth="1"
              />
              <text
                x={paddingLeft - 8}
                y={line.y + 3}
                fill="#94a3b8"
                fontSize="10"
                textAnchor="end"
              >
                {line.val}
              </text>
            </g>
          ))}

          {/* Area fill under line */}
          <path d={areaPath} fill="url(#forecastGradient)" />

          {/* Line stroke */}
          <polyline
            fill="none"
            stroke="#4f46e5"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />

          {/* Data Points */}
          {sortedValues.map((v, i) => {
            const cx = getX(i);
            const cy = getY(v.forecast_quantity);
            const isHovered = hoveredPoint?.date === v.forecast_date;

            return (
              <g key={v.id || i}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 5.5 : 3.5}
                  fill={isHovered ? '#312e81' : '#4f46e5'}
                  stroke="#ffffff"
                  strokeWidth="2"
                  className="transition-all cursor-pointer"
                  onMouseEnter={() =>
                    setHoveredPoint({
                      date: v.forecast_date,
                      value: v.forecast_quantity,
                      x: cx,
                      y: cy,
                    })
                  }
                  onMouseLeave={() => setHoveredPoint(null)}
                />
                {/* Date Label on X axis (skip to avoid overcrowding if many points) */}
                {(sortedValues.length <= 14 || i % Math.ceil(sortedValues.length / 10) === 0) && (
                  <text
                    x={cx}
                    y={height - paddingBottom + 16}
                    fill="#64748b"
                    fontSize="9"
                    textAnchor="middle"
                  >
                    {new Date(v.forecast_date).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute pointer-events-none rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs text-white shadow-lg -translate-x-1/2 -translate-y-full"
            style={{
              left: `${(hoveredPoint.x / width) * 100}%`,
              top: `${(hoveredPoint.y / height) * 100}%`,
              marginTop: '-8px',
            }}
          >
            <div className="font-semibold text-indigo-300">
              {new Date(hoveredPoint.date).toLocaleDateString(undefined, {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
              })}
            </div>
            <div>
              Forecast: <span className="font-bold">{hoveredPoint.value}</span> units
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
