import { apiClient } from './client';
import { AuthResponse, User } from '../types';

export const authApi = {
  login: (data: { username: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/login', data),

  getMe: () => apiClient.get<User>('/users/me'),
};
