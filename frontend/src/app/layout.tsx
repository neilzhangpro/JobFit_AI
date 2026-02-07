/**
 * Root layout — wraps the entire application.
 * Imports global Tailwind CSS and sets HTML metadata.
 */

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobFit AI",
  description: "Intelligent Resume Optimization Agent",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // TODO: Wrap with AuthProvider, TenantProvider, ThemeProvider
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
