import { render, screen } from '@testing-library/react';
import { ProgressBar } from '../../src/components/design-system/primitives/ProgressBar';
import { ThemeProvider } from '../../src/components/design-system/providers/ThemeProvider';

const renderWithTheme = (component: React.ReactNode) => {
  return render(
    <ThemeProvider defaultTheme="dark">
      {component}
    </ThemeProvider>
  );
};

describe('ProgressBar', () => {
  it('renders with correct value and max', () => {
    renderWithTheme(<ProgressBar value={50} max={100} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('calculates percentage correctly', () => {
    renderWithTheme(<ProgressBar value={75} max={100} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '75');
  });

  it('handles different sizes', () => {
    renderWithTheme(<ProgressBar value={50} max={100} size="lg" />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('handles different variants', () => {
    renderWithTheme(<ProgressBar value={50} max={100} variant="success" />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('handles zero value', () => {
    renderWithTheme(<ProgressBar value={0} max={100} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
  });

  it('handles max value', () => {
    renderWithTheme(<ProgressBar value={100} max={100} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });

  it('is accessible with proper ARIA attributes', () => {
    renderWithTheme(<ProgressBar value={60} max={100} aria-label="Win percentage" />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', 'Win percentage');
    expect(progressBar).toHaveAttribute('aria-valuenow', '60');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('handles custom className', () => {
    renderWithTheme(<ProgressBar value={50} max={100} className="custom-class" />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('custom-class');
  });
});