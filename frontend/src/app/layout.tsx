/**
 * Root layout — wraps the entire application.
 * Imports global Tailwind CSS and sets HTML metadata.
 */

import type { Metadata } from 'next';

import { AuthProvider } from '@/providers/AuthProvider';
import './globals.css';

export const metadata: Metadata = {
  title: 'JobFit AI',
  description: 'Intelligent Resume Optimization Agent',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
