import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Login } from '../pages/Login';
import { Profile } from '../pages/Profile';
import { Dashboard } from '../pages/Dashboard';
import { AuthProvider } from '../context/AuthContext';

// Mocks
vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}));

vi.mock('../api/inventory', () => ({
  inventoryApi: {
    getAll: vi.fn().mockResolvedValue([
      {
        id: 1,
        product_id: 10,
        current_stock: 5,
        reserved_stock: 0,
        available_stock: 5,
        status: 'LOW_STOCK',
        created_at: '2026-09-01',
        product: { name: 'Thermal Scanner', sku: 'SCAN-01' },
      },
    ]),
  },
}));

vi.mock('../api/replenishment', () => ({
  replenishmentApi: {
    getAll: vi.fn().mockResolvedValue([
      {
        id: 1,
        product_id: 10,
        supplier_id: 2,
        current_stock: 5,
        reserved_stock: 0,
        inventory_position: 5,
        reorder_point: 20,
        safety_stock: 10,
        target_stock: 100,
        average_daily_demand: 3,
        lead_time_days: 7,
        lead_time_demand: 21,
        recommended_quantity: 95,
        minimum_order_quantity: 20,
        priority: 'HIGH',
        reason: 'Current stock 5 is below reorder threshold 20',
        status: 'PENDING',
        generated_at: '2026-09-17',
        updated_at: '2026-09-17',
        product: { name: 'Thermal Scanner', sku: 'SCAN-01' },
      },
    ]),
  },
}));

vi.mock('../api/purchaseOrders', () => ({
  purchaseOrdersApi: {
    getAll: vi.fn().mockResolvedValue([]),
  },
}));

import { authApi } from '../api/auth';

describe('Application Pages', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Login Page', () => {
    it('renders the login form elements', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <Login />
          </AuthProvider>
        </MemoryRouter>
      );
      expect(screen.getByText(/Sign in to Smart Inventory/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });
  });

  describe('Dashboard Page', () => {
    it('loads and displays inventory metrics and replenishment alerts', async () => {
      render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Inventory Operations Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Low Stock Alert')).toBeInTheDocument();
        expect(screen.getByText('Pending Actions')).toBeInTheDocument();
        expect(screen.getAllByText('Thermal Scanner').length).toBeGreaterThan(0);
      });
    });
  });

  describe('Profile Page', () => {
    it('displays user profile and role privilege matrix', async () => {
      localStorage.setItem('access_token', 'mock_jwt_token');
      vi.mocked(authApi.getMe).mockResolvedValueOnce({
        id: 1,
        username: 'lead_operator',
        email: 'operator@smartinventory.com',
        role: 'INVENTORY_MANAGER',
        is_active: true,
        created_at: '2026-01-15',
      });

      render(
        <MemoryRouter>
          <AuthProvider>
            <Profile />
          </AuthProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('User Profile & Access Rights')).toBeInTheDocument();
        expect(screen.getByText('operator@smartinventory.com')).toBeInTheDocument();
        expect(screen.getByText('Role Privilege Matrix')).toBeInTheDocument();
      });
    });
  });
});
