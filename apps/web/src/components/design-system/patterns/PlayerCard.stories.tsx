import React from "react";
import { PlayerCard } from "./PlayerCard";

export default { title: "Design System/Patterns/PlayerCard" };

const mockPlayerData = {
  id: "1",
  name: "Patrick Mahomes",
  position: "QB",
  team: "KC",
  photoUrl: "/player-photos/mahomes.jpg",
  stats: {
    points: 24.5,
    projected: 22.1,
    passingYards: 325,
    touchdowns: 3,
    interceptions: 0
  },
  injury: null,
  status: "active" as const
};

export const Default = () => (
  <div className="p-6">
    <PlayerCard player={mockPlayerData} />
  </div>
);

export const DifferentPositions = () => (
  <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <PlayerCard player={mockPlayerData} />
    <PlayerCard
      player={{
        ...mockPlayerData,
        id: "2",
        name: "Derrick Henry",
        position: "RB",
        team: "TEN",
        stats: {
          points: 18.7,
          projected: 16.2,
          rushingYards: 125,
          touchdowns: 2,
          receptions: 3
        }
      }}
    />
    <PlayerCard
      player={{
        ...mockPlayerData,
        id: "3",
        name: "Cooper Kupp",
        position: "WR",
        team: "LAR",
        stats: {
          points: 21.3,
          projected: 19.5,
          receptions: 8,
          receivingYards: 95,
          touchdowns: 1
        }
      }}
    />
  </div>
);

export const InjuryStatus = () => (
  <div className="p-6 space-y-4">
    <PlayerCard
      player={{
        ...mockPlayerData,
        injury: { status: "questionable", description: "Ankle" }
      }}
    />
    <PlayerCard
      player={{
        ...mockPlayerData,
        name: "Aaron Rodgers",
        injury: { status: "out", description: "Achilles" },
        status: "injured"
      }}
    />
    <PlayerCard
      player={{
        ...mockPlayerData,
        name: "Josh Allen",
        injury: { status: "probable", description: "Shoulder" }
      }}
    />
  </div>
);

export const DifferentStatuses = () => (
  <div className="p-6 space-y-4">
    <PlayerCard player={{ ...mockPlayerData, status: "active" }} />
    <PlayerCard player={{ ...mockPlayerData, status: "bench", name: "Bench Player" }} />
    <PlayerCard player={{ ...mockPlayerData, status: "injured", name: "Injured Player" }} />
    <PlayerCard player={{ ...mockPlayerData, status: "bye", name: "Bye Week Player" }} />
  </div>
);

export const PerformanceVariations = () => (
  <div className="p-6 space-y-4">
    <PlayerCard
      player={{
        ...mockPlayerData,
        name: "Overperforming Player",
        stats: { ...mockPlayerData.stats, points: 28.5, projected: 18.2 }
      }}
    />
    <PlayerCard
      player={{
        ...mockPlayerData,
        name: "Underperforming Player",
        stats: { ...mockPlayerData.stats, points: 8.3, projected: 20.1 }
      }}
    />
    <PlayerCard
      player={{
        ...mockPlayerData,
        name: "Projected Performance",
        stats: { ...mockPlayerData.stats, points: 19.8, projected: 19.5 }
      }}
    />
  </div>
);

export const Compact = () => (
  <div className="p-6">
    <PlayerCard player={mockPlayerData} variant="compact" />
  </div>
);

export const WithActions = () => (
  <div className="p-6">
    <PlayerCard
      player={mockPlayerData}
      actions={[
        { label: "Start", action: () => alert("Start player") },
        { label: "Bench", action: () => alert("Bench player") },
        { label: "Drop", action: () => alert("Drop player"), destructive: true }
      ]}
    />
  </div>
);

export const Draggable = () => (
  <div className="p-6">
    <PlayerCard
      player={mockPlayerData}
      draggable
      onDragStart={() => console.log("Drag started")}
      onDragEnd={() => console.log("Drag ended")}
    />
  </div>
);

export const TeamRoster = () => (
  <div className="p-6">
    <div className="space-y-2">
      <h3 className="font-semibold">Starting Lineup</h3>
      <div className="grid grid-cols-1 gap-2">
        <PlayerCard player={{ ...mockPlayerData, status: "active" }} variant="compact" />
        <PlayerCard
          player={{
            ...mockPlayerData,
            id: "2",
            name: "Christian McCaffrey",
            position: "RB",
            team: "SF",
            status: "active"
          }}
          variant="compact"
        />
        <PlayerCard
          player={{
            ...mockPlayerData,
            id: "3",
            name: "Tyreek Hill",
            position: "WR",
            team: "MIA",
            status: "active"
          }}
          variant="compact"
        />
      </div>
    </div>
  </div>
);