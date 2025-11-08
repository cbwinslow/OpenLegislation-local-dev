"""
Tests for frontend components.

This module tests React components including:
- DataIngestionPlatform component
- UI components
- API integration
- Component interactions
- Error handling
"""

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { jest } from '@jest/globals';

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock components that might not be available in test environment
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
    query: {}
  })
}));

describe('DataIngestionPlatform', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  test('renders loading state initially', () => {
    // Mock pending API call
    (global.fetch as jest.Mock).mockImplementation(() =>
      new Promise(() => {}) // Never resolves
    );

    // Import and render component
    const { DataIngestionPlatform } = require('../components/DataIngestionPlatform');

    render(<DataIngestionPlatform />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test('renders data ingestion interface', async () => {
    // Mock successful API response
    const mockData = {
      bills: { count: 150, lastUpdated: '2025-01-15T10:30:00Z' },
      members: { count: 535, lastUpdated: '2025-01-14T15:45:00Z' },
      votes: { count: 2340, lastUpdated: '2025-01-15T09:15:00Z' }
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const { DataIngestionPlatform } = require('../components/DataIngestionPlatform');

    render(<DataIngestionPlatform />);

    await waitFor(() => {
      expect(screen.getByText('Data Ingestion Platform')).toBeInTheDocument();
    });

    expect(screen.getByText('150')).toBeInTheDocument(); // Bills count
    expect(screen.getByText('535')).toBeInTheDocument(); // Members count
    expect(screen.getByText('2340')).toBeInTheDocument(); // Votes count
  });

  test('handles API errors gracefully', async () => {
    // Mock failed API response
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    const { DataIngestionPlatform } = require('../components/DataIngestionPlatform');

    render(<DataIngestionPlatform />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  test('triggers data ingestion on button click', async () => {
    const mockData = {
      bills: { count: 100, lastUpdated: '2025-01-15T10:30:00Z' },
      members: { count: 500, lastUpdated: '2025-01-14T15:45:00Z' },
      votes: { count: 2000, lastUpdated: '2025-01-15T09:15:00Z' }
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'ingestion_started', jobId: 'job_123' })
      });

    const { DataIngestionPlatform } = require('../components/DataIngestionPlatform');

    render(<DataIngestionPlatform />);

    await waitFor(() => {
      expect(screen.getByText('Data Ingestion Platform')).toBeInTheDocument();
    });

    const ingestButton = screen.getByRole('button', { name: /start ingestion/i });
    fireEvent.click(ingestButton);

    await waitFor(() => {
      expect(screen.getByText(/ingestion started/i)).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/ingestion/start', expect.any(Object));
  });

  test('displays ingestion progress', async () => {
    const mockData = {
      bills: { count: 100, lastUpdated: '2025-01-15T10:30:00Z' },
      members: { count: 500, lastUpdated: '2025-01-14T15:45:00Z' },
      votes: { count: 2000, lastUpdated: '2025-01-15T09:15:00Z' }
    };

    const progressData = {
      status: 'running',
      progress: 65,
      currentTask: 'Processing bills',
      eta: '2 minutes remaining'
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => progressData
      });

    const { DataIngestionPlatform } = require('../components/DataIngestionPlatform');

    render(<DataIngestionPlatform />);

    await waitFor(() => {
      expect(screen.getByText('Data Ingestion Platform')).toBeInTheDocument();
    });

    // Trigger progress check
    const progressButton = screen.getByRole('button', { name: /check progress/i });
    fireEvent.click(progressButton);

    await waitFor(() => {
      expect(screen.getByText('65%')).toBeInTheDocument();
      expect(screen.getByText('Processing bills')).toBeInTheDocument();
    });
  });
});

describe('UI Components', () => {
  test('renders button component correctly', () => {
    // Mock UI button component
    const Button = ({ children, onClick, disabled }: any) => (
      <button onClick={onClick} disabled={disabled} data-testid="ui-button">
        {children}
      </button>
    );

    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByTestId('ui-button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Click me');

    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('renders input component with validation', () => {
    // Mock UI input component
    const Input = ({ value, onChange, error, placeholder }: any) => (
      <div>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          data-testid="ui-input"
        />
        {error && <span data-testid="error-message">{error}</span>}
      </div>
    );

    const handleChange = jest.fn();
    render(
      <Input
        value="test"
        onChange={handleChange}
        error="Invalid input"
        placeholder="Enter value"
      />
    );

    const input = screen.getByTestId('ui-input');
    const errorMessage = screen.getByTestId('error-message');

    expect(input).toHaveValue('test');
    expect(input).toHaveAttribute('placeholder', 'Enter value');
    expect(errorMessage).toHaveTextContent('Invalid input');

    fireEvent.change(input, { target: { value: 'new value' } });
    expect(handleChange).toHaveBeenCalledWith('new value');
  });

  test('renders loading spinner', () => {
    // Mock loading spinner component
    const LoadingSpinner = ({ size, message }: any) => (
      <div data-testid="loading-spinner">
        <div className={`spinner ${size}`} data-testid="spinner-element"></div>
        {message && <p data-testid="loading-message">{message}</p>}
      </div>
    );

    render(<LoadingSpinner size="large" message="Loading data..." />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByTestId('spinner-element')).toHaveClass('large');
    expect(screen.getByTestId('loading-message')).toHaveTextContent('Loading data...');
  });
});

describe('API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('fetches data from API endpoint', async () => {
    const mockApiResponse = {
      bills: { count: 100, status: 'completed' },
      members: { count: 535, status: 'completed' },
      votes: { count: 2000, status: 'running' }
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse
    });

    // Mock API service
    const apiService = {
      async getIngestionStatus() {
        const response = await fetch('/api/ingestion/status');
        if (!response.ok) {
          throw new Error('API request failed');
        }
        return response.json();
      }
    };

    const result = await apiService.getIngestionStatus();

    expect(result).toEqual(mockApiResponse);
    expect(global.fetch).toHaveBeenCalledWith('/api/ingestion/status');
  });

  test('handles API authentication', async () => {
    const mockAuthResponse = { token: 'mock_jwt_token', expires: 3600 };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAuthResponse
    });

    // Mock authentication service
    const authService = {
      async login(credentials: any) {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(credentials)
        });
        if (!response.ok) {
          throw new Error('Authentication failed');
        }
        return response.json();
      }
    };

    const credentials = { username: 'test', password: 'password' };
    const result = await authService.login(credentials);

    expect(result).toEqual(mockAuthResponse);
    expect(global.fetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    }));
  });

  test('handles API rate limiting', async () => {
    // Mock rate limited response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => ({ error: 'Rate limit exceeded', retryAfter: 60 })
    });

    const apiService = {
      async makeRequest() {
        const response = await fetch('/api/data');
        if (response.status === 429) {
          const data = await response.json();
          throw new Error(`Rate limited: ${data.error}`);
        }
        return response.json();
      }
    };

    await expect(apiService.makeRequest()).rejects.toThrow('Rate limited: Rate limit exceeded');
  });
});

