import type { Story } from '@ladle/react';
import { Card } from '../components/design-system/primitives/Card';

const FantasyCardDemo = () => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold">Fantasy Sports Cards</h2>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card variant="default" padding="md">
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Team Score</h3>
            <span className="text-2xl font-bold text-green-600">127.4</span>
          </div>
          <div className="text-sm text-gray-600">
            <p>Projected: 132.1 pts</p>
            <p>Win Probability: 73%</p>
          </div>
        </div>
      </Card>

      <Card variant="elevated" padding="md">
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
              JA
            </div>
            <div>
              <h3 className="font-semibold">Josh Allen</h3>
              <p className="text-sm text-gray-600">QB • Buffalo Bills</p>
            </div>
          </div>
          <div className="flex justify-between text-sm">
            <span>Projected</span>
            <span className="font-semibold">23.2 pts</span>
          </div>
        </div>
      </Card>

      <Card variant="outlined" padding="md">
        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Week 15 Matchup</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Your Team</span>
              <span className="font-semibold">127.4</span>
            </div>
            <div className="flex justify-between">
              <span>Opponent</span>
              <span className="font-semibold">119.7</span>
            </div>
          </div>
          <div className="text-center text-sm text-green-600 font-medium">
            Leading by 7.7 pts
          </div>
        </div>
      </Card>
    </div>
  </div>
);

export const Default: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Basic Cards</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <p>Default card with default padding</p>
      </Card>
      <Card padding="lg">
        <p>Card with large padding</p>
      </Card>
    </div>
  </div>
);

export const Variants: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Card Variants</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card variant="default" padding="md">
        <h3 className="font-semibold mb-2">Default Card</h3>
        <p className="text-gray-600">Basic card with subtle background</p>
      </Card>

      <Card variant="elevated" padding="md">
        <h3 className="font-semibold mb-2">Elevated Card</h3>
        <p className="text-gray-600">Card with enhanced shadow</p>
      </Card>

      <Card variant="outlined" padding="md">
        <h3 className="font-semibold mb-2">Outlined Card</h3>
        <p className="text-gray-600">Card with visible border</p>
      </Card>

      <Card variant="flat" padding="md">
        <h3 className="font-semibold mb-2">Flat Card</h3>
        <p className="text-gray-600">Card with no shadow or border</p>
      </Card>

      <Card variant="interactive" padding="md">
        <h3 className="font-semibold mb-2">Interactive Card</h3>
        <p className="text-gray-600">Clickable card with hover effects</p>
      </Card>

      <Card variant="primary" padding="md">
        <h3 className="font-semibold mb-2 text-white">Primary Card</h3>
        <p className="text-blue-100">Card with primary color background</p>
      </Card>
    </div>
  </div>
);

export const Padding: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Card Padding</h2>
    <div className="space-y-4">
      <Card variant="outlined" padding="none">
        <div className="bg-gray-100 p-2 text-center">No Padding</div>
      </Card>
      <Card variant="outlined" padding="sm">
        <div className="bg-gray-100 text-center">Small Padding</div>
      </Card>
      <Card variant="outlined" padding="md">
        <div className="bg-gray-100 text-center">Medium Padding</div>
      </Card>
      <Card variant="outlined" padding="lg">
        <div className="bg-gray-100 text-center">Large Padding</div>
      </Card>
    </div>
  </div>
);

export const InteractiveCards: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Interactive Cards</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card
        variant="interactive"
        padding="md"
        onClick={() => alert('Card clicked!')}
      >
        <h3 className="font-semibold mb-2">Clickable Card</h3>
        <p className="text-gray-600">Click me to see the action</p>
      </Card>

      <Card
        variant="interactive"
        padding="md"
        disabled
      >
        <h3 className="font-semibold mb-2 text-gray-400">Disabled Card</h3>
        <p className="text-gray-400">This card is not clickable</p>
      </Card>
    </div>
  </div>
);

export const CardWithHeader: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Cards with Headers</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card variant="outlined" padding="none">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="font-semibold">Card Header</h3>
        </div>
        <div className="p-4">
          <p className="text-gray-600">Card content goes here with custom header styling.</p>
        </div>
      </Card>

      <Card variant="elevated" padding="none">
        <div className="px-4 py-3 bg-blue-600 text-white">
          <h3 className="font-semibold">Colored Header</h3>
        </div>
        <div className="p-4">
          <p className="text-gray-600">Card with a colored header section.</p>
        </div>
      </Card>
    </div>
  </div>
);

export const CardWithActions: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Cards with Actions</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card variant="outlined" padding="md">
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold">Player Available</h3>
            <p className="text-gray-600">Christian McCaffrey is available in your league</p>
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm">
              Add to Roster
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm">
              Add to Watchlist
            </button>
          </div>
        </div>
      </Card>

      <Card variant="elevated" padding="md">
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold">Trade Proposal</h3>
            <p className="text-gray-600">You have a new trade offer from TeamOwner123</p>
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1 bg-green-600 text-white rounded text-sm">
              Accept
            </button>
            <button className="px-3 py-1 bg-red-600 text-white rounded text-sm">
              Decline
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm">
              Counter
            </button>
          </div>
        </div>
      </Card>
    </div>
  </div>
);

export const ResponsiveCards: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Responsive Card Grid</h2>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: 8 }, (_, i) => (
        <Card key={i} variant="outlined" padding="md">
          <h3 className="font-semibold mb-2">Card {i + 1}</h3>
          <p className="text-gray-600">Responsive grid card content</p>
        </Card>
      ))}
    </div>
  </div>
);

export const FantasyCards: Story = () => <FantasyCardDemo />;

Default.meta = {
  title: 'Design System/Primitives/Card',
};