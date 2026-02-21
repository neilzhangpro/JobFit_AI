/**
 * Unit tests for ApiClient — JWT injection, 401 refresh, error handling.
 */

import { ApiClient, ApiError, authApi } from '@/lib/api/client';
import type { TokenResponse } from '@/types/auth';

const MOCK_TOKENS: TokenResponse = {
  access_token: 'new-access',
  refresh_token: 'new-refresh',
  token_type: 'bearer',
  expires_in: 3600,
};

/** Minimal Response-like mock for jsdom where native Response is absent. */
function mockResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(body),
    headers: new Map([['Content-Type', 'application/json']]),
  };
}

const fetchMock = jest.fn() as jest.Mock;

beforeAll(() => {
  globalThis.fetch = fetchMock;
});

describe('ApiClient', () => {
  let client: ApiClient;
  let onTokenRefreshed: jest.Mock;
  let onAuthFailure: jest.Mock;
  let getAccessToken: jest.Mock;
  let getRefreshToken: jest.Mock;

  beforeEach(() => {
    fetchMock.mockReset();
    onTokenRefreshed = jest.fn();
    onAuthFailure = jest.fn();
    getAccessToken = jest.fn().mockReturnValue('access-123');
    getRefreshToken = jest.fn().mockReturnValue('refresh-456');

    client = new ApiClient({
      getAccessToken,
      getRefreshToken,
      onTokenRefreshed,
      onAuthFailure,
    });
  });

  it('injects Authorization header with access token', async () => {
    fetchMock.mockResolvedValue(mockResponse({ ok: true }));

    await client.get('/api/test');

    const [, init] = fetchMock.mock.calls[0];
    const headers = init?.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer access-123');
  });

  it('retries with refreshed token on 401', async () => {
    fetchMock
      .mockResolvedValueOnce(mockResponse({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(mockResponse(MOCK_TOKENS))
      .mockResolvedValueOnce(mockResponse({ id: 1 }));

    const result = await client.get<{ id: number }>('/api/data');

    expect(result).toEqual({ id: 1 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(onTokenRefreshed).toHaveBeenCalledWith(MOCK_TOKENS);
  });

  it('calls onAuthFailure when refresh fails', async () => {
    fetchMock
      .mockResolvedValueOnce(mockResponse({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(mockResponse({ detail: 'invalid' }, 401));

    await expect(client.get('/api/data')).rejects.toThrow(ApiError);
    expect(onAuthFailure).toHaveBeenCalled();
  });

  it('throws ApiError with status and message for non-ok responses', async () => {
    fetchMock.mockResolvedValue(mockResponse({ detail: 'Not found' }, 404));
    getRefreshToken.mockReturnValue(null);

    await expect(client.get('/api/missing')).rejects.toMatchObject({
      status: 404,
      message: 'Not found',
    });
  });

  it('sends POST body as JSON', async () => {
    fetchMock.mockResolvedValue(mockResponse({ created: true }));

    await client.post('/api/items', { name: 'test' });

    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe('POST');
    expect(init?.body).toBe(JSON.stringify({ name: 'test' }));
  });
});

describe('authApi', () => {
  beforeEach(() => fetchMock.mockReset());

  it('login sends correct payload and returns tokens', async () => {
    fetchMock.mockResolvedValue(mockResponse(MOCK_TOKENS));

    const result = await authApi.login('a@b.com', 'password123');

    expect(result).toEqual(MOCK_TOKENS);
    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(body).toEqual({ email: 'a@b.com', password: 'password123' });
  });

  it('login throws ApiError on failure', async () => {
    fetchMock.mockResolvedValue(mockResponse({ detail: 'Invalid credentials' }, 401));

    await expect(authApi.login('a@b.com', 'wrong')).rejects.toThrow('Invalid credentials');
  });

  it('register sends tenant_name in snake_case', async () => {
    fetchMock.mockResolvedValue(mockResponse(MOCK_TOKENS, 201));

    await authApi.register('a@b.com', 'password123', 'My Org');

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(body).toEqual({
      email: 'a@b.com',
      password: 'password123',
      tenant_name: 'My Org',
    });
  });
});
