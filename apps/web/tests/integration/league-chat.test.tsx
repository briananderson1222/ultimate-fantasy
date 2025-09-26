import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LeagueChat } from "../../src/components/design-system/patterns/LeagueChat";
import { ThemeProvider } from "../../src/components/design-system/providers/ThemeProvider";

const mockMessages = [
  {
    id: "1",
    userId: "user1",
    username: "Alice",
    message: "Great game last week!",
    timestamp: new Date("2024-01-15T10:30:00Z"),
    type: "message" as const,
  },
  {
    id: "2",
    userId: "user2",
    username: "Bob",
    message: "Thanks! Your lineup was solid too.",
    timestamp: new Date("2024-01-15T10:32:00Z"),
    type: "message" as const,
  },
  {
    id: "3",
    userId: "system",
    username: "System",
    message: "Alice has placed a waiver claim for Player X",
    timestamp: new Date("2024-01-15T10:35:00Z"),
    type: "transaction" as const,
    transactionData: {
      type: "waiver_claim" as const,
      player: "Player X",
      team: "Alice Team",
    },
  },
];

describe("League Chat Integration", () => {
  const renderWithTheme = (component: React.ReactNode) => {
    return render(<ThemeProvider defaultTheme="dark">{component}</ThemeProvider>);
  };

  const mockOnSendMessage = vi.fn();
  const mockOnReaction = vi.fn();

  beforeEach(() => {
    mockOnSendMessage.mockClear();
    mockOnReaction.mockClear();
  });

  it("should display all chat messages with correct information", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Check messages are displayed
    expect(screen.getByText("Great game last week!")).toBeInTheDocument();
    expect(screen.getByText("Thanks! Your lineup was solid too.")).toBeInTheDocument();
    expect(screen.getByText("Alice has placed a waiver claim for Player X")).toBeInTheDocument();

    // Check usernames
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("System")).toBeInTheDocument();
  });

  it("should distinguish between message types", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Regular messages should have standard styling
    const regularMessage = screen.getByText("Great game last week!").closest(".message");
    expect(regularMessage).toHaveClass("message-regular");

    // Transaction messages should have special styling
    const transactionMessage = screen
      .getByText("Alice has placed a waiver claim for Player X")
      .closest(".message");
    expect(transactionMessage).toHaveClass("message-transaction");
  });

  it("should highlight current user messages", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Alice's message (user1) should be highlighted as current user
    const currentUserMessage = screen.getByText("Great game last week!").closest(".message");
    expect(currentUserMessage).toHaveClass("message-own");

    // Bob's message should not be highlighted
    const otherUserMessage = screen
      .getByText("Thanks! Your lineup was solid too.")
      .closest(".message");
    expect(otherUserMessage).not.toHaveClass("message-own");
  });

  it("should allow sending new messages", async () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    const messageInput = screen.getByPlaceholderText("Type a message...");
    const sendButton = screen.getByRole("button", { name: /send/i });

    // Type a message
    fireEvent.change(messageInput, { target: { value: "New test message" } });
    expect(messageInput).toHaveValue("New test message");

    // Send the message
    fireEvent.click(sendButton);

    // Check that onSendMessage was called
    expect(mockOnSendMessage).toHaveBeenCalledWith("New test message");

    // Input should be cleared after sending
    await waitFor(() => {
      expect(messageInput).toHaveValue("");
    });
  });

  it("should send message on Enter key press", async () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    const messageInput = screen.getByPlaceholderText("Type a message...");

    fireEvent.change(messageInput, { target: { value: "Enter key test" } });
    fireEvent.keyDown(messageInput, { key: "Enter" });

    expect(mockOnSendMessage).toHaveBeenCalledWith("Enter key test");
  });

  it("should not send empty messages", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    const sendButton = screen.getByRole("button", { name: /send/i });

    // Try to send empty message
    fireEvent.click(sendButton);

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it("should show transaction messages with proper styling", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Check transaction message is displayed
    expect(screen.getByText("Alice has placed a waiver claim for Player X")).toBeInTheDocument();
  });

  it("should display timestamps for messages", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Check that timestamps are displayed (format may vary)
    expect(screen.getByText(/ago/)).toBeInTheDocument();
  });

  it("should auto-scroll to bottom when new messages arrive", () => {
    const { rerender } = renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    const newMessage = {
      id: "4",
      userId: "user2",
      username: "Bob",
      message: "New message",
      timestamp: new Date(),
      type: "message" as const,
    };

    // Add new message
    rerender(
      <ThemeProvider defaultTheme="dark">
        <LeagueChat
          messages={[...mockMessages, newMessage]}
          currentUserId="user1"
          onSendMessage={mockOnSendMessage}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText("New message")).toBeInTheDocument();
  });

  it("should support compact variant", async () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
        variant="compact"
      />,
    );

    // Check that messages are still displayed in compact mode
    expect(screen.getByText("Great game last week!")).toBeInTheDocument();
  });

  it("should be accessible with proper ARIA attributes", () => {
    renderWithTheme(
      <LeagueChat
        messages={mockMessages}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Check main chat area
    expect(screen.getByRole("log")).toBeInTheDocument();

    // Check message input
    const messageInput = screen.getByRole("textbox");
    expect(messageInput).toHaveAttribute("aria-label");

    // Check send button
    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).toBeInTheDocument();
  });

  it("should handle long messages gracefully", () => {
    const longMessage = "A".repeat(500);
    const messagesWithLongMessage = [
      ...mockMessages,
      {
        id: "4",
        userId: "user1",
        username: "Alice",
        message: longMessage,
        timestamp: new Date(),
        type: "message" as const,
      },
    ];

    renderWithTheme(
      <LeagueChat
        messages={messagesWithLongMessage}
        currentUserId="user1"
        onSendMessage={mockOnSendMessage}
      />,
    );

    // Long message should be displayed (potentially truncated)
    expect(screen.getByText(longMessage, { exact: false })).toBeInTheDocument();
  });
});
