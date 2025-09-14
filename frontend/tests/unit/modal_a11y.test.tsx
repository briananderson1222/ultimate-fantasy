import { render } from '@testing-library/react';
import React from 'react';
import { Modal } from '../../src/components/ui/modal';

describe('Modal a11y', () => {
  it('renders dialog role and aria-labelledby when title is provided', () => {
    const { getByRole } = render(
      <Modal open onClose={() => {}} title="Edit">
        Body
      </Modal>
    );
    const dialog = getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby');
  });
});

