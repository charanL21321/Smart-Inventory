import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { Notifications } from '../pages/Notifications';
import { AuthProvider } from '../context/AuthContext';
import { notificationApi } from '../api/notifications';
import { Notification } from '../types';

vi.mock('../api/notifications', () => ({
  notificationApi: {
    getAll: vi.fn(),
    getUnreadCount: vi.fn(),
    getById: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
  },
}));

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn().mockResolvedValue({
      id: 1,
      username: 'test_admin',
      email: 'admin@smartinventory.com',
      role: 'ADMIN',
      is_active: true,
      created_at: '2026-01-01',
    }),
  },
}));

const mockNotifications: Notification[] = [
  {
    id: 101,
    user_id: 1,
    notification_type: 'OUT_OF_STOCK',
    priority: 'HIGH',
    title: 'Out of Stock Alert: Thermal Scanner',
    message: 'Stock level reached 0 units for Thermal Scanner.',
    product_id: 5,
    is_read: false,
    created_at: '2026-09-17T10:00:00Z',
  },
  {
    id: 102,
    user_id: 1,
    notification_type: 'REPLENISHMENT_RECOMMENDATION',
    priority: 'HIGH',
    title: 'Replenishment Suggested: Barcode Printer',
    message: 'System recommends purchasing 50 units.',
    product_id: 6,
    replenishment_recommendation_id: 12,
    is_read: false,
    created_at: '2026-09-17T10:15:00Z',
  },
  {
    id: 103,
    user_id: 1,
    notification_type: 'PURCHASE_ORDER_STATUS',
    priority: 'MEDIUM',
    title: 'Purchase Order #8 Status Updated',
    message: 'Purchase order status transitioned to ORDERED.',
    purchase_order_id: 8,
    is_read: true,
    created_at: '2026-09-17T09:00:00Z',
    read_at: '2026-09-17T09:30:00Z',
  },
];

describe('Phase 9 Notifications & Alerts Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'mock_token');
    vi.mocked(notificationApi.getUnreadCount).mockResolvedValue({ unread_count: 2 });
    vi.mocked(notificationApi.getAll).mockResolvedValue(mockNotifications);
    vi.mocked(notificationApi.markAsRead).mockImplementation(async (id: number) => ({
      ...mockNotifications.find((n) => n.id === id)!,
      is_read: true,
      read_at: new Date().toISOString(),
    }));
    vi.mocked(notificationApi.markAllAsRead).mockResolvedValue({ marked_read: 2 });
  });

  describe('Header Notification Bell & Dropdown', () => {
    it('displays unread badge when unread notifications exist', async () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <Header />
          </AuthProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(notificationApi.getUnreadCount).toHaveBeenCalled();
        const badge = screen.getByTestId('notification-badge');
        expect(badge).toBeInTheDocument();
        expect(badge).toHaveTextContent('2');
      });
    });

    it('opens dropdown and displays alerts on bell click', async () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <Header />
          </AuthProvider>
        </MemoryRouter>
      );

      const bell = screen.getByTestId('notification-bell');
      fireEvent.click(bell);

      await waitFor(() => {
        expect(screen.getByTestId('notification-dropdown')).toBeInTheDocument();
        expect(screen.getByText('Notifications')).toBeInTheDocument();
        expect(screen.getAllByText(/Thermal Scanner/i).length).toBeGreaterThan(0);
        expect(screen.getByText(/View all notifications/i)).toBeInTheDocument();
      });
    });

    it('triggers mark all as read from dropdown', async () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <Header />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.click(screen.getByTestId('notification-bell'));

      await waitFor(() => {
        expect(screen.getByText('Mark all read')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Mark all read'));

      await waitFor(() => {
        expect(notificationApi.markAllAsRead).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Dedicated Notifications Page', () => {
    it('renders page header, metrics cards, and notifications list', async () => {
      render(
        <MemoryRouter>
          <Notifications />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Notifications & Alerts')).toBeInTheDocument();
        expect(screen.getByText('Total Notifications')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument(); // total mock items
        expect(screen.getByText('Unread Alerts')).toBeInTheDocument();
        expect(screen.getByText('Out of Stock Alert: Thermal Scanner')).toBeInTheDocument();
        expect(screen.getByText('Replenishment Suggested: Barcode Printer')).toBeInTheDocument();
        expect(screen.getByText('Purchase Order #8 Status Updated')).toBeInTheDocument();
      });
    });

    it('renders contextual navigation links to PO and Replenishment', async () => {
      render(
        <MemoryRouter>
          <Notifications />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('View Purchase Order #8')).toBeInTheDocument();
        expect(screen.getByText('View Replenishment Recommendation')).toBeInTheDocument();
        expect(screen.getByText('View Stock in Inventory')).toBeInTheDocument();
      });
    });

    it('allows marking a single notification as read', async () => {
      render(
        <MemoryRouter>
          <Notifications />
        </MemoryRouter>
      );

      await waitFor(() => {
        const markBtns = screen.getAllByRole('button', { name: /mark as read/i });
        expect(markBtns.length).toBeGreaterThan(0);
        fireEvent.click(markBtns[0]);
      });

      await waitFor(() => {
        expect(notificationApi.markAsRead).toHaveBeenCalled();
      });
    });

    it('allows marking all notifications as read from the page header', async () => {
      render(
        <MemoryRouter>
          <Notifications />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /mark all read/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /mark all read/i }));

      await waitFor(() => {
        expect(notificationApi.markAllAsRead).toHaveBeenCalled();
      });
    });
  });
});
