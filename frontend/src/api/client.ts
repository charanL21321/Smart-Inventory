const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

let unauthorizedHandler: (() => void) | null = null;

export const setUnauthorizedHandler = (handler: () => void) => {
  unauthorizedHandler = handler;
};

interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers: customHeaders, ...customOptions } = options;

  let url = `${BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const token = localStorage.getItem('access_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...customHeaders,
  };

  const response = await fetch(url, {
    headers,
    ...customOptions,
  });

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    let errorData: any = null;

    try {
      errorData = await response.json();
      if (typeof errorData?.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData?.detail)) {
        errorMessage = errorData.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
      }
    } catch {
      // Non-JSON response
    }

    if (response.status === 401) {
      localStorage.removeItem('access_token');
      if (unauthorizedHandler) {
        unauthorizedHandler();
      }
      window.dispatchEvent(new Event('auth:unauthorized'));
      throw new ApiError(401, errorMessage || 'Your session has expired. Please log in again.', errorData);
    }

    if (response.status === 403) {
      throw new ApiError(403, errorMessage || 'You do not have permission to perform this action.', errorData);
    }

    if (response.status === 404) {
      throw new ApiError(404, errorMessage || 'Requested resource was not found.', errorData);
    }

    throw new ApiError(response.status, errorMessage, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as unknown as T;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string, options?: { params?: Record<string, any> }) =>
    request<T>(endpoint, { method: 'GET', params: options?.params }),

  post: <T>(endpoint: string, data?: any, options?: { params?: Record<string, any> }) =>
    request<T>(endpoint, {
      method: 'POST',
      params: options?.params,
      body: data !== undefined && data !== null ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: any, options?: { params?: Record<string, any> }) =>
    request<T>(endpoint, {
      method: 'PUT',
      params: options?.params,
      body: data !== undefined && data !== null ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: any, options?: { params?: Record<string, any> }) =>
    request<T>(endpoint, {
      method: 'PATCH',
      params: options?.params,
      body: data !== undefined && data !== null ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string, options?: { params?: Record<string, any> }) =>
    request<T>(endpoint, { method: 'DELETE', params: options?.params }),
};
