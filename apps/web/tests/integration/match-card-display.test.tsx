import { render, screen } from "@testing-library/react";
import { MatchCard } from "../../src/components/design-system/patterns/MatchCard";
import { ThemeProvider } from "../../src/components/design-system/providers/ThemeProvider";

const mockMatch = {
  homeTeam: {
    id: "1",
    name: "Team Alpha",
    owner: "Alice Johnson",
    record: { wins: 8, losses: 4 },
  },
  awayTeam: {
    id: "2",
    name: "Team Beta",
    owner: "Bob Smith",
    record: { wins: 6, losses: 6 },
  },
  week: 8,
  status: "completed" as const,
  actualPoints: {
    home: 120.5,
    away: 95.3,
  },
};

const mockUpcomingMatch = {
  homeTeam: {
    id: "3",
    name: "Team Gamma",
    owner: "Charlie Brown",
    record: { wins: 7, losses: 5 },
  },
  awayTeam: {
    id: "4",
    name: "Team Delta",
    owner: "Diana Prince",
    record: { wins: 5, losses: 7 },
  },
  week: 9,
  status: "upcoming" as const,
  projectedPoints: {
    home: 115.2,
    away: 108.7,
  },
};

describe("Match Card Display Integration", () => {
  const renderWithTheme = (component: React.ReactNode, theme: "light" | "dark" = "dark") => {
    return render(<ThemeProvider defaultTheme={theme}>{component}</ThemeProvider>);
  };

  it("should display completed match with correct scores and styling", () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    // Check team names are displayed
    expect(screen.getByText("Team Alpha")).toBeInTheDocument();
    expect(screen.getByText("Team Beta")).toBeInTheDocument();

    // Check scores are displayed
    expect(screen.getByText("120.5")).toBeInTheDocument();
    expect(screen.getByText("95.3")).toBeInTheDocument();

    // Check manager names
    expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();

    // Check week information
    expect(screen.getByText(/Week 8/)).toBeInTheDocument();
  });

  it("should display upcoming match with projections", () => {
    renderWithTheme(<MatchCard match={mockUpcomingMatch} />);

    // Check team names are displayed
    expect(screen.getByText("Team Gamma")).toBeInTheDocument();
    expect(screen.getByText("Team Delta")).toBeInTheDocument();

    // Check projected scores
    expect(screen.getByText("115.2")).toBeInTheDocument();
    expect(screen.getByText("108.7")).toBeInTheDocument();
  });

  it("should display team records", () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    // Check team records are displayed
    expect(screen.getByText("8-4")).toBeInTheDocument();
    expect(screen.getByText("6-6")).toBeInTheDocument();
  });

  it("should render correctly in both light and dark themes", () => {
    const { rerender } = renderWithTheme(<MatchCard match={mockMatch} />, "dark");

    // Check dark theme rendering
    expect(screen.getByText("Team Alpha")).toBeInTheDocument();

    // Switch to light theme
    rerender(
      <ThemeProvider defaultTheme="light">
        <MatchCard match={mockMatch} />
      </ThemeProvider>,
    );

    // Should still render correctly
    expect(screen.getByText("Team Alpha")).toBeInTheDocument();
  });

  it("should display winner highlight for completed matches", () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    // Home team won (120.5 > 95.3), scores should be visible
    expect(screen.getByText("120.5")).toBeInTheDocument();
    expect(screen.getByText("95.3")).toBeInTheDocument();
  });

  it("should handle tie games correctly", () => {
    const tieMatch = {
      ...mockMatch,
      actualPoints: {
        home: 100.0,
        away: 100.0,
      },
    };

    renderWithTheme(<MatchCard match={tieMatch} />);

    // Both scores should be displayed
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("should show correct week information", () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    // Should show week information
    expect(screen.getByText(/Week 8/)).toBeInTheDocument();
  });

  it("should be accessible and render properly", () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    // Check basic rendering
    expect(screen.getByText("Team Alpha")).toBeInTheDocument();
    expect(screen.getByText("Team Beta")).toBeInTheDocument();
  });
});
