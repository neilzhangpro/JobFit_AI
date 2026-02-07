/**
 * TypeScript types for authentication: User, Tenant, LoginRequest, RegisterRequest, TokenResponse.
 */

export interface User {
  // TODO: Define user properties
  id: string;
  email: string;
}

export interface Tenant {
  // TODO: Define tenant properties
  id: string;
  name: string;
}

export interface LoginRequest {
  // TODO: Define login request properties
  email: string;
  password: string;
}

export interface RegisterRequest {
  // TODO: Define register request properties
  email: string;
  password: string;
  tenantName?: string;
}

export interface TokenResponse {
  // TODO: Define token response properties
  accessToken: string;
  refreshToken?: string;
}
