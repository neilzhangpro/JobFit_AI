'use client';

// Base button component with variants (primary, secondary, ghost).
/**
 * Renders a native HTML button element and forwards any provided attributes.
 *
 * The component accepts React button attributes and renders them onto the underlying <button>.
 *
 * @param children - Content displayed inside the button
 * @param props - Additional HTML button attributes (e.g., `onClick`, `className`, `disabled`) that are spread onto the rendered element
 * @returns The rendered `<button>` element with forwarded attributes and children
 */

export function Button({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  // TODO: Implement button variants
  return <button {...props}>{children}</button>;
}
