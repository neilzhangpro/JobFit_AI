'use client';

import React, { createContext } from 'react';

/**
 * React Context provider for current tenant information.
 */
export const TenantContext = createContext(null);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  // TODO: Implement tenant provider logic
  return <TenantContext.Provider value={null}>{children}</TenantContext.Provider>;
}
