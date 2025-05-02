import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import Login from './Login';

// Mock the auth context
const mockLogin = jest.fn();
const mockContextValue = {
  login: mockLogin,
  loading: false,
  isAuthenticated: false,
  authError: null
};

// Mock navigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: { from: { pathname: '/app' } } })
}));

describe('Login Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form correctly', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockContextValue}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/create a new account/i)).toBeInTheDocument();
    expect(screen.getByText(/Forgot your password/i)).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockContextValue}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    // Submit without filling fields
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    fireEvent.click(submitButton);

    // Check for validation messages
    await waitFor(() => {
      expect(screen.getByText(/Username is required/i)).toBeInTheDocument();
    });
  });

  test('calls login function and navigates on successful submission', async () => {
    // Mock successful login
    mockLogin.mockResolvedValueOnce({});

    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockContextValue}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    // Fill the form
    const usernameInput = screen.getByLabelText(/Username/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    fireEvent.click(submitButton);

    // Verify login was called with correct credentials
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
        remember: false
      });
      expect(mockNavigate).toHaveBeenCalledWith('/app', { replace: true });
    });
  });

  test('displays error message on login failure', async () => {
    // Mock failed login
    const errorMessage = 'Invalid username or password';
    mockLogin.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockContextValue}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    // Fill the form
    const usernameInput = screen.getByLabelText(/Username/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    fireEvent.click(submitButton);

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('renders loading spinner when loading', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ ...mockContextValue, loading: true }}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeDisabled();
  });
});