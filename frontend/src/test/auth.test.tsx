import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { ProtectedRoute } from '../routes/ProtectedRoute';

// Mock authApi
vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}));

import { authApi } from '../api/auth';

const TestConsumer: React.FC = () => {
  const { user, isAuthenticated, hasRole } = useAuth();
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'LOGGED_IN' : 'LOGGED_OUT'}</div>
      <div data-testid="user-role">{user?.role}</div>
      <div data-testid="is-admin">{hasRole('ADMIN') ? 'YES' : 'NO'}</div>
    </div>
  );
};

describe('AuthContext and ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initializes as unauthenticated when localStorage has no token', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('LOGGED_OUT');
    });
  });

  it('restores session when token exists and getMe succeeds', async () => {
    localStorage.setItem('access_token', 'mock_jwt_token');
    vi.mocked(authApi.getMe).mockResolvedValueOnce({
      id: 1,
      username: 'admin_user',
      email: 'admin@company.com',
      role: 'ADMIN',
      is_active: true,
      created_at: '2026-01-01',
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('LOGGED_IN');
      expect(screen.getByTestId('user-role')).toHaveTextContent('ADMIN');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('YES');
    });
  });

  it('blocks warehouse staff from admin routes with 403 screen', async () => {
    localStorage.setItem('access_token', 'mock_jwt_token');
    vi.mocked(authApi.getMe).mockResolvedValueOnce({
      id: 2,
      username: 'warehouse_staff',
      email: 'staff@company.com',
      role: 'WAREHOUSE_STAFF',
      is_active: true,
      created_at: '2026-01-01',
    });

    render(
      <MemoryRouter initialEntries={['/admin-only']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin-only"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <div>Admin Secret Area</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Access Restricted \(403\)/i)).toBeInTheDocument();
      expect(screen.queryByText('Admin Secret Area')).not.toBeInTheDocument();
    });
  });
});
