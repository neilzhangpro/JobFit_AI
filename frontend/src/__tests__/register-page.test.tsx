/**
 * Integration tests for RegisterPage — form validation, submission, error display.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import RegisterPage from '@/app/(auth)/register/page';
import { AuthContext } from '@/providers/AuthProvider';
import { ApiError } from '@/lib/api/client';

function renderWithAuth(registerMock = jest.fn()) {
  const value = {
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
    login: jest.fn(),
    register: registerMock,
    logout: jest.fn(),
    apiClient: {} as never,
  };

  return render(
    <AuthContext.Provider value={value}>
      <RegisterPage />
    </AuthContext.Provider>,
  );
}

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

describe('RegisterPage', () => {
  it('renders all form fields', () => {
    renderWithAuth();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization name/i)).toBeInTheDocument();
  });

  it('shows validation errors for empty submission', async () => {
    renderWithAuth();
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(screen.getByText('Organization name is required')).toBeInTheDocument();
  });

  it('shows password length error', async () => {
    renderWithAuth();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email$/i), 'a@b.com');
    await user.type(screen.getByLabelText(/^password$/i), 'short');
    await user.type(screen.getByLabelText(/confirm password/i), 'short');
    await user.type(screen.getByLabelText(/organization name/i), 'Org');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Password must be at least 8 characters')).toBeInTheDocument();
  });

  it('shows password mismatch error', async () => {
    renderWithAuth();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email$/i), 'a@b.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'different123');
    await user.type(screen.getByLabelText(/organization name/i), 'Org');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument();
  });

  it('calls register with correct data', async () => {
    const registerMock = jest.fn();
    renderWithAuth(registerMock);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email$/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByLabelText(/organization name/i), 'My Org');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith('test@example.com', 'password123', 'My Org');
    });
  });

  it('displays API error on registration failure', async () => {
    const registerMock = jest
      .fn()
      .mockRejectedValue(new ApiError(400, 'Email already registered'));
    renderWithAuth(registerMock);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email$/i), 'dup@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByLabelText(/organization name/i), 'Org');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Email already registered')).toBeInTheDocument();
  });

  it('has a link to login page', () => {
    renderWithAuth();
    const link = screen.getByRole('link', { name: /sign in/i });
    expect(link).toHaveAttribute('href', '/login');
  });
});
