"use client";

// Base button component with variants (primary, secondary, ghost).
// TODO: Implement button variants

export function Button({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  // TODO: Implement button variants
  return <button {...props}>{children}</button>;
}
