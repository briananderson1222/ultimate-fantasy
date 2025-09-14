import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { DataTable } from '../../src/components/ui/data-table';

type Row = { name: string; points: number };

describe('DataTable filters', () => {
  const columns = [
    { key: 'name', header: 'Name', sortable: true },
    { key: 'points', header: 'Points', sortable: true },
  ];
  const data: Row[] = [
    { name: 'Alpha', points: 10 },
    { name: 'Charlie', points: 4 },
    { name: 'Bravo', points: 7 },
  ];

  it('filters rows by contains operator', () => {
    render(<DataTable columns={columns} data={data} pageSize={10} storageKey="filters-test" />);

    // Open Filters
    const summary = screen.getByText('Filters');
    fireEvent.click(summary);

    // Select column 'Name' (default) and set value 'a'
    const valueInput = screen.getByLabelText('Value');
    fireEvent.change(valueInput, { target: { value: 'a' } });
    fireEvent.click(screen.getByRole('button', { name: /add/i }));

    // Should show only rows with 'a' (case-insensitive): Alpha, Bravo
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(1 /* header */ + 2);
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Bravo')).toBeInTheDocument();
  });
});

