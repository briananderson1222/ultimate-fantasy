import { render } from '@testing-library/react';
import React from 'react';
import RootLayout from '../../src/app/layout';

describe('RootLayout navigation', () => {
  it('renders main nav links', () => {
    const { getByRole } = render(
      <RootLayout>
        <div>Content</div>
      </RootLayout> as any
    );
    expect(getByRole('link', { name: /leagues/i })).toBeInTheDocument();
    expect(getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
  });
});
