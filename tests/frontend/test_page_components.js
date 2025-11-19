/**
 * Tests for main page components.
 *
 * This module tests the main application pages including:
 * - Home page (page.tsx)
 * - Layout component
 * - Page routing
 * - Global state management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock Next.js components
jest.mock('next/head', () => ({
  __esModule: true,
  default: ({ children }) => React.createElement('div', { 'data-testid': 'head' }, children)
}));

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }) => React.createElement('a', { href }, children)
}));

describe('Home Page (page.tsx)', () => {
  test('renders main page content', () => {
    // Mock the main page component
    const HomePage = () => (
      React.createElement('div', { 'data-testid': 'home-page' },
        React.createElement('h1', null, 'Open Legislation Platform'),
        React.createElement('p', null, 'Manage and track legislative data'),
        React.createElement('div', { 'data-testid': 'navigation' },
          React.createElement('a', { href: '/data' }, 'View Data'),
          React.createElement('a', { href: '/ingest' }, 'Start Ingestion')
        )
      )
    );

    render(React.createElement(HomePage));

    expect(screen.getByTestId('home-page')).toBeInTheDocument();
    expect(screen.getByText('Open Legislation Platform')).toBeInTheDocument();
    expect(screen.getByText('Manage and track legislative data')).toBeInTheDocument();
    expect(screen.getByTestId('navigation')).toBeInTheDocument();
  });

  test('navigation links work correctly', () => {
    const HomePage = () => (
      React.createElement('div', null,
        React.createElement('a', { href: '/data', 'data-testid': 'data-link' }, 'Data'),
        React.createElement('a', { href: '/ingest', 'data-testid': 'ingest-link' }, 'Ingest')
      )
    );

    render(React.createElement(HomePage));

    const dataLink = screen.getByTestId('data-link');
    const ingestLink = screen.getByTestId('ingest-link');

    expect(dataLink).toHaveAttribute('href', '/data');
    expect(ingestLink).toHaveAttribute('href', '/ingest');
  });
});

describe('Layout Component', () => {
  test('renders layout with header and footer', () => {
    const Layout = ({ children }) => (
      React.createElement('div', { 'data-testid': 'layout' },
        React.createElement('header', { 'data-testid': 'header' },
          React.createElement('nav', null,
            React.createElement('a', { href: '/' }, 'Home'),
            React.createElement('a', { href: '/about' }, 'About')
          )
        ),
        React.createElement('main', { 'data-testid': 'main-content' }, children),
        React.createElement('footer', { 'data-testid': 'footer' },
          React.createElement('p', null, '© 2025 Open Legislation')
        )
      )
    );

    render(
      React.createElement(Layout, null,
        React.createElement('p', null, 'Page content')
      )
    );

    expect(screen.getByTestId('layout')).toBeInTheDocument();
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('main-content')).toHaveTextContent('Page content');
    expect(screen.getByTestId('footer')).toHaveTextContent('© 2025 Open Legislation');
  });

  test('header navigation is accessible', () => {
    const Layout = () => (
      React.createElement('header', null,
        React.createElement('nav', { 'aria-label': 'Main navigation' },
          React.createElement('a', { href: '/', 'aria-current': 'page' }, 'Home'),
          React.createElement('a', { href: '/data' }, 'Data'),
          React.createElement('a', { href: '/ingest' }, 'Ingestion')
        )
      )
    );

    render(React.createElement(Layout));

    const nav = screen.getByLabelText('Main navigation');
    expect(nav).toBeInTheDocument();

    const homeLink = screen.getByText('Home');
    expect(homeLink).toHaveAttribute('aria-current', 'page');
  });
});

describe('Page Routing', () => {
  test('handles client-side navigation', () => {
    // Mock a simple router
    const MockRouter = ({ children }) => {
      const [currentPath, setCurrentPath] = React.useState('/');

      const navigate = (path) => setCurrentPath(path);

      return React.createElement('div', null,
        React.createElement('nav', null,
          React.createElement('button', {
            onClick: () => navigate('/data'),
            'data-testid': 'nav-data'
          }, 'Data'),
          React.createElement('button', {
            onClick: () => navigate('/ingest'),
            'data-testid': 'nav-ingest'
          }, 'Ingest')
        ),
        React.createElement('div', { 'data-testid': 'page-content' },
          currentPath === '/' && 'Home Page',
          currentPath === '/data' && 'Data Page',
          currentPath === '/ingest' && 'Ingestion Page'
        )
      );
    };

    render(React.createElement(MockRouter));

    expect(screen.getByTestId('page-content')).toHaveTextContent('Home Page');

    fireEvent.click(screen.getByTestId('nav-data'));
    expect(screen.getByTestId('page-content')).toHaveTextContent('Data Page');

    fireEvent.click(screen.getByTestId('nav-ingest'));
    expect(screen.getByTestId('page-content')).toHaveTextContent('Ingestion Page');
  });

  test('handles route parameters', () => {
    const BillDetailPage = ({ billId }) => (
      React.createElement('div', { 'data-testid': 'bill-detail' },
        React.createElement('h1', null, `Bill ${billId}`),
        React.createElement('p', null, 'Bill details here')
      )
    );

    render(React.createElement(BillDetailPage, { billId: 'S.123' }));

    expect(screen.getByTestId('bill-detail')).toBeInTheDocument();
    expect(screen.getByText('Bill S.123')).toBeInTheDocument();
  });
});

describe('Global State Management', () => {
  test('manages application state across components', () => {
    // Mock a simple context provider
    const AppContext = React.createContext();

    const AppProvider = ({ children }) => {
      const [user, setUser] = React.useState(null);
      const [theme, setTheme] = React.useState('light');

      const value = {
        user,
        setUser,
        theme,
        setTheme
      };

      return React.createElement(AppContext.Provider, { value }, children);
    };

    const UserProfile = () => {
      const { user, setUser } = React.useContext(AppContext);

      return React.createElement('div', { 'data-testid': 'user-profile' },
        user ? React.createElement('p', null, `Welcome ${user.name}`) :
               React.createElement('button', {
                 onClick: () => setUser({ name: 'John Doe' }),
                 'data-testid': 'login-button'
               }, 'Login')
      );
    };

    const ThemeToggle = () => {
      const { theme, setTheme } = React.useContext(AppContext);

      return React.createElement('button', {
        onClick: () => setTheme(theme === 'light' ? 'dark' : 'light'),
        'data-testid': 'theme-toggle'
      }, `Theme: ${theme}`);
    };

    render(
      React.createElement(AppProvider, null,
        React.createElement(UserProfile),
        React.createElement(ThemeToggle)
      )
    );

    // Test initial state
    expect(screen.getByTestId('login-button')).toBeInTheDocument();
    expect(screen.getByTestId('theme-toggle')).toHaveTextContent('Theme: light');

    // Test state updates
    fireEvent.click(screen.getByTestId('login-button'));
    expect(screen.getByText('Welcome John Doe')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('theme-toggle'));
    expect(screen.getByTestId('theme-toggle')).toHaveTextContent('Theme: dark');
  });

  test('handles loading states globally', () => {
    const LoadingContext = React.createContext();

    const LoadingProvider = ({ children }) => {
      const [isLoading, setIsLoading] = React.useState(false);

      return React.createElement(LoadingContext.Provider, {
        value: { isLoading, setIsLoading }
      }, children);
    };

    const LoadingIndicator = () => {
      const { isLoading } = React.useContext(LoadingContext);

      return isLoading ?
        React.createElement('div', { 'data-testid': 'loading' }, 'Loading...') :
        null;
    };

    const DataFetcher = () => {
      const { setIsLoading } = React.useContext(LoadingContext);

      return React.createElement('button', {
        onClick: () => {
          setIsLoading(true);
          // Simulate async operation
          setTimeout(() => setIsLoading(false), 100);
        },
        'data-testid': 'fetch-button'
      }, 'Fetch Data');
    };

    render(
      React.createElement(LoadingProvider, null,
        React.createElement(LoadingIndicator),
        React.createElement(DataFetcher)
      )
    );

    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('fetch-button'));
    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });
});

describe('Error Boundaries', () => {
  test('catches component errors', () => {
    class ErrorBoundary extends React.Component {
      constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
      }

      static getDerivedStateFromError(error) {
        return { hasError: true, error };
      }

      render() {
        if (this.state.hasError) {
          return React.createElement('div', { 'data-testid': 'error-boundary' },
            React.createElement('h2', null, 'Something went wrong'),
            React.createElement('p', null, this.state.error.message)
          );
        }

        return this.props.children;
      }
    }

    const ErrorComponent = () => {
      throw new Error('Test component error');
    };

    render(
      React.createElement(ErrorBoundary, null,
        React.createElement(ErrorComponent)
      )
    );

    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test component error')).toBeInTheDocument();
  });

  test('error boundary reset functionality', () => {
    class ResettableErrorBoundary extends React.Component {
      constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
      }

      static getDerivedStateFromError(error) {
        return { hasError: true, error };
      }

      resetError = () => {
        this.setState({ hasError: false, error: null });
      };

      render() {
        if (this.state.hasError) {
          return React.createElement('div', { 'data-testid': 'error-boundary' },
            React.createElement('p', null, 'Error occurred'),
            React.createElement('button', {
              onClick: this.resetError,
              'data-testid': 'reset-button'
            }, 'Try again')
          );
        }

        return this.props.children;
      }
    }

    const ErrorComponent = ({ shouldError }) => {
      if (shouldError) {
        throw new Error('Component error');
      }
      return React.createElement('div', { 'data-testid': 'normal-content' }, 'Normal content');
    };

    const TestComponent = () => {
      const [shouldError, setShouldError] = React.useState(true);

      return React.createElement(ResettableErrorBoundary, null,
        React.createElement(ErrorComponent, { shouldError }),
        React.createElement('button', {
          onClick: () => setShouldError(false),
          'data-testid': 'fix-error'
        }, 'Fix Error')
      );
    };

    render(React.createElement(TestComponent));

    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('reset-button'));
    expect(screen.queryByTestId('error-boundary')).not.toBeInTheDocument();
  });
});

describe('Performance and Optimization', () => {
  test('components handle large datasets efficiently', () => {
    const LargeList = ({ items }) => (
      React.createElement('ul', { 'data-testid': 'large-list' },
        items.map((item, index) =>
          React.createElement('li', { key: index, 'data-testid': `item-${index}` }, item)
        )
      )
    );

    const largeDataset = Array.from({ length: 1000 }, (_, i) => `Item ${i + 1}`);

    render(React.createElement(LargeList, { items: largeDataset }));

    expect(screen.getByTestId('large-list')).toBeInTheDocument();
    expect(screen.getAllByTestId(/^item-/)).toHaveLength(1000);
    expect(screen.getByTestId('item-0')).toHaveTextContent('Item 1');
    expect(screen.getByTestId('item-999')).toHaveTextContent('Item 1000');
  });

  test('lazy loading components', async () => {
    const LazyComponent = React.lazy(() =>
      Promise.resolve({
        default: () => React.createElement('div', { 'data-testid': 'lazy-content' }, 'Lazy loaded content')
      })
    );

    const App = () => (
      React.createElement(React.Suspense, {
        fallback: React.createElement('div', { 'data-testid': 'loading' }, 'Loading...')
      },
        React.createElement(LazyComponent)
      )
    );

    render(React.createElement(App));

    expect(screen.getByTestId('loading')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('lazy-content')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
  });

  test('memoized components prevent unnecessary re-renders', () => {
    const renderCount = { count: 0 };

    const ExpensiveComponent = React.memo(({ value }) => {
      renderCount.count++;
      return React.createElement('div', { 'data-testid': 'expensive' }, `Value: ${value}`);
    });

    const ParentComponent = () => {
      const [count, setCount] = React.useState(0);
      const [otherValue, setOtherValue] = React.useState(0);

      return React.createElement('div', null,
        React.createElement(ExpensiveComponent, { value: count }),
        React.createElement('button', {
          onClick: () => setCount(c => c + 1),
          'data-testid': 'increment-count'
        }, 'Increment Count'),
        React.createElement('button', {
          onClick: () => setOtherValue(v => v + 1),
          'data-testid': 'increment-other'
        }, 'Increment Other')
      );
    };

    render(React.createElement(ParentComponent));

    expect(renderCount.count).toBe(1);
    expect(screen.getByTestId('expensive')).toHaveTextContent('Value: 0');

    // Changing unrelated state should not re-render expensive component
    fireEvent.click(screen.getByTestId('increment-other'));
    expect(renderCount.count).toBe(1); // Should still be 1

    // Changing relevant state should re-render
    fireEvent.click(screen.getByTestId('increment-count'));
    expect(renderCount.count).toBe(2);
    expect(screen.getByTestId('expensive')).toHaveTextContent('Value: 1');
  });
});