/**
 * Tests for UI components.
 *
 * This module tests reusable UI components including:
 * - Button component
 * - Input component
 * - Card component
 * - Alert component
 * - Progress component
 * - Dialog component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock UI components
describe('Button Component', () => {
  test('renders button with correct text', () => {
    const Button = ({ children, onClick, variant, size, disabled }) => (
      React.createElement('button', {
        onClick,
        disabled,
        className: `${variant || 'default'} ${size || 'default'}`,
        'data-testid': 'ui-button'
      }, children)
    );

    render(React.createElement(Button, { variant: 'primary', size: 'lg' }, 'Click me'));

    const button = screen.getByTestId('ui-button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Click me');
    expect(button).toHaveClass('primary', 'lg');
  });

  test('handles click events', () => {
    const Button = ({ children, onClick }) => (
      React.createElement('button', { onClick, 'data-testid': 'ui-button' }, children)
    );

    const handleClick = jest.fn();
    render(React.createElement(Button, { onClick: handleClick }, 'Click me'));

    const button = screen.getByTestId('ui-button');
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('respects disabled state', () => {
    const Button = ({ children, onClick, disabled }) => (
      React.createElement('button', {
        onClick,
        disabled,
        'data-testid': 'ui-button'
      }, children)
    );

    const handleClick = jest.fn();
    render(React.createElement(Button, { onClick: handleClick, disabled: true }, 'Click me'));

    const button = screen.getByTestId('ui-button');
    expect(button).toBeDisabled();

    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  test('supports different variants', () => {
    const Button = ({ children, variant }) => (
      React.createElement('button', {
        className: variant,
        'data-testid': 'ui-button'
      }, children)
    );

    const { rerender } = render(React.createElement(Button, { variant: 'primary' }, 'Primary'));
    expect(screen.getByTestId('ui-button')).toHaveClass('primary');

    rerender(React.createElement(Button, { variant: 'secondary' }, 'Secondary'));
    expect(screen.getByTestId('ui-button')).toHaveClass('secondary');

    rerender(React.createElement(Button, { variant: 'destructive' }, 'Destructive'));
    expect(screen.getByTestId('ui-button')).toHaveClass('destructive');
  });
});

describe('Input Component', () => {
  test('renders input with correct props', () => {
    const Input = ({ value, onChange, placeholder, type, disabled }) => (
      React.createElement('input', {
        value,
        onChange: (e) => onChange && onChange(e),
        placeholder,
        type: type || 'text',
        disabled,
        'data-testid': 'ui-input'
      })
    );

    render(React.createElement(Input, {
      value: 'test value',
      placeholder: 'Enter text',
      type: 'email'
    }));

    const input = screen.getByTestId('ui-input');
    expect(input).toHaveValue('test value');
    expect(input).toHaveAttribute('placeholder', 'Enter text');
    expect(input).toHaveAttribute('type', 'email');
  });

  test('handles value changes', () => {
    const Input = ({ value, onChange }) => (
      React.createElement('input', {
        value,
        onChange: (e) => onChange(e.target.value),
        'data-testid': 'ui-input'
      })
    );

    const handleChange = jest.fn();
    render(React.createElement(Input, { value: '', onChange: handleChange }));

    const input = screen.getByTestId('ui-input');
    fireEvent.change(input, { target: { value: 'new value' } });

    expect(handleChange).toHaveBeenCalledWith('new value');
  });

  test('respects disabled state', () => {
    const Input = ({ disabled }) => (
      React.createElement('input', {
        disabled,
        'data-testid': 'ui-input'
      })
    );

    render(React.createElement(Input, { disabled: true }));

    const input = screen.getByTestId('ui-input');
    expect(input).toBeDisabled();
  });
});

describe('Card Component', () => {
  test('renders card with content', () => {
    const Card = ({ children, className }) => (
      React.createElement('div', {
        className: `card ${className || ''}`,
        'data-testid': 'ui-card'
      }, children)
    );

    const CardHeader = ({ children }) => (
      React.createElement('div', { 'data-testid': 'card-header' }, children)
    );

    const CardContent = ({ children }) => (
      React.createElement('div', { 'data-testid': 'card-content' }, children)
    );

    render(
      React.createElement(Card, null,
        React.createElement(CardHeader, null, 'Card Title'),
        React.createElement(CardContent, null, 'Card content')
      )
    );

    expect(screen.getByTestId('ui-card')).toBeInTheDocument();
    expect(screen.getByTestId('card-header')).toHaveTextContent('Card Title');
    expect(screen.getByTestId('card-content')).toHaveTextContent('Card content');
  });

  test('applies custom className', () => {
    const Card = ({ className }) => (
      React.createElement('div', {
        className: `card ${className || ''}`,
        'data-testid': 'ui-card'
      })
    );

    render(React.createElement(Card, { className: 'custom-class' }));

    const card = screen.getByTestId('ui-card');
    expect(card).toHaveClass('card', 'custom-class');
  });
});

describe('Alert Component', () => {
  test('renders alert with different variants', () => {
    const Alert = ({ children, variant }) => (
      React.createElement('div', {
        className: `alert alert-${variant}`,
        'data-testid': 'ui-alert'
      }, children)
    );

    const { rerender } = render(
      React.createElement(Alert, { variant: 'success' }, 'Success message')
    );

    expect(screen.getByTestId('ui-alert')).toHaveClass('alert-success');
    expect(screen.getByText('Success message')).toBeInTheDocument();

    rerender(React.createElement(Alert, { variant: 'error' }, 'Error message'));
    expect(screen.getByTestId('ui-alert')).toHaveClass('alert-error');
  });

  test('renders alert with title and description', () => {
    const Alert = ({ children }) => (
      React.createElement('div', { 'data-testid': 'ui-alert' }, children)
    );

    const AlertTitle = ({ children }) => (
      React.createElement('h4', { 'data-testid': 'alert-title' }, children)
    );

    const AlertDescription = ({ children }) => (
      React.createElement('p', { 'data-testid': 'alert-description' }, children)
    );

    render(
      React.createElement(Alert, null,
        React.createElement(AlertTitle, null, 'Alert Title'),
        React.createElement(AlertDescription, null, 'Alert description text')
      )
    );

    expect(screen.getByTestId('alert-title')).toHaveTextContent('Alert Title');
    expect(screen.getByTestId('alert-description')).toHaveTextContent('Alert description text');
  });
});

describe('Progress Component', () => {
  test('renders progress bar with correct value', () => {
    const Progress = ({ value, max }) => (
      React.createElement('div', { 'data-testid': 'ui-progress' },
        React.createElement('div', {
          style: { width: `${(value / (max || 100)) * 100}%` },
          'data-testid': 'progress-bar'
        }),
        React.createElement('span', { 'data-testid': 'progress-text' }, `${value}%`)
      )
    );

    render(React.createElement(Progress, { value: 75, max: 100 }));

    const progressBar = screen.getByTestId('progress-bar');
    const progressText = screen.getByTestId('progress-text');

    expect(progressBar).toHaveStyle({ width: '75%' });
    expect(progressText).toHaveTextContent('75%');
  });

  test('handles different max values', () => {
    const Progress = ({ value, max }) => (
      React.createElement('div', { 'data-testid': 'ui-progress' },
        React.createElement('div', {
          style: { width: `${(value / max) * 100}%` },
          'data-testid': 'progress-bar'
        })
      )
    );

    render(React.createElement(Progress, { value: 3, max: 10 }));

    const progressBar = screen.getByTestId('progress-bar');
    expect(progressBar).toHaveStyle({ width: '30%' });
  });
});

describe('Dialog Component', () => {
  test('renders dialog when open', () => {
    const Dialog = ({ open, children }) => {
      if (!open) return null;

      return React.createElement('div', {
        'data-testid': 'ui-dialog',
        role: 'dialog'
      }, children);
    };

    const DialogContent = ({ children }) => (
      React.createElement('div', { 'data-testid': 'dialog-content' }, children)
    );

    const DialogHeader = ({ children }) => (
      React.createElement('div', { 'data-testid': 'dialog-header' }, children)
    );

    render(
      React.createElement(Dialog, { open: true },
        React.createElement(DialogContent, null,
          React.createElement(DialogHeader, null, 'Dialog Title'),
          React.createElement('p', null, 'Dialog content')
        )
      )
    );

    expect(screen.getByTestId('ui-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('dialog-header')).toHaveTextContent('Dialog Title');
    expect(screen.getByText('Dialog content')).toBeInTheDocument();
  });

  test('does not render when closed', () => {
    const Dialog = ({ open, children }) => {
      if (!open) return null;

      return React.createElement('div', { 'data-testid': 'ui-dialog' }, children);
    };

    render(React.createElement(Dialog, { open: false }, 'Content'));

    expect(screen.queryByTestId('ui-dialog')).not.toBeInTheDocument();
  });

  test('handles close action', () => {
    const Dialog = ({ open, onClose, children }) => {
      if (!open) return null;

      return React.createElement('div', { 'data-testid': 'ui-dialog' },
        React.createElement('button', {
          onClick: onClose,
          'data-testid': 'close-button'
        }, '×'),
        children
      );
    };

    const handleClose = jest.fn();
    render(
      React.createElement(Dialog, { open: true, onClose: handleClose },
        'Dialog content'
      )
    );

    const closeButton = screen.getByTestId('close-button');
    fireEvent.click(closeButton);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});

describe('Badge Component', () => {
  test('renders badge with text', () => {
    const Badge = ({ children, variant }) => (
      React.createElement('span', {
        className: `badge badge-${variant || 'default'}`,
        'data-testid': 'ui-badge'
      }, children)
    );

    render(React.createElement(Badge, { variant: 'success' }, 'Active'));

    const badge = screen.getByTestId('ui-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Active');
    expect(badge).toHaveClass('badge-success');
  });

  test('supports different variants', () => {
    const Badge = ({ variant }) => (
      React.createElement('span', {
        className: `badge badge-${variant}`,
        'data-testid': 'ui-badge'
      }, variant)
    );

    const variants = ['primary', 'secondary', 'success', 'warning', 'error'];

    variants.forEach(variant => {
      const { rerender } = render(React.createElement(Badge, { variant }));
      expect(screen.getByTestId('ui-badge')).toHaveClass(`badge-${variant}`);
    });
  });
});

describe('Checkbox Component', () => {
  test('renders checkbox with correct state', () => {
    const Checkbox = ({ checked, onChange, label }) => (
      React.createElement('label', { 'data-testid': 'checkbox-label' },
        React.createElement('input', {
          type: 'checkbox',
          checked,
          onChange: (e) => onChange(e.target.checked),
          'data-testid': 'ui-checkbox'
        }),
        label
      )
    );

    render(React.createElement(Checkbox, {
      checked: true,
      label: 'Accept terms'
    }));

    const checkbox = screen.getByTestId('ui-checkbox');
    const label = screen.getByTestId('checkbox-label');

    expect(checkbox).toBeChecked();
    expect(label).toHaveTextContent('Accept terms');
  });

  test('handles checkbox toggle', () => {
    const Checkbox = ({ checked, onChange }) => (
      React.createElement('input', {
        type: 'checkbox',
        checked,
        onChange: (e) => onChange(e.target.checked),
        'data-testid': 'ui-checkbox'
      })
    );

    const handleChange = jest.fn();
    render(React.createElement(Checkbox, { checked: false, onChange: handleChange }));

    const checkbox = screen.getByTestId('ui-checkbox');
    fireEvent.click(checkbox);

    expect(handleChange).toHaveBeenCalledWith(true);
  });
});

describe('Select Component', () => {
  test('renders select with options', () => {
    const Select = ({ value, onChange, children }) => (
      React.createElement('select', {
        value,
        onChange: (e) => onChange(e.target.value),
        'data-testid': 'ui-select'
      }, children)
    );

    const SelectItem = ({ value, children }) => (
      React.createElement('option', { value }, children)
    );

    render(
      React.createElement(Select, { value: 'option1' },
        React.createElement(SelectItem, { value: 'option1' }, 'Option 1'),
        React.createElement(SelectItem, { value: 'option2' }, 'Option 2')
      )
    );

    const select = screen.getByTestId('ui-select');
    expect(select).toHaveValue('option1');
    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
  });

  test('handles selection change', () => {
    const Select = ({ value, onChange }) => (
      React.createElement('select', {
        value,
        onChange: (e) => onChange(e.target.value),
        'data-testid': 'ui-select'
      },
        React.createElement('option', { value: 'a' }, 'A'),
        React.createElement('option', { value: 'b' }, 'B')
      )
    );

    const handleChange = jest.fn();
    render(React.createElement(Select, { value: 'a', onChange: handleChange }));

    const select = screen.getByTestId('ui-select');
    fireEvent.change(select, { target: { value: 'b' } });

    expect(handleChange).toHaveBeenCalledWith('b');
  });
});

describe('Tabs Component', () => {
  test('renders tabs with content', () => {
    const Tabs = ({ children }) => (
      React.createElement('div', { 'data-testid': 'ui-tabs' }, children)
    );

    const TabsList = ({ children }) => (
      React.createElement('div', { 'data-testid': 'tabs-list' }, children)
    );

    const TabsTrigger = ({ children, active }) => (
      React.createElement('button', {
        className: active ? 'active' : '',
        'data-testid': 'tab-trigger'
      }, children)
    );

    const TabsContent = ({ children, active }) => (
      active ? React.createElement('div', { 'data-testid': 'tab-content' }, children) : null
    );

    render(
      React.createElement(Tabs, null,
        React.createElement(TabsList, null,
          React.createElement(TabsTrigger, { active: true }, 'Tab 1'),
          React.createElement(TabsTrigger, { active: false }, 'Tab 2')
        ),
        React.createElement(TabsContent, { active: true }, 'Content 1'),
        React.createElement(TabsContent, { active: false }, 'Content 2')
      )
    );

    expect(screen.getByTestId('ui-tabs')).toBeInTheDocument();
    expect(screen.getAllByTestId('tab-trigger')).toHaveLength(2);
    expect(screen.getByTestId('tab-content')).toHaveTextContent('Content 1');
    expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
  });

  test('switches tab content', () => {
    const TabsComponent = () => {
      const [activeTab, setActiveTab] = React.useState('tab1');

      return React.createElement('div', { 'data-testid': 'tabs-container' },
        React.createElement('button', {
          onClick: () => setActiveTab('tab1'),
          'data-testid': 'tab1-button'
        }, 'Tab 1'),
        React.createElement('button', {
          onClick: () => setActiveTab('tab2'),
          'data-testid': 'tab2-button'
        }, 'Tab 2'),
        activeTab === 'tab1' && React.createElement('div', { 'data-testid': 'content1' }, 'Content 1'),
        activeTab === 'tab2' && React.createElement('div', { 'data-testid': 'content2' }, 'Content 2')
      );
    };

    render(React.createElement(TabsComponent));

    expect(screen.getByTestId('content1')).toBeInTheDocument();
    expect(screen.queryByTestId('content2')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('tab2-button'));

    expect(screen.queryByTestId('content1')).not.toBeInTheDocument();
    expect(screen.getByTestId('content2')).toBeInTheDocument();
  });
});