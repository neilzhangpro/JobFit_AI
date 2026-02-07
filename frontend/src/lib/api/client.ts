/**
 * API client factory (Factory pattern).
 * Creates configured fetch/axios instances with JWT token injection.
 */
export function createApiClient(baseUrl: string) {
  // TODO: Create configured API client
  return {
    get: async (url: string) => ({}),
    post: async (url: string, data: unknown) => ({}),
  };
}
