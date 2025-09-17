import type { Story } from '@ladle/react';
import { Button } from '../components/design-system/primitives/Button';

const FantasyActionDemo = () => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold">Fantasy Sports Actions</h2>

    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-3">Lineup Management</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" size="md">Set Lineup</Button>
          <Button variant="secondary" size="md">View Bench</Button>
          <Button variant="outline" size="md">Auto-Fill</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Player Transactions</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="success" size="md">Add Player</Button>
          <Button variant="warning" size="md">Trade Player</Button>
          <Button variant="danger" size="md">Drop Player</Button>
          <Button variant="outline" size="md">Add to Watchlist</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">League Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" size="lg">Join League</Button>
          <Button variant="secondary" size="md">View Settings</Button>
          <Button variant="ghost" size="md">Leave League</Button>
        </div>
      </div>
    </div>
  </div>
);

export const Default: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Basic Buttons</h2>
    <div className="flex flex-wrap gap-3">
      <Button>Default Button</Button>
      <Button disabled>Disabled Button</Button>
    </div>
  </div>
);

export const Variants: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Button Variants</h2>
    <div className="flex flex-wrap gap-3">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="success">Success</Button>
      <Button variant="warning">Warning</Button>
      <Button variant="danger">Danger</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  </div>
);

export const Sizes: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Button Sizes</h2>
    <div className="flex flex-wrap items-center gap-3">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  </div>
);

export const States: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Button States</h2>

    <div className="space-y-3">
      <div>
        <h3 className="text-lg font-semibold mb-2">Normal State</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary">Normal</Button>
          <Button variant="secondary">Normal</Button>
          <Button variant="outline">Normal</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Disabled State</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" disabled>Disabled</Button>
          <Button variant="secondary" disabled>Disabled</Button>
          <Button variant="outline" disabled>Disabled</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Loading State</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" loading>Loading...</Button>
          <Button variant="secondary" loading>Processing</Button>
          <Button variant="outline" loading>Submitting</Button>
        </div>
      </div>
    </div>
  </div>
);

export const WithIcons: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Buttons with Icons</h2>

    <div className="space-y-3">
      <div>
        <h3 className="text-lg font-semibold mb-2">Icon + Text</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" leftIcon="plus">Add Player</Button>
          <Button variant="warning" leftIcon="refresh">Trade</Button>
          <Button variant="danger" leftIcon="trash">Drop</Button>
          <Button variant="outline" rightIcon="external-link">View Profile</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Icon Only</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="ghost" size="sm" isIconOnly aria-label="Settings">⚙</Button>
          <Button variant="ghost" size="sm" isIconOnly aria-label="Favorite">★</Button>
          <Button variant="ghost" size="sm" isIconOnly aria-label="More options">⋮</Button>
          <Button variant="outline" size="md" isIconOnly aria-label="Filter">⚡</Button>
        </div>
      </div>
    </div>
  </div>
);

export const FullWidth: Story = () => (
  <div className="p-6 space-y-4 max-w-md">
    <h2 className="text-2xl font-bold">Full Width Buttons</h2>
    <Button variant="primary" fullWidth>Join League</Button>
    <Button variant="secondary" fullWidth>Create New League</Button>
    <Button variant="outline" fullWidth>Browse Public Leagues</Button>
  </div>
);

export const ButtonGroups: Story = () => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold">Button Groups</h2>

    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2">Position Filters</h3>
        <div className="inline-flex rounded-lg overflow-hidden border border-gray-300">
          <Button variant="ghost" size="sm" className="rounded-none border-0">All</Button>
          <Button variant="ghost" size="sm" className="rounded-none border-0 bg-blue-50">QB</Button>
          <Button variant="ghost" size="sm" className="rounded-none border-0">RB</Button>
          <Button variant="ghost" size="sm" className="rounded-none border-0">WR</Button>
          <Button variant="ghost" size="sm" className="rounded-none border-0">TE</Button>
          <Button variant="ghost" size="sm" className="rounded-none border-0">DEF</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">View Toggle</h3>
        <div className="inline-flex rounded-lg overflow-hidden border border-gray-300">
          <Button variant="ghost" size="md" className="rounded-none border-0 bg-blue-50">My Team</Button>
          <Button variant="ghost" size="md" className="rounded-none border-0">All Players</Button>
          <Button variant="ghost" size="md" className="rounded-none border-0">Free Agents</Button>
        </div>
      </div>
    </div>
  </div>
);

export const FantasyActions: Story = () => <FantasyActionDemo />;

Default.meta = {
  title: 'Design System/Primitives/Button',
};