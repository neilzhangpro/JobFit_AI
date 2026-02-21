'use client';

import { useContext } from 'react';

import { AuthContext } from '@/providers/AuthProvider';

/**
 * Typed consumer for AuthContext. Throws if used outside AuthProvider
 * so call-sites never have to null-check.
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
