"use client";

import React, { createContext } from "react";

/**
 * React Context provider for theme/dark mode.
 */
export const ThemeContext = createContext(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // TODO: Implement theme provider logic
  return <ThemeContext.Provider value={null}>{children}</ThemeContext.Provider>;
}
