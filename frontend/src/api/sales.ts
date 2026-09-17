import { apiClient } from './client';
import { Sale, SaleCreate } from '../types';

export interface SalesFilterParams {
  product_id?: number;
  sold_by?: number;
  reference?: string;
  start_date?: string;
  end_date?: string;
}

export const salesApi = {
  getAll: (params?: SalesFilterParams) =>
    apiClient.get<Sale[]>('/sales', { params }),

  getById: (id: number) =>
    apiClient.get<Sale>(`/sales/${id}`),

  create: (data: SaleCreate) =>
    apiClient.post<Sale>('/sales', data),
};
