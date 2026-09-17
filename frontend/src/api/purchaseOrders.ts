import { apiClient } from './client';
import {
  PurchaseOrder,
  PurchaseOrderCreate,
  PurchaseOrderReceiveRequest,
  PurchaseOrderStatus,
  PurchaseOrderStatusUpdate,
  PurchaseOrderUpdate,
} from '../types';

export interface PurchaseOrderFilterParams {
  supplier_id?: number;
  status?: PurchaseOrderStatus;
  created_by?: number;
  start_date?: string;
  end_date?: string;
}

export const purchaseOrdersApi = {
  getAll: (params?: PurchaseOrderFilterParams) =>
    apiClient.get<PurchaseOrder[]>('/purchase-orders', { params }),

  getById: (id: number) =>
    apiClient.get<PurchaseOrder>(`/purchase-orders/${id}`),

  create: (data: PurchaseOrderCreate) =>
    apiClient.post<PurchaseOrder>('/purchase-orders', data),

  update: (id: number, data: PurchaseOrderUpdate) =>
    apiClient.put<PurchaseOrder>(`/purchase-orders/${id}`, data),

  updateStatus: (id: number, data: PurchaseOrderStatusUpdate) =>
    apiClient.patch<PurchaseOrder>(`/purchase-orders/${id}/status`, data),

  receive: (id: number, data: PurchaseOrderReceiveRequest) =>
    apiClient.post<PurchaseOrder>(`/purchase-orders/${id}/receive`, data),
};
