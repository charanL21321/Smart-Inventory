import { apiClient } from './client';
import { Category, CategoryCreate, CategoryUpdate } from '../types';

export const categoriesApi = {
  list: (params?: { is_active?: boolean; search?: string }) =>
    apiClient.get<Category[]>('/categories', { params }),

  getAll: (isActive?: boolean, search?: string) =>
    apiClient.get<Category[]>('/categories', {
      params: {
        is_active: isActive,
        search,
      },
    }),

  getById: (id: number) => apiClient.get<Category>(`/categories/${id}`),

  create: (data: CategoryCreate) => apiClient.post<Category>('/categories', data),

  update: (id: number, data: CategoryUpdate) => apiClient.put<Category>(`/categories/${id}`, data),

  delete: (id: number) => apiClient.delete<void>(`/categories/${id}`),
};
