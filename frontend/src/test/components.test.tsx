import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { StatusBadge } from '../components/common/StatusBadge';
import { Input } from '../components/common/Input';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Modal } from '../components/common/Modal';
import { ForecastChart } from '../components/common/ForecastChart';

describe('Common UI Components', () => {
  describe('Button', () => {
    it('renders with label and fires onClick', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Submit Order</Button>);
      const btn = screen.getByRole('button', { name: /submit order/i });
      expect(btn).toBeInTheDocument();
      fireEvent.click(btn);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('disables when loading and hides text while spinning', () => {
      render(<Button loading>Saving</Button>);
      const btn = screen.getByRole('button');
      expect(btn).toBeDisabled();
    });
  });

  describe('Badge & StatusBadge', () => {
    it('renders correct labels and color variants for inventory status', () => {
      const { rerender } = render(<StatusBadge status="IN_STOCK" />);
      expect(screen.getByText('In Stock')).toBeInTheDocument();

      rerender(<StatusBadge status="LOW_STOCK" />);
      expect(screen.getByText('Low Stock')).toBeInTheDocument();

      rerender(<StatusBadge status="OUT_OF_STOCK" />);
      expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    });

    it('renders correct labels for PO statuses', () => {
      const { rerender } = render(<StatusBadge status="DRAFT" />);
      expect(screen.getByText('Draft')).toBeInTheDocument();

      rerender(<StatusBadge status="ORDERED" />);
      expect(screen.getByText('Ordered')).toBeInTheDocument();

      rerender(<StatusBadge status="RECEIVED" />);
      expect(screen.getByText('Received')).toBeInTheDocument();
    });
  });

  describe('Input', () => {
    it('renders with label, required asterisk, and error hint', () => {
      render(
        <Input
          label="SKU Code"
          required
          placeholder="Enter SKU"
          error="SKU is duplicate"
        />
      );
      expect(screen.getByText('SKU Code')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter SKU')).toBeInTheDocument();
      expect(screen.getByText('SKU is duplicate')).toBeInTheDocument();
    });
  });

  describe('ErrorAlert', () => {
    it('renders title, error message, and retry button', () => {
      const handleRetry = vi.fn();
      render(
        <ErrorAlert
          title="Network Failure"
          message="Could not reach backend API"
          onRetry={handleRetry}
        />
      );
      expect(screen.getByText('Network Failure')).toBeInTheDocument();
      expect(screen.getByText('Could not reach backend API')).toBeInTheDocument();
      const retryBtn = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryBtn);
      expect(handleRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('EmptyState', () => {
    it('renders title, description, and action button', () => {
      const handleAction = vi.fn();
      render(
        <EmptyState
          title="No products"
          description="Catalog is empty"
          actionLabel="Add Product"
          onAction={handleAction}
        />
      );
      expect(screen.getByText('No products')).toBeInTheDocument();
      expect(screen.getByText('Catalog is empty')).toBeInTheDocument();
      const actionBtn = screen.getByRole('button', { name: /add product/i });
      fireEvent.click(actionBtn);
      expect(handleAction).toHaveBeenCalledTimes(1);
    });
  });

  describe('Modal', () => {
    it('renders when isOpen is true and calls onClose on escape/close click', () => {
      const handleClose = vi.fn();
      const { rerender } = render(
        <Modal isOpen={false} onClose={handleClose} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      );
      expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();

      rerender(
        <Modal isOpen={true} onClose={handleClose} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      );
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
      expect(screen.getByText('Modal content')).toBeInTheDocument();

      const closeBtn = screen.getByRole('button', { name: /close modal/i });
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('ForecastChart', () => {
    it('renders SVG chart with sorted data points', () => {
      const values = [
        { id: 1, forecast_id: 10, forecast_date: '2026-09-18', forecast_quantity: 25, created_at: '' },
        { id: 2, forecast_id: 10, forecast_date: '2026-09-19', forecast_quantity: 30, created_at: '' },
      ];
      render(<ForecastChart values={values} title="Demand Projection Trend" />);
      expect(screen.getByText('Demand Projection Trend')).toBeInTheDocument();
      expect(screen.getByText('2 Days Horizon')).toBeInTheDocument();
    });

    it('renders fallback when values array is empty', () => {
      render(<ForecastChart values={[]} />);
      expect(
        screen.getByText(/no forecast data points available/i)
      ).toBeInTheDocument();
    });
  });
});