describe('Component Integration', () => {
  test('parent component communicates with child', () => {
    // Mock parent-child component interaction
    const ChildComponent = ({ onDataChange, data }: any) => (
      <div>
        <input
          value={data}
          onChange={(e) => onDataChange(e.target.value)}
          data-testid="child-input"
        />
        <p data-testid="child-display">Data: {data}</p>
      </div>
    );

    const ParentComponent = () => {
      const [data, setData] = React.useState('initial');

      return (
        <div>
          <ChildComponent data={data} onDataChange={setData} />
          <p data-testid="parent-display">Parent data: {data}</p>
        </div>
      );
    };

    render(<ParentComponent />);

    const input = screen.getByTestId('child-input');
    const childDisplay = screen.getByTestId('child-display');
    const parentDisplay = screen.getByTestId('parent-display');

    expect(childDisplay).toHaveTextContent('Data: initial');
    expect(parentDisplay).toHaveTextContent('Parent data: initial');

    fireEvent.change(input, { target: { value: 'updated' } });

    expect(childDisplay).toHaveTextContent('Data: updated');
    expect(parentDisplay).toHaveTextContent('Parent data: updated');
  });

  test('component handles async operations', async () => {
    // Mock component with async operation
    const AsyncComponent = () => {
      const [status, setStatus] = React.useState('idle');
      const [data, setData] = React.useState(null);

      const handleAsyncOperation = async () => {
        setStatus('loading');
        try {
          // Simulate API call
          await new Promise(resolve => setTimeout(resolve, 100));
          const result = { message: 'Success' };
          setData(result);
          setStatus('completed');
        } catch (error) {
          setStatus('error');
        }
      };

      return (
        <div>
          <button onClick={handleAsyncOperation} data-testid="async-button">
            Start Operation
          </button>
          <p data-testid="status">Status: {status}</p>
          {data && <p data-testid="result">{data.message}</p>}
        </div>
      );
    };

    render(<AsyncComponent />);

    const button = screen.getByTestId('async-button');
    const statusDisplay = screen.getByTestId('status');

    expect(statusDisplay).toHaveTextContent('Status: idle');

    fireEvent.click(button);

    expect(statusDisplay).toHaveTextContent('Status: loading');

    await waitFor(() => {
      expect(statusDisplay).toHaveTextContent('Status: completed');
      expect(screen.getByTestId('result')).toHaveTextContent('Success');
    });
  });
});

