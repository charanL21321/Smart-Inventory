import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { notificationApi } from '../api/notifications';
import {
  Notification,
  NotificationPriority,
  NotificationType,
} from '../types';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { StatusBadge } from '../components/common/StatusBadge';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import {
  Bell,
  CheckCheck,
  Check,
  RefreshCw,
  AlertTriangle,
  AlertCircle,
  TrendingUp,
  ClipboardList,
  Sparkles,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';

export const Notifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [markingAll, setMarkingAll] = useState<boolean>(false);
  const [markingId, setMarkingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [readFilter, setReadFilter] = useState<string>(''); // '' = all, 'unread', 'read'
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);

      const isReadParam =
        readFilter === 'unread' ? false : readFilter === 'read' ? true : undefined;

      const [listData, countData] = await Promise.all([
        notificationApi.getAll({
          is_read: isReadParam,
          notification_type: (typeFilter as NotificationType) || undefined,
          priority: (priorityFilter as NotificationPriority) || undefined,
          limit: 100,
        }),
        notificationApi.getUnreadCount(),
      ]);

      setNotifications(listData);
      setUnreadCount(countData.unread_count);
    } catch (err: any) {
      setError(err?.message || 'Failed to load notifications.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [readFilter, typeFilter, priorityFilter]);

  const handleMarkAsRead = async (id: number) => {
    try {
      setMarkingId(id);
      const updated = await notificationApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: updated.read_at } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err: any) {
      setError(err?.message || 'Failed to mark notification as read.');
    } finally {
      setMarkingId(null);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      setMarkingAll(true);
      await notificationApi.markAllAsRead();
      const nowIso = new Date().toISOString();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read_at: nowIso }))
      );
      setUnreadCount(0);
    } catch (err: any) {
      setError(err?.message || 'Failed to mark all as read.');
    } finally {
      setMarkingAll(false);
    }
  };

  const renderIcon = (type: NotificationType) => {
    switch (type) {
      case 'OUT_OF_STOCK':
        return <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />;
      case 'LOW_STOCK':
        return <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0" />;
      case 'REPLENISHMENT_RECOMMENDATION':
        return <Sparkles className="h-5 w-5 text-indigo-600 flex-shrink-0" />;
      case 'PURCHASE_ORDER_STATUS':
      case 'PURCHASE_ORDER_RECEIVED':
        return <ClipboardList className="h-5 w-5 text-emerald-600 flex-shrink-0" />;
      case 'FORECAST_GENERATED':
        return <TrendingUp className="h-5 w-5 text-sky-600 flex-shrink-0" />;
      default:
        return <Bell className="h-5 w-5 text-slate-500 flex-shrink-0" />;
    }
  };

  const renderContextualLink = (n: Notification) => {
    if (n.purchase_order_id) {
      return (
        <Link
          to={`/purchase-orders/${n.purchase_order_id}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          View Purchase Order #{n.purchase_order_id} <ExternalLink className="h-3 w-3" />
        </Link>
      );
    }
    if (n.replenishment_recommendation_id) {
      return (
        <Link
          to="/replenishment"
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          View Replenishment Recommendation <ExternalLink className="h-3 w-3" />
        </Link>
      );
    }
    if (n.forecast_id) {
      return (
        <Link
          to="/forecasts"
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          View Forecast Analysis <ExternalLink className="h-3 w-3" />
        </Link>
      );
    }
    if (n.product_id) {
      return (
        <Link
          to="/inventory"
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          View Stock in Inventory <ExternalLink className="h-3 w-3" />
        </Link>
      );
    }
    return null;
  };

  const highPriorityCount = notifications.filter((n) => n.priority === 'HIGH').length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Notifications & Alerts
            </h1>
            {unreadCount > 0 && (
              <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-600 border border-indigo-200">
                {unreadCount} unread
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Real-time alerts for low stock, purchase orders, replenishment suggestions, and demand forecasting.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadNotifications}
            disabled={loading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {unreadCount > 0 && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleMarkAllAsRead}
              disabled={markingAll || loading}
              className="flex items-center gap-1.5"
            >
              <CheckCheck className="h-4 w-4" />
              {markingAll ? 'Marking All...' : 'Mark All Read'}
            </Button>
          )}
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadNotifications} />}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
            <Bell className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Total Notifications</p>
            <p className="text-xl font-bold text-slate-900">{notifications.length}</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Unread Alerts</p>
            <p className="text-xl font-bold text-slate-900">{unreadCount}</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">High Priority</p>
            <p className="text-xl font-bold text-slate-900">{highPriorityCount}</p>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Select
            label="Read Status"
            value={readFilter}
            onChange={(e) => setReadFilter(e.target.value)}
            options={[
              { value: '', label: 'All Statuses' },
              { value: 'unread', label: 'Unread Only' },
              { value: 'read', label: 'Read Only' },
            ]}
          />

          <Select
            label="Alert Type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            options={[
              { value: '', label: 'All Types' },
              { value: 'LOW_STOCK', label: 'Low Stock' },
              { value: 'OUT_OF_STOCK', label: 'Out of Stock' },
              { value: 'REPLENISHMENT_RECOMMENDATION', label: 'Replenishment' },
              { value: 'PURCHASE_ORDER_STATUS', label: 'PO Status' },
              { value: 'PURCHASE_ORDER_RECEIVED', label: 'PO Received' },
              { value: 'FORECAST_GENERATED', label: 'Forecast Generated' },
            ]}
          />

          <Select
            label="Priority"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            options={[
              { value: '', label: 'All Priorities' },
              { value: 'HIGH', label: 'High Priority' },
              { value: 'MEDIUM', label: 'Medium Priority' },
              { value: 'LOW', label: 'Low Priority' },
            ]}
          />
        </div>
      </div>

      {/* Notification List Content */}
      {loading ? (
        <div className="flex justify-center p-12">
          <Spinner />
        </div>
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={<Bell className="h-10 w-10 text-slate-400" />}
          title="No notifications found"
          description="There are no alerts matching the selected filter criteria."
        />
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => {
            return (
              <div
                key={n.id}
                className={`rounded-xl border p-4 sm:p-5 transition-all shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                  n.is_read
                    ? 'border-slate-200 bg-white opacity-85'
                    : 'border-indigo-200 bg-indigo-50/30'
                }`}
              >
                <div className="flex items-start gap-4 flex-1">
                  <div className="mt-1 flex h-10 w-10 items-center justify-center rounded-lg bg-white border border-slate-100 shadow-sm flex-shrink-0">
                    {renderIcon(n.notification_type)}
                  </div>

                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`text-sm font-semibold ${n.is_read ? 'text-slate-800' : 'text-slate-950 font-bold'}`}>
                        {n.title}
                      </span>
                      <StatusBadge status={n.priority} />
                      <StatusBadge status={n.notification_type} />
                      {!n.is_read ? (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 uppercase tracking-wide">
                          Unread
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 uppercase tracking-wide">
                          Read
                        </span>
                      )}
                    </div>

                    <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                      {n.message}
                    </p>

                    <div className="flex flex-wrap items-center gap-4 pt-1">
                      <span className="text-xs text-slate-400">
                        {new Date(n.created_at).toLocaleString([], {
                          dateStyle: 'medium',
                          timeStyle: 'short',
                        })}
                      </span>
                      {renderContextualLink(n)}
                    </div>
                  </div>
                </div>

                {/* Right Action */}
                {!n.is_read && (
                  <div className="flex-shrink-0 self-end sm:self-center">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleMarkAsRead(n.id)}
                      disabled={markingId === n.id}
                      className="flex items-center gap-1 text-xs"
                    >
                      <Check className="h-3.5 w-3.5" />
                      {markingId === n.id ? 'Marking...' : 'Mark as Read'}
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
