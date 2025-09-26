import React from "react";
import { TrendingPlayers } from "./TrendingPlayers";

export default { title: "Design System/Patterns/TrendingPlayers" };

const mockTrendingData = [
  {
    id: "1",
    name: "Ja'Marr Chase",
    position: "WR",
    team: "CIN",
    photoUrl: "/player-photos/chase.jpg",
    trendData: {
      direction: "up" as const,
      percentage: 15.3,
      reason: "Target share increasing",
      addDropPercentage: 23.1,
    },
    weeklyPoints: [12.3, 18.7, 24.1, 19.5],
    projectedPoints: 21.8,
  },
  {
    id: "2",
    name: "Gus Edwards",
    position: "RB",
    team: "BAL",
    photoUrl: "/player-photos/edwards.jpg",
    trendData: {
      direction: "down" as const,
      percentage: -8.7,
      reason: "Injury concerns",
      addDropPercentage: -12.4,
    },
    weeklyPoints: [15.2, 8.1, 6.3, 4.9],
    projectedPoints: 8.2,
  },
  {
    id: "3",
    name: "Rashee Rice",
    position: "WR",
    team: "KC",
    photoUrl: "/player-photos/rice.jpg",
    trendData: {
      direction: "hot" as const,
      percentage: 28.9,
      reason: "Breakout performance",
      addDropPercentage: 45.2,
    },
    weeklyPoints: [3.1, 8.4, 19.7, 26.3],
    projectedPoints: 18.9,
  },
];

export const Default = () => (
  <div className="p-6">
    <TrendingPlayers players={mockTrendingData} />
  </div>
);

export const TrendingUp = () => (
  <div className="p-6">
    <TrendingPlayers
      players={mockTrendingData.filter((p) => p.trendData.direction === "up")}
      title="Trending Up"
    />
  </div>
);

export const TrendingDown = () => (
  <div className="p-6">
    <TrendingPlayers
      players={mockTrendingData.filter((p) => p.trendData.direction === "down")}
      title="Trending Down"
    />
  </div>
);

export const HotPlayers = () => (
  <div className="p-6">
    <TrendingPlayers
      players={mockTrendingData.filter((p) => p.trendData.direction === "hot")}
      title="Hot Pickups"
    />
  </div>
);

export const WithFilters = () => (
  <div className="p-6">
    <TrendingPlayers
      players={mockTrendingData}
      filters={{
        position: ["QB", "RB", "WR", "TE"],
        trend: ["up", "down", "hot"],
        availability: ["available", "rostered"],
      }}
      onFilterChange={(filters) => console.log("Filters changed:", filters)}
    />
  </div>
);

export const Compact = () => (
  <div className="p-6">
    <TrendingPlayers players={mockTrendingData} variant="compact" />
  </div>
);

export const WithActions = () => (
  <div className="p-6">
    <TrendingPlayers
      players={mockTrendingData}
      showActions
      onAddPlayer={(playerId) => alert(`Add player ${playerId}`)}
      onWatchPlayer={(playerId) => alert(`Watch player ${playerId}`)}
    />
  </div>
);

export const LargeDataset = () => {
  const largeMockData = Array.from({ length: 20 }, (_, i) => ({
    ...mockTrendingData[i % 3],
    id: `player-${i}`,
    name: `Player ${i + 1}`,
    trendData: {
      ...mockTrendingData[i % 3].trendData,
      percentage: Math.random() * 40 - 20,
      addDropPercentage: Math.random() * 60 - 30,
    },
  }));

  return (
    <div className="p-6">
      <TrendingPlayers players={largeMockData} />
    </div>
  );
};

export const Loading = () => (
  <div className="p-6">
    <TrendingPlayers players={[]} loading />
  </div>
);

export const Empty = () => (
  <div className="p-6">
    <TrendingPlayers players={[]} />
  </div>
);
