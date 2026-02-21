/**
 * Auth types matching backend identity DTOs.
 *
 * Backend uses snake_case; these mirror the JSON wire format exactly
 * so no field-name transformation is needed.
 */

export interface User {
  id: string;
  email: string;
  role: string;
  tenant_id: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  tenant_name: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
