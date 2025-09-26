import React from "react";
import { LeagueChat } from "./LeagueChat";

export default { title: "Design System/Patterns/LeagueChat" };

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
  {
    id: "3",
    userId: "user2",
    username: "Commissioner",
    message: "Reminder: Trade deadline is this Friday!",
    timestamp: new Date("2024-01-15T08:45:00"),
    type: "announcement" as const,
  },
  {
    id: "4",
    userId: "user3",
    username: "TeamRocket",
    message: "Looking good for playoffs! 💪",
    timestamp: new Date("2024-01-15T08:20:00"),
    type: "message" as const,
  },
  {
    id: "5",
    userId: "system",
    username: "System",
    message: "Trade completed: Mike Evans for Josh Jacobs",
    timestamp: new Date("2024-01-15T07:55:00"),
    type: "transaction" as const,
    transactionData: {
      type: "trade" as const,
      fromTeam: "Team Alpha",
      toTeam: "Team Beta",
      fromPlayer: "Mike Evans",
      toPlayer: "Josh Jacobs",
    },
  },
];

export const Default = () => (
  <div className="p-6 h-96">
    <LeagueChat messages={mockMessages} />
  </div>
);

export const WithComposer = () => (
  <div className="p-6 h-96">
    <LeagueChat
      messages={mockMessages}
      showComposer
      onSendMessage={(message) => alert(`Sending: ${message}`)}
    />
  </div>
);

export const MessageTypes = () => (
  <div className="p-6 h-96">
    <LeagueChat
      messages={[
        {
          id: "1",
          userId: "user1",
          username: "Player1",
          message: "Regular chat message",
          timestamp: new Date(),
          type: "message",
        },
        {
          id: "2",
          userId: "system",
          username: "System",
          message: "Trade notification",
          timestamp: new Date(),
          type: "transaction",
        },
        {
          id: "3",
          userId: "user2",
          username: "Commissioner",
          message: "Important announcement",
          timestamp: new Date(),
          type: "announcement",
        },
      ]}
    />
  </div>
);

export const LongConversation = () => {
  const longMessages = Array.from({ length: 50 }, (_, i) => ({
    id: `msg-${i}`,
    userId: `user${i % 5}`,
    username: `Player${i % 5}`,
    message: `This is message number ${i + 1} in the chat`,
    timestamp: new Date(Date.now() - i * 300000),
    type: "message" as const,
  }));

  return (
    <div className="p-6 h-96">
      <LeagueChat messages={longMessages} />
    </div>
  );
};

export const RealTimeUpdates = () => (
  <div className="p-6 h-96">
    <LeagueChat
      messages={mockMessages}
      showComposer
      showTypingIndicator
      typingUsers={["FantasyGuru", "TeamRocket"]}
      onSendMessage={(message) => console.log("Message sent:", message)}
    />
  </div>
);

export const CompactMode = () => (
  <div className="p-6 h-64">
    <LeagueChat messages={mockMessages} variant="compact" />
  </div>
);

export const EmptyChat = () => (
  <div className="p-6 h-96">
    <LeagueChat messages={[]} showComposer />
  </div>
);

export const WithMentions = () => (
  <div className="p-6 h-96">
    <LeagueChat
      messages={[
        {
          id: "1",
          userId: "user1",
          username: "Player1",
          message: "Hey @Player2, want to make a trade?",
          timestamp: new Date(),
          type: "message",
          mentions: ["Player2"],
        },
        {
          id: "2",
          userId: "user2",
          username: "Player2",
          message: "@Player1 Sure! What are you thinking?",
          timestamp: new Date(),
          type: "message",
          mentions: ["Player1"],
        },
      ]}
      showComposer
      currentUserId="user2"
    />
  </div>
);

export const TransactionFocus = () => (
  <div className="p-6 h-96">
    <LeagueChat
      messages={mockMessages.filter((m) => m.type === "transaction")}
      showTransactionsOnly
    />
  </div>
);