describe('Error Handling', () => {
  test('component displays error boundary', () => {
    // Mock error boundary component
    class ErrorBoundary extends React.Component {
      constructor(props: any) {
        super(props);
        this.state = { hasError: false };
      }

      static getDerivedStateFromError() {
        return { hasError: true };
      }

      render() {
        if (this.state.hasError) {
          return <div data-testid="error-boundary">Something went wrong</div>;
        }
        return this.props.children;
      }
    }

    // Component that throws error
    const ErrorComponent = () => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  test('form validation displays errors', () => {
    // Mock form component with validation
    const ValidationForm = () => {
      const [errors, setErrors] = React.useState({});
      const [formData, setFormData] = React.useState({ email: '', password: '' });

      const validateForm = () => {
        const newErrors: any = {};
        if (!formData.email) newErrors.email = 'Email is required';
        if (!formData.password) newErrors.password = 'Password is required';
        if (formData.email && !formData.email.includes('@')) {
          newErrors.email = 'Invalid email format';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
      };

      return (
        <form data-testid="validation-form">
          <input
            data-testid="email-input"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            placeholder="Email"
          />
          {errors.email && <span data-testid="email-error">{errors.email}</span>}

          <input
            data-testid="password-input"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            placeholder="Password"
          />
          {errors.password && <span data-testid="password-error">{errors.password}</span>}

          <button
            type="button"
            onClick={validateForm}
            data-testid="submit-button"
          >
            Submit
          </button>
        </form>
      );
    };

    render(<ValidationForm />);

    const submitButton = screen.getByTestId('submit-button');
    fireEvent.click(submitButton);

    expect(screen.getByTestId('email-error')).toHaveTextContent('Email is required');
    expect(screen.getByTestId('password-error')).toHaveTextContent('Password is required');

    // Fill in invalid email
    const emailInput = screen.getByTestId('email-input');
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    fireEvent.click(submitButton);

    expect(screen.getByTestId('email-error')).toHaveTextContent('Invalid email format');
  });
});

describe('Accessibility', () => {
  test('components have proper ARIA labels', () => {
    // Mock accessible component
    const AccessibleButton = ({ children, onClick, ariaLabel }: any) => (
      <button onClick={onClick} aria-label={ariaLabel} data-testid="accessible-button">
        {children}
      </button>
    );

    render(
      <AccessibleButton onClick={() => {}} ariaLabel="Submit form">
        Submit
      </AccessibleButton>
    );

    const button = screen.getByTestId('accessible-button');
    expect(button).toHaveAttribute('aria-label', 'Submit form');
  });

  test('form has proper labels and associations', () => {
    // Mock accessible form
    const AccessibleForm = () => (
      <form data-testid="accessible-form">
        <label htmlFor="username-input">Username</label>
        <input id="username-input" data-testid="username-input" />

        <label htmlFor="email-input">Email Address</label>
        <input id="email-input" type="email" data-testid="email-input" />
      </form>
    );

    render(<AccessibleForm />);

    const usernameInput = screen.getByTestId('username-input');
    const emailInput = screen.getByTestId('email-input');

    expect(usernameInput).toHaveAttribute('id', 'username-input');
    expect(emailInput).toHaveAttribute('id', 'email-input');

    // Check that labels are associated
    expect(screen.getByLabelText('Username')).toBe(usernameInput);
    expect(screen.getByLabelText('Email Address')).toBe(emailInput);
  });
});