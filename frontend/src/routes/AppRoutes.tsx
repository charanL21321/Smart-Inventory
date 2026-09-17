import React from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { AppLayout } from '../components/layout/AppLayout';

// Pages
import { Login } from '../pages/Login';
import { Dashboard } from '../pages/Dashboard';
import { Products } from '../pages/Products';
import { Categories } from '../pages/Categories';
import { Suppliers } from '../pages/Suppliers';
import { InventoryPage } from '../pages/Inventory';
import { InventoryTransactions } from '../pages/InventoryTransactions';
import { Sales } from '../pages/Sales';
import { PurchaseOrders } from '../pages/PurchaseOrders';
import { PurchaseOrderDetail } from '../pages/PurchaseOrderDetail';
import { Replenishment } from '../pages/Replenishment';
import { Forecasts } from '../pages/Forecasts';
import { ForecastDetail } from '../pages/ForecastDetail';
import { Profile } from '../pages/Profile';
import { FileQuestion, ArrowLeft } from 'lucide-react';

const NotFound: React.FC = () => (
  <div className="flex min-h-[60vh] flex-col items-center justify-center p-8 text-center">
    <div className="rounded-full bg-slate-100 p-4 text-slate-400 mb-4">
      <FileQuestion className="h-12 w-12" />
    </div>
    <h2 className="text-2xl font-bold text-slate-800">Page Not Found (404)</h2>
    <p className="mt-2 text-sm text-slate-500 max-w-sm">
      The page or resource you requested does not exist or has been moved.
    </p>
    <Link
      to="/dashboard"
      className="mt-6 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
    >
      <ArrowLeft className="h-4 w-4" /> Return to Dashboard
    </Link>
  </div>
);

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<Login />} />

      {/* Protected Operations Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route
          path="categories"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'INVENTORY_MANAGER']}>
              <Categories />
            </ProtectedRoute>
          }
        />
        <Route
          path="suppliers"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'INVENTORY_MANAGER']}>
              <Suppliers />
            </ProtectedRoute>
          }
        />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="inventory/transactions" element={<InventoryTransactions />} />
        <Route path="sales" element={<Sales />} />
        <Route path="purchase-orders" element={<PurchaseOrders />} />
        <Route path="purchase-orders/:id" element={<PurchaseOrderDetail />} />
        <Route path="replenishment" element={<Replenishment />} />
        <Route path="forecasts" element={<Forecasts />} />
        <Route path="forecasts/:id" element={<ForecastDetail />} />
        <Route path="profile" element={<Profile />} />
        <Route path="*" element={<NotFound />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
