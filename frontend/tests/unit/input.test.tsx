import React from 'react';
import { render, screen } from '@testing-library/react';
import { Input } from '../../src/components/ui/input';

describe('Input', () => {
  it('associates label with input and shows error', () => {
    render(<Input id="name" name="name" label="Name" error="Required" />);
    const label = screen.getByText('Name');
    const input = screen.getByLabelText('Name');
    expect(label).toHaveAttribute('for', 'name');
    expect(input).toBeInTheDocument();
    screen.getByText('Required');
  });
});
