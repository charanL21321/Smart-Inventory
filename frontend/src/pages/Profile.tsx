import React from 'react';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { Button } from '../components/common/Button';
import { User as UserIcon, Shield, Check, X, LogOut, Mail, Calendar } from 'lucide-react';

export const Profile: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const rolePermissions = {
    ADMIN: {
      catalog: true,
      stockIn: true,
      stockOut: true,
      stockAdjust: true,
      sales: true,
      poManage: true,
      poReceive: true,
      replenishment: true,
      forecasting: true,
    },
    INVENTORY_MANAGER: {
      catalog: true,
      stockIn: true,
      stockOut: true,
      stockAdjust: true,
      sales: true,
      poManage: true,
      poReceive: true,
      replenishment: true,
      forecasting: true,
    },
    WAREHOUSE_STAFF: {
      catalog: false, // read only
      stockIn: true,
      stockOut: true,
      stockAdjust: false, // strictly forbidden
      sales: true,
      poManage: false, // cannot create/approve PO
      poReceive: true, // can physical receive
      replenishment: false, // view only
      forecasting: false, // view only
    },
  };

  const perms = rolePermissions[user.role] || rolePermissions.WAREHOUSE_STAFF;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">User Profile & Access Rights</h2>
        <p className="text-sm text-slate-500">
          Account credentials, identity verification, and role-based privilege mapping.
        </p>
      </div>

      {/* User Info Card */}
      <div className="card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600 text-white text-2xl font-bold shadow-md">
            {user.username.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-xl font-bold text-slate-900">{user.full_name || user.username}</h3>
              <StatusBadge status={user.role} />
            </div>
            <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Mail className="h-3.5 w-3.5" /> {user.email}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" /> Joined {new Date(user.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        <Button
          variant="secondary"
          onClick={logout}
          icon={<LogOut className="h-4 w-4 text-rose-600" />}
        >
          Sign Out
        </Button>
      </div>

      {/* Permissions Matrix */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-indigo-600" />
            <h4 className="text-base font-bold text-slate-900">Role Privilege Matrix</h4>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Enforced by both backend API route security dependencies and frontend UI controls.
          </p>
        </div>

        <div className="table-container border-0 rounded-none">
          <table className="table">
            <thead>
              <tr>
                <th>Operational Capability</th>
                <th>Access Scope</th>
                <th className="text-right">Granted to Your Account</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="font-semibold text-slate-800">Catalog Management</td>
                <td className="text-xs text-slate-500">
                  Create, update, or delete products, categories, and supplier records
                </td>
                <td className="text-right">
                  {perms.catalog ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                      <Check className="h-4 w-4" /> Allowed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400">
                      <X className="h-4 w-4" /> Read Only
                    </span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Stock Movements (In / Out)</td>
                <td className="text-xs text-slate-500">
                  Perform stock-in receiving and dispatch stock-out
                </td>
                <td className="text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                    <Check className="h-4 w-4" /> Allowed
                  </span>
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Manual Stock Adjustment</td>
                <td className="text-xs text-slate-500">
                  Reconcile stock count discrepancy with mandatory audit log
                </td>
                <td className="text-right">
                  {perms.stockAdjust ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                      <Check className="h-4 w-4" /> Allowed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-500">
                      <X className="h-4 w-4" /> Forbidden
                    </span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Sales Recording</td>
                <td className="text-xs text-slate-500">Record customer sales order and deduct stock</td>
                <td className="text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                    <Check className="h-4 w-4" /> Allowed
                  </span>
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Purchase Order Lifecycle</td>
                <td className="text-xs text-slate-500">
                  Create draft POs, submit, approve, and place supplier orders
                </td>
                <td className="text-right">
                  {perms.poManage ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                      <Check className="h-4 w-4" /> Allowed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400">
                      <X className="h-4 w-4" /> Read Only
                    </span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Purchase Order Goods Receipt</td>
                <td className="text-xs text-slate-500">
                  Accept incoming supplier shipments and increment stock balances
                </td>
                <td className="text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                    <Check className="h-4 w-4" /> Allowed
                  </span>
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Replenishment Engine Controls</td>
                <td className="text-xs text-slate-500">
                  Trigger automated replenishment analysis, mark reviewed, or dismiss
                </td>
                <td className="text-right">
                  {perms.replenishment ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                      <Check className="h-4 w-4" /> Allowed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400">
                      <X className="h-4 w-4" /> Read Only
                    </span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="font-semibold text-slate-800">Forecasting Engine Controls</td>
                <td className="text-xs text-slate-500">
                  Trigger SMA/WMA time-series forecasting calculations
                </td>
                <td className="text-right">
                  {perms.forecasting ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                      <Check className="h-4 w-4" /> Allowed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400">
                      <X className="h-4 w-4" /> Read Only
                    </span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
