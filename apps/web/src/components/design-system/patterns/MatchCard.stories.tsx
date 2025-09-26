import React from "react";
import { MatchCard } from "./MatchCard";

export default { title: "Design System/Patterns/MatchCard" };

const mockMatchData = {
  homeTeam: {
    id: "1",
    name: "Team Warriors",
    owner: "John Doe",
    logo: "/team-logos/warriors.png",
    record: { wins: 8, losses: 4 },
  },
  awayTeam: {
    id: "2",
    name: "Team Dragons",
    owner: "Jane Smith",
    logo: "/team-logos/dragons.png",
    record: { wins: 6, losses: 6 },
  },
  week: 13,
  projectedPoints: { home: 112.5, away: 108.2 },
  actualPoints: { home: 118.7, away: 105.3 },
  status: "completed" as const,
};

export const Upcoming = () => (
  <div className="p-6">
    <MatchCard
      match={{
        ...mockMatchData,
        status: "upcoming",
        actualPoints: undefined,
      }}
    />
  </div>
);

export const InProgress = () => (
  <div className="p-6">
    <MatchCard
      match={{
        ...mockMatchData,
        status: "in_progress",
        actualPoints: { home: 95.2, away: 78.1 },
      }}
    />
  </div>
);

export const Completed = () => (
  <div className="p-6">
    <MatchCard match={mockMatchData} />
  </div>
);

export const CloseGame = () => (
  <div className="p-6">
    <MatchCard
      match={{
        ...mockMatchData,
        actualPoints: { home: 112.4, away: 112.1 },
      }}
    />
  </div>
);

export const Blowout = () => (
  <div className="p-6">
    <MatchCard
      match={{
        ...mockMatchData,
        actualPoints: { home: 145.8, away: 89.2 },
      }}
    />
  </div>
);

export const WithPlayoffImplications = () => (
  <div className="p-6 space-y-4">
    <MatchCard
      match={{
        ...mockMatchData,
        playoffImplications: "Winner clinches playoff spot",
      }}
    />
    <MatchCard
      match={{
        ...mockMatchData,
        homeTeam: { ...mockMatchData.homeTeam, name: "Team Eliminators" },
        awayTeam: { ...mockMatchData.awayTeam, name: "Team Survivors" },
        playoffImplications: "Loser eliminated from playoffs",
      }}
    />
  </div>
);

export const DifferentWeeks = () => (
  <div className="p-6 space-y-4">
    <MatchCard
      match={{
        ...mockMatchData,
        week: 1,
        status: "upcoming",
      }}
    />
    <MatchCard
      match={{
        ...mockMatchData,
        week: 8,
        status: "in_progress",
      }}
    />
    <MatchCard
      match={{
        ...mockMatchData,
        week: 16,
        status: "completed",
      }}
    />
  </div>
);

export const Responsive = () => (
  <div className="p-6">
    <div className="max-w-sm">
      <MatchCard match={mockMatchData} />
    </div>
  </div>
);

export const Interactive = () => (
  <div className="p-6">
    <MatchCard
      match={mockMatchData}
      onClick={() => alert("Navigate to match details")}
      showDetailsButton
    />
  </div>
);
