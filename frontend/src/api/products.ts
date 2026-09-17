import { apiClient } from './client';
import { Product, ProductCreate, ProductUpdate } from '../types';

export interface ProductFilterParams {
  category_id?: number;
  supplier_id?: number;
  is_active?: boolean;
  search?: string;
  sku?: string;
}

export const productsApi = {
  getAll: (params?: ProductFilterParams) =>
    apiClient.get<Product[]>('/products', { params }),

  getById: (id: number) =>
    apiClient.get<Product>(`/products/${id}`),

  create: (data: ProductCreate) =>
    apiClient.post<Product>('/products', data),

  update: (id: number, data: ProductUpdate) =>
    apiClient.put<Product>(`/products/${id}`, data),

  delete: (id: number) =>
    apiClient.delete<void>(`/products/${id}`),
};
