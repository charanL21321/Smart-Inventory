import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Boxes,
  Tags,
  Truck,
  Warehouse,
  Receipt,
  ShoppingCart,
  ClipboardList,
  Sparkles,
  TrendingUp,
  UserCheck,
  Package,
  Bell,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { hasRole } = useAuth();

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { to: '/inventory', label: 'Inventory Stock', icon: Warehouse },
    { to: '/inventory/transactions', label: 'Ledger Audit', icon: Receipt },
    { to: '/products', label: 'Products', icon: Boxes },
    {
      to: '/categories',
      label: 'Categories',
      icon: Tags,
      roles: ['ADMIN', 'INVENTORY_MANAGER'] as const,
    },
    {
      to: '/suppliers',
      label: 'Suppliers',
      icon: Truck,
      roles: ['ADMIN', 'INVENTORY_MANAGER'] as const,
    },
    { to: '/sales', label: 'Sales Orders', icon: ShoppingCart },
    { to: '/purchase-orders', label: 'Purchase Orders', icon: ClipboardList },
    { to: '/replenishment', label: 'Replenishment', icon: Sparkles },
    { to: '/forecasts', label: 'Demand Forecasting', icon: TrendingUp },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/profile', label: 'User Profile', icon: UserCheck },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800 min-h-screen">
      {/* Platform Branding */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md">
          <Package className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-wide">SMART INVENTORY</h1>
          <p className="text-[10px] uppercase font-medium text-slate-400">Replenishment Suite</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          if (item.roles && !hasRole(...item.roles)) {
            return null;
          }
          const Icon = item.icon;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`
              }
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
        Enterprise Edition v1.0
      </div>
    </aside>
  );
};
