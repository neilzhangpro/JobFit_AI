// Dashboard layout with sidebar navigation. Requires authentication.
/**
 * Wraps dashboard pages and renders provided content within the dashboard layout.
 *
 * @param children - The content to render inside the dashboard layout (page body).
 * @returns A React element that renders `children` inside the dashboard layout container.
 */

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // TODO: Add sidebar + header
  return <div>{children}</div>;
}