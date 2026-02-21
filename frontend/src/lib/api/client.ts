/**
 * API client with JWT injection and automatic token refresh on 401.
 *
 * Uses native fetch (no extra dependencies). Token getter/setter are
 * injected so the client stays decoupled from React state.
 */

import { API_ENDPOINTS } from './endpoints';
import type { TokenResponse } from '@/types/auth';

export interface ApiClientConfig {
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  onTokenRefreshed: (tokens: TokenResponse) => void;
  onAuthFailure: () => void;
}

export class ApiClient {
  private config: ApiClientConfig;
  private refreshPromise: Promise<TokenResponse | null> | null = null;

  constructor(config: ApiClientConfig) {
    this.config = config;
  }

  async get<T>(url: string): Promise<T> {
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>(url, { method: 'DELETE' });
  }

  private async request<T>(url: string, init: RequestInit): Promise<T> {
    const headers = new Headers(init.headers);
    const token = this.config.getAccessToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    let response = await fetch(url, { ...init, headers });

    if (response.status === 401 && this.config.getRefreshToken()) {
      const refreshed = await this.tryRefresh();
      if (refreshed) {
        headers.set('Authorization', `Bearer ${refreshed.access_token}`);
        response = await fetch(url, { ...init, headers });
      }
    }

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      const message =
        errorBody?.detail ?? errorBody?.message ?? `Request failed: ${response.status}`;
      throw new ApiError(response.status, message);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  /**
   * Deduplicates concurrent refresh calls so only one network request
   * is made even if multiple 401s arrive at the same time.
   */
  private async tryRefresh(): Promise<TokenResponse | null> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.executeRefresh();

    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async executeRefresh(): Promise<TokenResponse | null> {
    const refreshToken = this.config.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.config.onAuthFailure();
        return null;
      }

      const tokens: TokenResponse = await response.json();
      this.config.onTokenRefreshed(tokens);
      return tokens;
    } catch {
      this.config.onAuthFailure();
      return null;
    }
  }
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Public-facing auth API calls that do NOT require a token
 * (login, register). Kept as plain functions to avoid
 * circular dependency with AuthProvider.
 */
export const authApi = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new ApiError(response.status, errorBody?.detail ?? 'Login failed');
    }

    return response.json();
  },

  async register(email: string, password: string, tenantName: string): Promise<TokenResponse> {
    const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, tenant_name: tenantName }),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new ApiError(response.status, errorBody?.detail ?? 'Registration failed');
    }

    return response.json();
  },
};
