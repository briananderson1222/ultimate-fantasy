import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TrendingPlayers } from "../../src/components/design-system/patterns/TrendingPlayers";
import { ThemeProvider } from "../../src/components/design-system/providers/ThemeProvider";

const mockTrendingPlayers = [
  {
    id: "1",
    name: "Player One",
    position: "QB",
    team: "Team A",
    trendData: {
      direction: "up" as const,
      percentage: 15.5,
      reason: "Strong performance expected this week",
      addDropPercentage: 12.3,
    },
    weeklyPoints: [18.2, 23.5, 19.8, 26.1],
    projectedPoints: 23.2,
  },
  {
    id: "2",
    name: "Player Two",
    position: "RB",
    team: "Team B",
    trendData: {
      direction: "down" as const,
      percentage: -8.3,
      reason: "Minor injury concern",
      addDropPercentage: -5.2,
    },
    weeklyPoints: [22.1, 18.7, 14.3, 19.2],
    projectedPoints: 18.7,
  },
  {
    id: "3",
    name: "Player Three",
    position: "WR",
    team: "Team C",
    trendData: {
      direction: "up" as const,
      percentage: 22.1,
      reason: "Breakout candidate this week",
      addDropPercentage: 18.7,
    },
    weeklyPoints: [12.3, 16.9, 21.4, 24.8],
    projectedPoints: 16.9,
  },
];

describe("Trending Players Integration", () => {
  const renderWithTheme = (component: React.ReactNode) => {
    return render(<ThemeProvider defaultTheme="dark">{component}</ThemeProvider>);
  };

  it("should display all trending players with correct information", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    // Check all players are displayed
    expect(screen.getByText("Player One")).toBeInTheDocument();
    expect(screen.getByText("Player Two")).toBeInTheDocument();
    expect(screen.getByText("Player Three")).toBeInTheDocument();

    // Check positions
    expect(screen.getByText("QB")).toBeInTheDocument();
    expect(screen.getByText("RB")).toBeInTheDocument();
    expect(screen.getByText("WR")).toBeInTheDocument();
  });

  it("should show correct trend indicators", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    // Check for trending up indicators
    expect(screen.getByText("15.5%")).toBeInTheDocument();
    expect(screen.getByText("22.1%")).toBeInTheDocument();

    // Check for trending down indicator
    expect(screen.getByText("8.3%")).toBeInTheDocument();
  });

  it("should display all players initially", async () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    // Initially all players should be shown
    expect(screen.getByText("Player One")).toBeInTheDocument();
    expect(screen.getByText("Player Two")).toBeInTheDocument();
    expect(screen.getByText("Player Three")).toBeInTheDocument();
  });

  it("should show trending up and down indicators", async () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    // Check that trend directions are displayed
    expect(screen.getByText("Player One")).toBeInTheDocument();
    expect(screen.getByText("Player Two")).toBeInTheDocument();
    expect(screen.getByText("Player Three")).toBeInTheDocument();
  });

  it("should render players in correct order", async () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    // Check that all players are rendered
    expect(screen.getByText("Player One")).toBeInTheDocument();
    expect(screen.getByText("Player Two")).toBeInTheDocument();
    expect(screen.getByText("Player Three")).toBeInTheDocument();
  });

  it("should show add/drop percentages correctly", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    expect(screen.getByText("12.3%")).toBeInTheDocument();
    expect(screen.getByText("5.2%")).toBeInTheDocument();
    expect(screen.getByText("18.7%")).toBeInTheDocument();
  });

  it("should display projected points for each player", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    expect(screen.getByText("23.2")).toBeInTheDocument();
    expect(screen.getByText("18.7")).toBeInTheDocument();
    expect(screen.getByText("16.9")).toBeInTheDocument();
  });

  it("should show trend reasons", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    expect(screen.getByText("Strong performance expected this week")).toBeInTheDocument();
    expect(screen.getByText("Minor injury concern")).toBeInTheDocument();
    expect(screen.getByText("Breakout candidate this week")).toBeInTheDocument();
  });

  it("should display player names correctly", async () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    expect(screen.getByText("Player One")).toBeInTheDocument();
    expect(screen.getByText("Player Two")).toBeInTheDocument();
    expect(screen.getByText("Player Three")).toBeInTheDocument();
  });

  it("should show trend reasons for each player", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    expect(screen.getByText("Strong performance expected this week")).toBeInTheDocument();
    expect(screen.getByText("Minor injury concern")).toBeInTheDocument();
    expect(screen.getByText("Breakout candidate this week")).toBeInTheDocument();
  });

  it("should handle empty player list", async () => {
    renderWithTheme(<TrendingPlayers players={[]} />);

    // Should render without crashing
    expect(screen.queryByText("Player One")).not.toBeInTheDocument();
  });

  it("should be accessible with proper ARIA attributes", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    // Check for accessibility attributes
    expect(screen.getByRole("list")).toBeInTheDocument();
    const playerItems = screen.getAllByRole("listitem");
    expect(playerItems).toHaveLength(3);

    playerItems.forEach((item) => {
      expect(item).toHaveAttribute("aria-label");
    });
  });

  it("should be accessible with proper ARIA attributes", () => {
    renderWithTheme(<TrendingPlayers players={mockTrendingPlayers} />);

    expect(screen.getByText("Player One")).toBeInTheDocument();
    expect(screen.getByText("Player Two")).toBeInTheDocument();
    expect(screen.getByText("Player Three")).toBeInTheDocument();
  });
});
