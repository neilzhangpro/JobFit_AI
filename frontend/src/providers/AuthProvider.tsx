'use client';

import React, { createContext, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

import { ApiClient } from '@/lib/api/client';
import { authApi } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { AuthState, TokenResponse, User } from '@/types/auth';

const TOKEN_KEY = 'jobfit_refresh_token';

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, tenantName: string) => Promise<void>;
  logout: () => void;
  apiClient: ApiClient;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const accessTokenRef = useRef<string | null>(null);
  const refreshTokenRef = useRef<string | null>(null);

  const clearAuth = useCallback(() => {
    accessTokenRef.current = null;
    refreshTokenRef.current = null;
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  const handleLogout = useCallback(() => {
    clearAuth();
    router.push('/login');
  }, [clearAuth, router]);

  const applyTokens = useCallback((tokens: TokenResponse) => {
    accessTokenRef.current = tokens.access_token;
    refreshTokenRef.current = tokens.refresh_token;
    localStorage.setItem(TOKEN_KEY, tokens.refresh_token);
  }, []);

  const apiClient = useMemo(
    () =>
      new ApiClient({
        getAccessToken: () => accessTokenRef.current,
        getRefreshToken: () => refreshTokenRef.current,
        onTokenRefreshed: (tokens) => applyTokens(tokens),
        onAuthFailure: () => handleLogout(),
      }),
    [applyTokens, handleLogout],
  );

  const fetchUser = useCallback(async (): Promise<User | null> => {
    try {
      return await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    } catch {
      return null;
    }
  }, [apiClient]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await authApi.login(email, password);
      applyTokens(tokens);
      const me = await fetchUser();
      setUser(me);
      router.push('/optimize');
    },
    [applyTokens, fetchUser, router],
  );

  const register = useCallback(
    async (email: string, password: string, tenantName: string) => {
      const tokens = await authApi.register(email, password, tenantName);
      applyTokens(tokens);
      const me = await fetchUser();
      setUser(me);
      router.push('/optimize');
    },
    [applyTokens, fetchUser, router],
  );

  // Restore session from stored refresh token on mount
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setIsLoading(false);
      return;
    }

    refreshTokenRef.current = stored;

    (async () => {
      try {
        const response = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: stored }),
        });

        if (!response.ok) {
          clearAuth();
          setIsLoading(false);
          return;
        }

        const tokens: TokenResponse = await response.json();
        applyTokens(tokens);
        const me = await fetchUser();
        setUser(me);
      } catch {
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken: accessTokenRef.current,
      refreshToken: refreshTokenRef.current,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout: handleLogout,
      apiClient,
    }),
    [user, isLoading, login, register, handleLogout, apiClient],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
