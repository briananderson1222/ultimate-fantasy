import React from "react";
import { Card } from "./Card";
import { Trophy, Users, Calendar, TrendingUp } from "lucide-react";

export default { title: "Design System/Primitives/Card" };

export const Default = () => (
  <div className="p-6">
    <Card>
      <div className="p-4">
        <h3 className="text-lg font-semibold">Default Card</h3>
        <p className="text-gray-600">This is a basic card with default styling.</p>
      </div>
    </Card>
  </div>
);

export const Variants = () => (
  <div className="p-6 space-y-4">
    <Card variant="default">
      <div className="p-4">
        <h3 className="font-semibold">Default Card</h3>
        <p className="text-gray-600">Standard card styling</p>
      </div>
    </Card>
    <Card variant="outlined">
      <div className="p-4">
        <h3 className="font-semibold">Outlined Card</h3>
        <p className="text-gray-600">Card with visible border</p>
      </div>
    </Card>
    <Card variant="elevated">
      <div className="p-4">
        <h3 className="font-semibold">Elevated Card</h3>
        <p className="text-gray-600">Card with elevated shadow</p>
      </div>
    </Card>
    <Card variant="flat">
      <div className="p-4">
        <h3 className="font-semibold">Flat Card</h3>
        <p className="text-gray-600">Card with no shadow or border</p>
      </div>
    </Card>
  </div>
);

export const Interactive = () => (
  <div className="p-6 space-y-4">
    <Card clickable>
      <div className="p-4">
        <h3 className="font-semibold">Clickable Card</h3>
        <p className="text-gray-600">This card responds to hover and click</p>
      </div>
    </Card>
    <Card clickable variant="outlined">
      <div className="p-4">
        <h3 className="font-semibold">Clickable Outlined</h3>
        <p className="text-gray-600">Outlined card with interactions</p>
      </div>
    </Card>
  </div>
);

export const WithHeader = () => (
  <div className="p-6">
    <Card>
      <Card.Header>
        <div className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <h3 className="font-semibold">League Standings</h3>
        </div>
      </Card.Header>
      <Card.Content>
        <p>Your team is currently in 3rd place with a 7-5 record.</p>
      </Card.Content>
    </Card>
  </div>
);

export const WithFooter = () => (
  <div className="p-6">
    <Card>
      <Card.Header>
        <h3 className="font-semibold">Weekly Matchup</h3>
      </Card.Header>
      <Card.Content>
        <p>You're facing the league champion this week. Good luck!</p>
      </Card.Content>
      <Card.Footer>
        <button className="text-blue-600 text-sm hover:underline">
          View Full Matchup
        </button>
      </Card.Footer>
    </Card>
  </div>
);

export const FantasySportsCards = () => (
  <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <Card variant="elevated">
      <Card.Header>
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold">My Teams</h3>
        </div>
      </Card.Header>
      <Card.Content>
        <div className="text-2xl font-bold">8</div>
        <p className="text-gray-600">Active leagues</p>
      </Card.Content>
    </Card>

    <Card variant="elevated">
      <Card.Header>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-green-500" />
          <h3 className="font-semibold">Win Rate</h3>
        </div>
      </Card.Header>
      <Card.Content>
        <div className="text-2xl font-bold text-green-600">72%</div>
        <p className="text-gray-600">This season</p>
      </Card.Content>
    </Card>

    <Card variant="elevated">
      <Card.Header>
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-purple-500" />
          <h3 className="font-semibold">Next Game</h3>
        </div>
      </Card.Header>
      <Card.Content>
        <div className="text-lg font-semibold">Sunday 1:00 PM</div>
        <p className="text-gray-600">vs. Team Rocket</p>
      </Card.Content>
    </Card>
  </div>
);

export const CompactCards = () => (
  <div className="p-6 space-y-2">
    <Card variant="flat" className="p-3">
      <div className="flex justify-between items-center">
        <span className="font-medium">Patrick Mahomes</span>
        <span className="text-green-600">+24.5</span>
      </div>
    </Card>
    <Card variant="flat" className="p-3">
      <div className="flex justify-between items-center">
        <span className="font-medium">Travis Kelce</span>
        <span className="text-green-600">+18.2</span>
      </div>
    </Card>
    <Card variant="flat" className="p-3">
      <div className="flex justify-between items-center">
        <span className="font-medium">Tyreek Hill</span>
        <span className="text-red-600">+8.1</span>
      </div>
    </Card>
  </div>
);