import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

// Mock next/navigation useParams to provide a stable leagueId
vi.mock('next/navigation', async (orig) => {
  const mod = await orig();
  return {
    ...mod,
    useParams: () => ({ leagueId: '00000000-0000-0000-0000-000000000001' }),
  };
});

// Mock API layer used by the page
const api = vi.hoisted(() => ({
  getPublicLeague: vi.fn(),
  getScoreboard: vi.fn(),
  getLeagueMembers: vi.fn(),
}));

vi.mock('../../src/services/api', () => ({
  getPublicLeague: api.getPublicLeague,
  getScoreboard: api.getScoreboard,
  getLeagueMembers: api.getLeagueMembers,
}));

import Providers from '../../src/app/providers';
import LeaguePublicPage from '../../src/app/leagues/[leagueId]/page';

const LID = '00000000-0000-0000-0000-000000000001';

function setupDefaultMocks() {
  api.getPublicLeague.mockResolvedValue({
    league_id: LID,
    name: 'Prime League',
    sport: 'nba',
    league_type: 'redraft',
    season: '2025',
  });
  api.getScoreboard.mockResolvedValue({ league_id: LID, items: [] });
}

describe('League Public • Managers tab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  it('renders managers list when data exists', async () => {
    api.getLeagueMembers.mockResolvedValue({
      items: [
        { team_id: 't1', user_id: 'aaaaaaaa-1111-2222-3333-444444444444', team_name: 'A Team' },
        { team_id: 't2', user_id: 'bbbbbbbb-1111-2222-3333-444444444444', team_name: 'B Team' },
      ],
    });

    render(
      <Providers>
        <LeaguePublicPage />
      </Providers>
    );

    // Wait for tabs to appear after league info loads
    const tablist = await screen.findByRole('tablist');
    const managersTab = within(tablist).getByRole('tab', { name: /Managers/i });

    // Switch to Managers tab
    fireEvent.click(managersTab);

    // Assert list items render with team names and short user ids
    const list = await screen.findByRole('list');
    expect(within(list).getByText('A Team')).toBeInTheDocument();
    expect(within(list).getByText('B Team')).toBeInTheDocument();
    // Short ids are first 8 chars of user_id
    expect(within(list).getByText('aaaaaaaa')).toBeInTheDocument();
    expect(within(list).getByText('bbbbbbbb')).toBeInTheDocument();
  });

  it('shows empty state when no managers', async () => {
    api.getLeagueMembers.mockResolvedValue({ items: [] });

    render(
      <Providers>
        <LeaguePublicPage />
      </Providers>
    );

    const tablist = await screen.findByRole('tablist');
    const managersTab = within(tablist).getByRole('tab', { name: /Managers/i });
    fireEvent.click(managersTab);

    expect(await screen.findByText(/No managers yet/i)).toBeInTheDocument();
  });

  it('supports keyboard navigation to Managers tab (focus order)', async () => {
    api.getLeagueMembers.mockResolvedValue({ items: [] });

    render(
      <Providers>
        <LeaguePublicPage />
      </Providers>
    );

    const tablist = await screen.findByRole('tablist');
    // Move from Overview -> Scoreboard -> Managers via ArrowRight
    fireEvent.keyDown(tablist, { key: 'ArrowRight' });
    fireEvent.keyDown(tablist, { key: 'ArrowRight' });
    const managersTab = within(tablist).getByRole('tab', { name: /Managers/i });
    expect(managersTab).toHaveAttribute('aria-selected', 'true');
  });
});

