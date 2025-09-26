import React from "react";
import { Button } from "./Button";
import { Trophy, Plus, Settings, ChevronRight } from "lucide-react";

export default { title: "Design System/Primitives/Button" };

export const Variants = () => (
  <div className="p-6 space-y-4">
    <div className="flex gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="destructive">Destructive</Button>
    </div>
  </div>
);

export const Sizes = () => (
  <div className="p-6 space-y-4">
    <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
      <Button size="xl">Extra Large</Button>
    </div>
  </div>
);

export const WithIcons = () => (
  <div className="p-6 space-y-4">
    <div className="flex gap-4">
      <Button leftIcon={<Plus className="h-4 w-4" />}>Add Player</Button>
      <Button rightIcon={<ChevronRight className="h-4 w-4" />}>View Details</Button>
      <Button
        leftIcon={<Trophy className="h-4 w-4" />}
        rightIcon={<ChevronRight className="h-4 w-4" />}
      >
        Leaderboard
      </Button>
    </div>
  </div>
);

export const IconOnly = () => (
  <div className="p-6 space-y-4">
    <div className="flex gap-4">
      <Button variant="primary" size="sm" isIconOnly>
        <Settings className="h-4 w-4" />
      </Button>
      <Button variant="secondary" size="md" isIconOnly>
        <Plus className="h-4 w-4" />
      </Button>
      <Button variant="outline" size="lg" isIconOnly>
        <Trophy className="h-4 w-4" />
      </Button>
    </div>
  </div>
);

export const States = () => (
  <div className="p-6 space-y-4">
    <div className="space-y-2">
      <div className="text-sm font-medium">Default</div>
      <div className="flex gap-4">
        <Button>Normal</Button>
        <Button disabled>Disabled</Button>
        <Button loading>Loading</Button>
      </div>
    </div>
    <div className="space-y-2">
      <div className="text-sm font-medium">Secondary</div>
      <div className="flex gap-4">
        <Button variant="secondary">Normal</Button>
        <Button variant="secondary" disabled>
          Disabled
        </Button>
        <Button variant="secondary" loading>
          Loading
        </Button>
      </div>
    </div>
  </div>
);

export const FantasySportsActions = () => (
  <div className="p-6 space-y-6">
    <div className="space-y-2">
      <div className="text-sm font-medium">League Management</div>
      <div className="flex flex-wrap gap-2">
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />}>
          Create League
        </Button>
        <Button variant="secondary">Join League</Button>
        <Button variant="outline">View Settings</Button>
      </div>
    </div>
    <div className="space-y-2">
      <div className="text-sm font-medium">Player Actions</div>
      <div className="flex flex-wrap gap-2">
        <Button variant="primary">Start Player</Button>
        <Button variant="secondary">Bench Player</Button>
        <Button variant="outline">Add to Watchlist</Button>
        <Button variant="destructive">Drop Player</Button>
      </div>
    </div>
    <div className="space-y-2">
      <div className="text-sm font-medium">Trade Actions</div>
      <div className="flex flex-wrap gap-2">
        <Button variant="primary">Send Trade</Button>
        <Button variant="secondary">Counter Offer</Button>
        <Button variant="outline">View History</Button>
        <Button variant="destructive">Reject Trade</Button>
      </div>
    </div>
  </div>
);
