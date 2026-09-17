import { apiClient } from './client';
import {
  DemandForecast,
  ForecastMethod,
  ForecastStatus,
} from '../types';

export interface ForecastFilterParams {
  product_id?: number;
  method?: ForecastMethod;
  status?: ForecastStatus;
  generated_from?: string;
  generated_to?: string;
  skip?: number;
  limit?: number;
}

export const forecastApi = {
  generateAll: (method: ForecastMethod = 'SMA') =>
    apiClient.post<DemandForecast[]>('/forecast/generate', null, { params: { method } }),

  generateProduct: (productId: number, method: ForecastMethod = 'SMA') =>
    apiClient.post<DemandForecast>(`/forecast/generate/${productId}`, null, { params: { method } }),

  getAll: (params?: ForecastFilterParams) =>
    apiClient.get<DemandForecast[]>('/forecast', { params }),

  getByProductId: (productId: number) =>
    apiClient.get<DemandForecast>(`/forecast/products/${productId}`),

  getById: (id: number) =>
    apiClient.get<DemandForecast>(`/forecast/${id}`),
};
