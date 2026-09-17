import { apiClient } from './client';
import { Supplier, SupplierCreate, SupplierUpdate } from '../types';

export const suppliersApi = {
  list: (params?: { is_active?: boolean; search?: string }) =>
    apiClient.get<Supplier[]>('/suppliers', { params }),

  getAll: (isActive?: boolean, search?: string) =>
    apiClient.get<Supplier[]>('/suppliers', {
      params: {
        is_active: isActive,
        search,
      },
    }),

  getById: (id: number) => apiClient.get<Supplier>(`/suppliers/${id}`),

  create: (data: SupplierCreate) => apiClient.post<Supplier>('/suppliers', data),

  update: (id: number, data: SupplierUpdate) => apiClient.put<Supplier>(`/suppliers/${id}`, data),

  delete: (id: number) => apiClient.delete<void>(`/suppliers/${id}`),
};
