import React from 'react';
import { Badge, BadgeVariant } from './Badge';
import {
  ForecastMethod,
  ForecastStatus,
  InventoryStatus,
  PurchaseOrderStatus,
  RecommendationPriority,
  RecommendationStatus,
  TransactionType,
  UserRole,
} from '../../types';

interface StatusBadgeProps {
  status:
    | InventoryStatus
    | PurchaseOrderStatus
    | RecommendationPriority
    | RecommendationStatus
    | ForecastStatus
    | ForecastMethod
    | TransactionType
    | UserRole
    | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  let variant: BadgeVariant = 'neutral';
  let label: string = status;

  switch (status) {
    // Inventory Statuses
    case 'IN_STOCK':
      variant = 'success';
      label = 'In Stock';
      break;
    case 'LOW_STOCK':
      variant = 'warning';
      label = 'Low Stock';
      break;
    case 'OUT_OF_STOCK':
      variant = 'danger';
      label = 'Out of Stock';
      break;

    // Purchase Order Statuses
    case 'DRAFT':
      variant = 'neutral';
      label = 'Draft';
      break;
    case 'PENDING_APPROVAL':
      variant = 'warning';
      label = 'Pending Approval';
      break;
    case 'APPROVED':
      variant = 'info';
      label = 'Approved';
      break;
    case 'ORDERED':
      variant = 'primary';
      label = 'Ordered';
      break;
    case 'PARTIALLY_RECEIVED':
      variant = 'warning';
      label = 'Partially Received';
      break;
    case 'RECEIVED':
      variant = 'success';
      label = 'Received';
      break;
    case 'CANCELLED':
      variant = 'danger';
      label = 'Cancelled';
      break;

    // Recommendation Priorities
    case 'HIGH':
      variant = 'danger';
      label = 'High Priority';
      break;
    case 'MEDIUM':
      variant = 'warning';
      label = 'Medium Priority';
      break;
    case 'LOW':
      variant = 'neutral';
      label = 'Low Priority';
      break;

    // Recommendation Statuses
    case 'PENDING':
      variant = 'warning';
      label = 'Pending';
      break;
    case 'REVIEWED':
      variant = 'info';
      label = 'Reviewed';
      break;
    case 'DISMISSED':
      variant = 'neutral';
      label = 'Dismissed';
      break;

    // Forecast Statuses
    case 'GENERATED':
      variant = 'success';
      label = 'Generated';
      break;
    case 'ARCHIVED':
      variant = 'neutral';
      label = 'Archived';
      break;

    // Forecast Methods
    case 'SMA':
      variant = 'info';
      label = 'SMA';
      break;
    case 'WMA':
      variant = 'primary';
      label = 'WMA';
      break;

    // Transaction Types
    case 'STOCK_IN':
      variant = 'success';
      label = 'Stock In';
      break;
    case 'STOCK_OUT':
      variant = 'danger';
      label = 'Stock Out';
      break;
    case 'ADJUSTMENT_IN':
      variant = 'info';
      label = 'Adjust In';
      break;
    case 'ADJUSTMENT_OUT':
      variant = 'warning';
      label = 'Adjust Out';
      break;

    // Roles
    case 'ADMIN':
      variant = 'danger';
      label = 'Admin';
      break;
    case 'INVENTORY_MANAGER':
      variant = 'primary';
      label = 'Inventory Manager';
      break;
    case 'WAREHOUSE_STAFF':
      variant = 'neutral';
      label = 'Warehouse Staff';
      break;

    // Notification Types
    case 'REPLENISHMENT_RECOMMENDATION':
      variant = 'primary';
      label = 'Replenishment';
      break;
    case 'PURCHASE_ORDER_STATUS':
      variant = 'info';
      label = 'PO Status';
      break;
    case 'PURCHASE_ORDER_RECEIVED':
      variant = 'success';
      label = 'PO Received';
      break;
    case 'FORECAST_GENERATED':
      variant = 'info';
      label = 'Forecast Generated';
      break;
    case 'UNREAD':
      variant = 'warning';
      label = 'Unread';
      break;
    case 'READ':
      variant = 'neutral';
      label = 'Read';
      break;

    default:
      variant = 'neutral';
      label = String(status);
  }

  return (
    <Badge variant={variant} className={className}>
      {label}
    </Badge>
  );
};
