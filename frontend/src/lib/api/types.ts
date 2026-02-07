/**
 * Shared API response types.
 * ApiResponse envelope type and error types.
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: {
    code: string;
    message: string;
  } | null;
  meta: {
    request_id: string;
    timestamp: string;
  };
}
