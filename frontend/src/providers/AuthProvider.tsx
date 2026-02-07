"use client";

import React, { createContext } from "react";

/**
 * React Context provider for JWT authentication state.
 * Manages access token in memory, refresh token in httpOnly cookie.
 */
export const AuthContext = createContext(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // TODO: Implement auth provider logic
  return <AuthContext.Provider value={null}>{children}</AuthContext.Provider>;
}
