import type { Story } from "@ladle/react";
import { ProgressBar } from "../components/design-system/primitives/ProgressBar";

// Win percentage examples for fantasy sports
const WinPercentageDemo = () => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold">Win Percentage Indicators</h2>

    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2">High Win Chance (Favorable Matchup)</h3>
        <ProgressBar
          value={87}
          variant="success"
          showLabel={true}
          label="Win Probability"
          animated={true}
        />
        <p className="text-sm text-gray-600 mt-1">Your team has an 87% chance to win this week</p>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Medium Win Chance (Close Matchup)</h3>
        <ProgressBar
          value={54}
          variant="default"
          showLabel={true}
          label="Win Probability"
          animated={true}
        />
        <p className="text-sm text-gray-600 mt-1">Projected close game - 54% chance to win</p>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Low Win Chance (Tough Matchup)</h3>
        <ProgressBar
          value={23}
          variant="warning"
          showLabel={true}
          label="Win Probability"
          animated={true}
        />
        <p className="text-sm text-gray-600 mt-1">Uphill battle - only 23% chance to win</p>
      </div>
    </div>
  </div>
);

const RosterPercentageDemo = () => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold">Player Roster Percentages</h2>

    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2">Popular Player (High Roster %)</h3>
        <ProgressBar value={94} size="md" showLabel={true} label="Rostered in 94% of leagues" />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Trending Player (Medium Roster %)</h3>
        <ProgressBar value={67} size="md" showLabel={true} label="Rostered in 67% of leagues" />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Sleeper Pick (Low Roster %)</h3>
        <ProgressBar value={12} size="md" showLabel={true} label="Rostered in 12% of leagues" />
      </div>
    </div>
  </div>
);

export const Default: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Basic Progress Bar</h2>
    <ProgressBar value={60} />
    <ProgressBar value={60} showLabel={true} />
    <ProgressBar value={60} showLabel={true} label="Custom Label" />
  </div>
);

export const Variants: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Progress Bar Variants</h2>
    <ProgressBar value={75} variant="default" showLabel={true} label="Default" />
    <ProgressBar value={85} variant="success" showLabel={true} label="Success" />
    <ProgressBar value={45} variant="warning" showLabel={true} label="Warning" />
    <ProgressBar value={15} variant="danger" showLabel={true} label="Danger" />
  </div>
);

export const Sizes: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Progress Bar Sizes</h2>
    <ProgressBar value={60} size="sm" showLabel={true} label="Small" />
    <ProgressBar value={60} size="md" showLabel={true} label="Medium" />
    <ProgressBar value={60} size="lg" showLabel={true} label="Large" />
  </div>
);

export const Animated: Story = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Animated Progress Bars</h2>
    <ProgressBar value={30} animated={true} showLabel={true} label="Loading..." />
    <ProgressBar
      value={60}
      animated={true}
      variant="success"
      showLabel={true}
      label="In Progress"
    />
    <ProgressBar
      value={90}
      animated={true}
      variant="success"
      showLabel={true}
      label="Almost Complete"
    />
  </div>
);

export const WinProbabilities: Story = () => <WinPercentageDemo />;

export const RosterStats: Story = () => <RosterPercentageDemo />;

export const FantasyScenarios: Story = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <WinPercentageDemo />
    <RosterPercentageDemo />
  </div>
);

Default.meta = {
  title: "Design System/Primitives/ProgressBar",
};
