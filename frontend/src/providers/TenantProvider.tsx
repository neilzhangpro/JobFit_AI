"use client";

import React, { createContext } from "react";

/**
 * React Context provider for current tenant information.
 */
export const TenantContext = createContext(null);

/**
 * Provides TenantContext to descendant components.
 *
 * Renders a TenantContext.Provider that supplies `null` as the current tenant value and mounts the given children.
 *
 * @param children - Elements to render inside the provider
 * @returns The provider element wrapping `children`
 */
export function TenantProvider({ children }: { children: React.ReactNode }) {
  // TODO: Implement tenant provider logic
  return (
    <TenantContext.Provider value={null}>{children}</TenantContext.Provider>
  );
}