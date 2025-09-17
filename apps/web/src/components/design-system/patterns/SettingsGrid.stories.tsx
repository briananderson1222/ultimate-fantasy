import React from "react";
import { SettingsGrid } from "./SettingsGrid";

export default { title: "Design System/Patterns/SettingsGrid" };

const mockSettings = [
  {
    id: "scoring",
    title: "Scoring System",
    description: "Configure how points are awarded",
    value: "Standard",
    type: "select" as const,
    options: ["Standard", "PPR", "Half PPR", "Custom"]
  },
  {
    id: "roster_size",
    title: "Roster Size",
    description: "Number of players per team",
    value: "16",
    type: "number" as const,
    min: 12,
    max: 20
  },
  {
    id: "waiver_type",
    title: "Waiver System",
    description: "How waiver claims are processed",
    value: "FAAB",
    type: "select" as const,
    options: ["FAAB", "Rolling Waivers", "Reverse Standings"]
  },
  {
    id: "trade_deadline",
    title: "Trade Deadline",
    description: "Last day trades can be made",
    value: "2024-11-15",
    type: "date" as const
  },
  {
    id: "auto_draft",
    title: "Auto Draft",
    description: "Automatically draft if owner is absent",
    value: true,
    type: "boolean" as const
  }
];

export const Default = () => (
  <div className="p-6">
    <SettingsGrid settings={mockSettings} />
  </div>
);

export const ReadOnly = () => (
  <div className="p-6">
    <SettingsGrid settings={mockSettings} readOnly />
  </div>
);

export const WithCategories = () => (
  <div className="p-6">
    <SettingsGrid
      settings={[
        {
          category: "Draft Settings",
          items: [
            {
              id: "draft_type",
              title: "Draft Type",
              description: "How the draft is conducted",
              value: "Snake",
              type: "select",
              options: ["Snake", "Auction", "Linear"]
            },
            {
              id: "draft_time",
              title: "Draft Date",
              description: "When the draft takes place",
              value: "2024-08-25T19:00:00",
              type: "datetime"
            }
          ]
        },
        {
          category: "Regular Season",
          items: [
            {
              id: "regular_weeks",
              title: "Regular Season Length",
              description: "Number of weeks in regular season",
              value: "14",
              type: "number",
              min: 10,
              max: 17
            },
            {
              id: "playoff_teams",
              title: "Playoff Teams",
              description: "Teams that make playoffs",
              value: "6",
              type: "select",
              options: ["4", "6", "8"]
            }
          ]
        }
      ]}
    />
  </div>
);

export const Interactive = () => (
  <div className="p-6">
    <SettingsGrid
      settings={mockSettings}
      onChange={(settingId, value) => {
        console.log("Setting changed:", settingId, value);
        alert(`Changed ${settingId} to ${value}`);
      }}
    />
  </div>
);

export const ValidationErrors = () => (
  <div className="p-6">
    <SettingsGrid
      settings={mockSettings.map(setting => ({
        ...setting,
        error: setting.id === "roster_size" ? "Must be between 12 and 20" : undefined
      }))}
    />
  </div>
);

export const CompactLayout = () => (
  <div className="p-6">
    <SettingsGrid settings={mockSettings} variant="compact" />
  </div>
);

export const CustomActions = () => (
  <div className="p-6">
    <SettingsGrid
      settings={mockSettings}
      actions={[
        { label: "Reset to Default", action: () => alert("Reset settings") },
        { label: "Import Settings", action: () => alert("Import settings") },
        { label: "Export Settings", action: () => alert("Export settings") }
      ]}
    />
  </div>
);