import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

// Mock react-query useMutation to avoid provider/network
vi.mock('@tanstack/react-query', async (orig) => {
  const original = await orig();
  return {
    ...original,
    useMutation: () => ({ mutate: vi.fn(), isPending: false, isError: false, error: undefined }),
  } as any;
});

import Page from '../../src/app/leagues/[leagueId]/settings/page';
import { ToastProvider } from '../../src/components/ui/toast';

// Mock next/navigation useParams to provide a leagueId
vi.mock('next/navigation', () => ({ useParams: () => ({ leagueId: '00000000-0000-0000-0000-000000000000' }) }));

describe('League Settings Rule Editor', () => {
  it('shows JSON error for invalid JSON', () => {
    render(
      <ToastProvider>
        <Page />
      </ToastProvider>
    );

    const textarea = screen.getByLabelText('Value (JSON)') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: '{"bad": }' } });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    expect(screen.getByText(/unexpected token|json/i)).toBeInTheDocument();
  });
});

