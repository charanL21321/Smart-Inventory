import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { StatusBadge } from '../common/StatusBadge';
import {
  LogOut,
  Bell,
  CheckCheck,
  AlertTriangle,
  AlertCircle,
  TrendingUp,
  ClipboardList,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { notificationApi } from '../../api/notifications';
import { Notification, NotificationType } from '../../types';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const [recentNotifications, setRecentNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchUnreadCount = async () => {
    try {
      const res = await notificationApi.getUnreadCount();
      setUnreadCount(res.unread_count);
    } catch {
      // Keep silent on background count check failure
    }
  };

  const fetchRecentNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationApi.getAll({ limit: 8 });
      setRecentNotifications(data);
    } catch {
      // Ignore background load error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  useEffect(() => {
    if (dropdownOpen) {
      fetchRecentNotifications();
      fetchUnreadCount();
    }
  }, [dropdownOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  const handleMarkAsRead = async (notification: Notification, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (notification.is_read) return;

    try {
      await notificationApi.markAsRead(notification.id);
      setRecentNotifications((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // Ignore failure
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      setRecentNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch {
      // Ignore failure
    }
  };

  const getTargetUrl = (notification: Notification): string | null => {
    if (notification.purchase_order_id) {
      return `/purchase-orders/${notification.purchase_order_id}`;
    }
    if (notification.replenishment_recommendation_id) {
      return '/replenishment';
    }
    if (notification.forecast_id) {
      return '/forecasts';
    }
    if (notification.product_id) {
      return '/inventory';
    }
    return null;
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      await handleMarkAsRead(notification);
    }
    const target = getTargetUrl(notification);
    if (target) {
      setDropdownOpen(false);
      navigate(target);
    }
  };

  const renderIcon = (type: NotificationType) => {
    switch (type) {
      case 'OUT_OF_STOCK':
        return <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />;
      case 'LOW_STOCK':
        return <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />;
      case 'REPLENISHMENT_RECOMMENDATION':
        return <Sparkles className="h-4 w-4 text-indigo-600 flex-shrink-0" />;
      case 'PURCHASE_ORDER_STATUS':
      case 'PURCHASE_ORDER_RECEIVED':
        return <ClipboardList className="h-4 w-4 text-emerald-600 flex-shrink-0" />;
      case 'FORECAST_GENERATED':
        return <TrendingUp className="h-4 w-4 text-sky-600 flex-shrink-0" />;
      default:
        return <Bell className="h-4 w-4 text-slate-500 flex-shrink-0" />;
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-sm sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Smart Operations Portal
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Notification Bell with Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            data-testid="notification-bell"
            aria-label="Notifications"
            onClick={() => setDropdownOpen((prev) => !prev)}
            className="relative p-2 text-slate-600 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer border-0 bg-transparent"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span
                data-testid="notification-badge"
                className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white shadow-sm"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {dropdownOpen && (
            <div
              data-testid="notification-dropdown"
              className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-white shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in slide-in-from-top-2"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    onClick={handleMarkAllRead}
                    className="flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-800 cursor-pointer border-0 bg-transparent"
                  >
                    <CheckCheck className="h-3.5 w-3.5" />
                    Mark all read
                  </button>
                )}
              </div>

              {/* Notification List */}
              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                {loading ? (
                  <div className="p-6 text-center text-xs text-slate-400">Loading alerts...</div>
                ) : recentNotifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500">
                    <Bell className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                    No notifications yet
                  </div>
                ) : (
                  recentNotifications.map((n) => {
                    const hasLink = Boolean(getTargetUrl(n));
                    return (
                      <div
                        key={n.id}
                        onClick={() => handleNotificationClick(n)}
                        className={`p-3 transition-colors cursor-pointer flex gap-3 ${
                          n.is_read ? 'hover:bg-slate-50 opacity-75' : 'bg-indigo-50/40 hover:bg-indigo-50/70'
                        }`}
                      >
                        <div className="pt-0.5">{renderIcon(n.notification_type)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1 mb-0.5">
                            <span className={`text-xs font-semibold truncate ${n.is_read ? 'text-slate-700' : 'text-slate-900'}`}>
                              {n.title}
                            </span>
                            {!n.is_read && (
                              <span className="h-2 w-2 rounded-full bg-indigo-600 flex-shrink-0" />
                            )}
                          </div>
                          <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed mb-1">
                            {n.message}
                          </p>
                          <div className="flex items-center justify-between text-[11px] text-slate-400">
                            <span>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })}</span>
                            <div className="flex items-center gap-2">
                              {hasLink && (
                                <span className="flex items-center gap-0.5 text-indigo-600 hover:underline">
                                  View <ExternalLink className="h-3 w-3" />
                                </span>
                              )}
                              {!n.is_read && (
                                <button
                                  type="button"
                                  onClick={(e) => handleMarkAsRead(n, e)}
                                  className="text-slate-500 hover:text-slate-800 text-[11px] font-medium border-0 bg-transparent p-0 cursor-pointer"
                                >
                                  Mark read
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Footer */}
              <div className="border-t border-slate-100 px-4 py-2 text-center bg-slate-50/50 rounded-b-xl">
                <Link
                  to="/notifications"
                  onClick={() => setDropdownOpen(false)}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors inline-block"
                >
                  View all notifications &rarr;
                </Link>
              </div>
            </div>
          )}
        </div>

        <div className="h-5 w-px bg-slate-200" />

        {user && (
          <Link
            to="/profile"
            className="flex items-center gap-3 p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-inherit no-underline"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-semibold text-xs border border-indigo-200">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-semibold text-slate-800 leading-tight">
                {user.full_name || user.username}
              </div>
              <div className="text-[11px] text-slate-500">{user.email}</div>
            </div>
            <StatusBadge status={user.role} />
          </Link>
        )}

        <div className="h-5 w-px bg-slate-200" />

        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-rose-600 p-2 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer border-0 bg-transparent"
          title="Sign Out"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden md:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
};
