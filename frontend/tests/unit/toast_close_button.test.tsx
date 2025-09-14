import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { ToastProvider, useToast } from '../../src/components/ui/toast';

function Demo() {
  const toast = useToast();
  return (
    <button onClick={() => toast.show({ title: 'Notice', description: 'Hello' })}>Show</button>
  );
}

describe('Toast close button', () => {
  it('has accessible label and closes when clicked', () => {
    render(
      <ToastProvider>
        <Demo />
      </ToastProvider>
    );
    fireEvent.click(screen.getByRole('button', { name: /show/i }));
    const close = screen.getByRole('button', { name: /close notification/i });
    fireEvent.click(close);
    expect(screen.queryByText('Notice')).toBeNull();
  });
});

