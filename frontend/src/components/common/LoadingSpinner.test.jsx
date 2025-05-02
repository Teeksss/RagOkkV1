import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from './LoadingSpinner';

describe('LoadingSpinner Component', () => {
  test('renders with default props', () => {
    render(<LoadingSpinner />);
    const spinnerElement = screen.getByTestId('loading-spinner');
    expect(spinnerElement).toBeInTheDocument();
    expect(spinnerElement).toHaveClass('animate-spin');
    expect(spinnerElement).toHaveClass('h-8 w-8'); // Medium size default
    expect(spinnerElement).toHaveClass('text-blue-600'); // Blue color default
  });

  test('renders with small size', () => {
    render(<LoadingSpinner size="small" />);
    const spinnerElement = screen.getByTestId('loading-spinner');
    expect(spinnerElement).toHaveClass('h-4 w-4');
  });

  test('renders with large size', () => {
    render(<LoadingSpinner size="large" />);
    const spinnerElement = screen.getByTestId('loading-spinner');
    expect(spinnerElement).toHaveClass('h-12 w-12');
  });

  test('renders with white color', () => {
    render(<LoadingSpinner color="white" />);
    const spinnerElement = screen.getByTestId('loading-spinner');
    expect(spinnerElement).toHaveClass('text-white');
  });

  test('renders with custom className', () => {
    render(<LoadingSpinner className="custom-class" />);
    const spinnerElement = screen.getByTestId('loading-spinner');
    expect(spinnerElement).toHaveClass('custom-class');
  });
});