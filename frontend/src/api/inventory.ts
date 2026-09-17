import { apiClient } from './client';
import {
  Inventory,
  InventoryTransaction,
  StockAdjustmentRequest,
  StockInRequest,
  StockOutRequest,
  TransactionType,
} from '../types';

export interface InventoryFilterParams {
  product_id?: number;
  low_stock?: boolean;
  out_of_stock?: boolean;
}

export interface TransactionFilterParams {
  product_id?: number;
  transaction_type?: TransactionType;
  performed_by?: number;
}

export const inventoryApi = {
  getAll: (params?: InventoryFilterParams) =>
    apiClient.get<Inventory[]>('/inventory', { params }),

  getByProductId: (productId: number) =>
    apiClient.get<Inventory>(`/inventory/${productId}`),

  stockIn: (data: StockInRequest) =>
    apiClient.post<Inventory>('/inventory/stock-in', data),

  stockOut: (data: StockOutRequest) =>
    apiClient.post<Inventory>('/inventory/stock-out', data),

  adjustment: (data: StockAdjustmentRequest) =>
    apiClient.post<Inventory>('/inventory/adjustment', data),

  getTransactions: (params?: TransactionFilterParams) =>
    apiClient.get<InventoryTransaction[]>('/inventory/transactions', { params }),

  getTransactionById: (id: number) =>
    apiClient.get<InventoryTransaction>(`/inventory/transactions/${id}`),
};
