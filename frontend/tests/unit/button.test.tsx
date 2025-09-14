import React from 'react';
import { render, screen } from '@testing-library/react';
import { Button } from '../../src/components/ui/button';

describe('Button', () => {
  it('disables and shows spinner when loading', () => {
    render(<Button loading>Submit</Button>);
    const btn = screen.getByRole('button', { name: /submit/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
  });
});
