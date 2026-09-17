import { apiClient } from './client';
import {
  RecommendationPriority,
  RecommendationStatus,
  ReplenishmentDismissRequest,
  ReplenishmentRecommendation,
} from '../types';

export interface ReplenishmentFilterParams {
  status?: RecommendationStatus;
  priority?: RecommendationPriority;
  product_id?: number;
  supplier_id?: number;
}

export const replenishmentApi = {
  generate: () =>
    apiClient.post<ReplenishmentRecommendation[]>('/replenishment/generate'),

  getAll: (params?: ReplenishmentFilterParams) =>
    apiClient.get<ReplenishmentRecommendation[]>('/replenishment/recommendations', { params }),

  getById: (id: number) =>
    apiClient.get<ReplenishmentRecommendation>(`/replenishment/recommendations/${id}`),

  review: (id: number) =>
    apiClient.patch<ReplenishmentRecommendation>(`/replenishment/recommendations/${id}/review`),

  dismiss: (id: number, data: ReplenishmentDismissRequest) =>
    apiClient.patch<ReplenishmentRecommendation>(`/replenishment/recommendations/${id}/dismiss`, data),
};
