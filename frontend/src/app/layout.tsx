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

/**
 * Root layout component that provides the top-level HTML structure for all pages.
 *
 * @param children - The content to render inside the document body.
 * @returns The root `<html>` element containing a `<body>` with the given `children`.
 */
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