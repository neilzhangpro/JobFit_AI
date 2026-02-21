/**
 * Integration tests for LoginPage — form validation, submission, error display.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import LoginPage from '@/app/(auth)/login/page';
import { AuthContext } from '@/providers/AuthProvider';
import { ApiError } from '@/lib/api/client';

function renderWithAuth(loginMock = jest.fn()) {
  const value = {
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
    login: loginMock,
    register: jest.fn(),
    logout: jest.fn(),
    apiClient: {} as never,
  };

  return render(
    <AuthContext.Provider value={value}>
      <LoginPage />
    </AuthContext.Provider>,
  );
}

// next/navigation mock
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

describe('LoginPage', () => {
  it('renders email and password fields', () => {
    renderWithAuth();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('shows validation errors for empty submission', async () => {
    renderWithAuth();
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
  });

  it('shows invalid email error', async () => {
    renderWithAuth();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/email/i), 'not-an-email');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText('Invalid email address')).toBeInTheDocument();
  });

  it('calls login with correct credentials', async () => {
    const loginMock = jest.fn();
    renderWithAuth(loginMock);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('displays API error message on login failure', async () => {
    const loginMock = jest.fn().mockRejectedValue(new ApiError(401, 'Invalid credentials'));
    renderWithAuth(loginMock);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
  });

  it('has a link to register page', () => {
    renderWithAuth();
    const link = screen.getByRole('link', { name: /create one/i });
    expect(link).toHaveAttribute('href', '/register');
  });
});
