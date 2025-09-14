import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

// Mock react-query hooks to avoid needing a provider or network
vi.mock('@tanstack/react-query', async (orig) => {
  const original = await orig();
  return {
    ...original,
    useQuery: () => ({ isLoading: false, isError: false, data: { items: [] }, error: undefined, refetch: vi.fn() }),
    useMutation: () => ({ mutate: vi.fn(), isPending: false, isError: false, error: undefined }),
    useQueryClient: () => ({ invalidateQueries: vi.fn(), cancelQueries: vi.fn(), getQueryData: vi.fn(), setQueryData: vi.fn() }),
  } as any;
});

import LineupPage from '../../src/app/lineup/page';
import { ToastProvider } from '../../src/components/ui/toast';

describe('LineupPage basic behavior', () => {
  it('renders and disables Save until Team ID is set', () => {
    render(
      <ToastProvider>
        <LineupPage />
      </ToastProvider>
    );

    expect(screen.getByRole('heading', { name: /set lineup/i })).toBeInTheDocument();

    const save = screen.getByRole('button', { name: /save lineup/i });
    expect(save).toBeDisabled();

    // Set Team ID; Save should enable (validation occurs on submit)
    fireEvent.change(screen.getByPlaceholderText('team uuid'), { target: { value: 'T1' } });
    expect(save).not.toBeDisabled();
  });
});

