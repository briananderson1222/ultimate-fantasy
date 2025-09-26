"use client";

import React from "react";
import {
  Card,
  Button,
  ProgressBar,
  Avatar,
  Badge,
  MatchCard,
  PlayerCard,
  TrendingPlayers,
  SettingsGrid,
  LeagueChat,
  useTheme,
} from "../../components/design-system";
import { Settings, Plus, Trophy } from "lucide-react";

const mockMatch = {
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

const mockPlayer = {
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
    interceptions: 0,
  },
  injury: null,
  status: "active" as const,
};

const mockTrendingPlayers = [
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
];

const mockSettings = [
  {
    id: "scoring",
    title: "Scoring System",
    description: "Configure how points are awarded",
    value: "Standard",
    type: "select" as const,
    options: ["Standard", "PPR", "Half PPR", "Custom"],
  },
  {
    id: "roster_size",
    title: "Roster Size",
    description: "Number of players per team",
    value: "16",
    type: "number" as const,
    min: 12,
    max: 20,
  },
];

const mockMessages = [
  {
    id: "1",
    userId: "user1",
    username: "FantasyGuru",
    message: "Anyone want to trade for a WR? I need RB depth",
    timestamp: new Date("2024-01-15T10:30:00"),
    type: "message" as const,
  },
  {
    id: "2",
    userId: "system",
    username: "System",
    message: "John Doe claimed Gus Edwards off waivers",
    timestamp: new Date("2024-01-15T09:15:00"),
    type: "transaction" as const,
    transactionData: {
      type: "waiver_claim" as const,
      player: "Gus Edwards",
      team: "Team Warriors",
    },
  },
];

export default function DesignSystemPage() {
  const { theme, setTheme } = useTheme();

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Design System Showcase</h1>
          <div className="flex items-center gap-2">
            <Button
              variant={theme === "light" ? "primary" : "secondary"}
              onClick={() => setTheme("light")}
              size="sm"
            >
              Light
            </Button>
            <Button
              variant={theme === "dark" ? "primary" : "secondary"}
              onClick={() => setTheme("dark")}
              size="sm"
            >
              Dark
            </Button>
          </div>
        </div>

        {/* Primitives Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Primitive Components</h2>

          {/* Buttons */}
          <Card>
            <Card.Header>
              <Card.Title>Buttons</Card.Title>
              <Card.Description>Various button styles and states</Card.Description>
            </Card.Header>
            <Card.Content>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="destructive">Destructive</Button>
                </div>
                <div className="flex gap-4">
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                </div>
                <div className="flex gap-4">
                  <Button leftIcon={<Plus className="h-4 w-4" />}>With Icon</Button>
                  <Button loading>Loading</Button>
                  <Button disabled>Disabled</Button>
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Progress Bars */}
          <Card>
            <Card.Header>
              <Card.Title>Progress Bars</Card.Title>
              <Card.Description>Progress indicators for stats and completion</Card.Description>
            </Card.Header>
            <Card.Content>
              <div className="space-y-4">
                <div>
                  <div className="mb-2 text-sm font-medium">Win Percentage (75%)</div>
                  <ProgressBar value={75} max={100} variant="success" />
                </div>
                <div>
                  <div className="mb-2 text-sm font-medium">Season Progress (8/14 weeks)</div>
                  <ProgressBar value={8} max={14} />
                </div>
                <div>
                  <div className="mb-2 text-sm font-medium">Injury Risk (25%)</div>
                  <ProgressBar value={25} max={100} variant="warning" />
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Avatars & Badges */}
          <Card>
            <Card.Header>
              <Card.Title>Avatars & Badges</Card.Title>
              <Card.Description>User avatars and status indicators</Card.Description>
            </Card.Header>
            <Card.Content>
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <Avatar size="sm" fallback="JD" />
                  <Avatar size="md" fallback="JS" />
                  <Avatar size="lg" fallback="AB" />
                  <Avatar size="xl" fallback="CD" />
                </div>
                <div className="flex gap-2">
                  <Badge variant="success">Active</Badge>
                  <Badge variant="warning">Questionable</Badge>
                  <Badge variant="error">Injured</Badge>
                  <Badge variant="info">Bye Week</Badge>
                </div>
              </div>
            </Card.Content>
          </Card>
        </section>

        {/* Pattern Components */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Pattern Components</h2>

          {/* Match Card */}
          <div>
            <h3 className="text-lg font-medium mb-4">Match Card</h3>
            <div className="max-w-md">
              <MatchCard match={mockMatch} />
            </div>
          </div>

          {/* Player Card */}
          <div>
            <h3 className="text-lg font-medium mb-4">Player Card</h3>
            <div className="max-w-md">
              <PlayerCard player={mockPlayer} />
            </div>
          </div>

          {/* Trending Players */}
          <div>
            <h3 className="text-lg font-medium mb-4">Trending Players</h3>
            <div className="max-w-2xl">
              <TrendingPlayers players={mockTrendingPlayers} />
            </div>
          </div>

          {/* Settings Grid */}
          <div>
            <h3 className="text-lg font-medium mb-4">Settings Grid</h3>
            <div className="max-w-2xl">
              <SettingsGrid settings={mockSettings} />
            </div>
          </div>

          {/* League Chat */}
          <div>
            <h3 className="text-lg font-medium mb-4">League Chat</h3>
            <div className="max-w-2xl h-96">
              <LeagueChat
                messages={mockMessages}
                showComposer
                onSendMessage={(message) => console.log("Message:", message)}
              />
            </div>
          </div>
        </section>

        {/* Grid Layout Example */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Layout Example</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <Card.Header>
                <div className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  <Card.Title>My Teams</Card.Title>
                </div>
              </Card.Header>
              <Card.Content>
                <div className="text-2xl font-bold">8</div>
                <p className="text-muted-foreground">Active leagues</p>
              </Card.Content>
            </Card>

            <Card>
              <Card.Header>
                <Card.Title>Win Rate</Card.Title>
              </Card.Header>
              <Card.Content>
                <div className="text-2xl font-bold text-green-600">72%</div>
                <p className="text-muted-foreground">This season</p>
                <div className="mt-2">
                  <ProgressBar value={72} max={100} variant="success" size="sm" />
                </div>
              </Card.Content>
            </Card>

            <Card>
              <Card.Header>
                <Card.Title>Recent Activity</Card.Title>
              </Card.Header>
              <Card.Content>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Trade completed</span>
                    <span className="text-muted-foreground">2h ago</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Waiver claim</span>
                    <span className="text-muted-foreground">1d ago</span>
                  </div>
                </div>
              </Card.Content>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
}
