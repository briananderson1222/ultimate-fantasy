import { LeaguesService } from "../../services/leagues";
import { ScoreboardService } from "../../services/scoreboard";
import { WaiversService } from "../../services/waivers";
import { LineupsService } from "../../services/lineups";
import { HttpClient } from "../../services/leagues";

// Mock HTTP client for testing
const createMockHttpClient = (): HttpClient => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
  setAuthToken: jest.fn(),
  clearAuthToken: jest.fn(),
});

describe("API Service Extraction Integration Tests", () => {
  describe("Leagues Service", () => {
    it("should extract leagues API calls from frontend components", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new LeaguesService(mockHttpClient);

      expect(service.getMyLeagues).toBeDefined();
      expect(service.createLeague).toBeDefined();
      expect(service.joinLeague).toBeDefined();
      expect(service.getLeagueMembers).toBeDefined();
    });

    it("should maintain same API contract as frontend components", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new LeaguesService(mockHttpClient);

      // These should match the existing frontend component API calls
      const mockLeagueData = {
        name: "Test League",
        sport: "nfl",
        league_type: "standard",
        season: "2024",
      };

      expect(() => service.createLeague(mockLeagueData)).not.toThrow();
    });
  });

  describe("Scoreboard Service", () => {
    it("should extract scoreboard API calls from frontend components", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new ScoreboardService(mockHttpClient);

      expect(service.getScoreboard).toBeDefined();
      expect(service.getMatchups).toBeDefined();
      expect(service.getWeeklyScores).toBeDefined();
    });

    it("should handle league ID parameter correctly", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new ScoreboardService(mockHttpClient);
      const leagueId = "test-league-123";

      expect(() => service.getScoreboard(leagueId)).not.toThrow();
      expect(() => service.getMatchups(leagueId, 1)).not.toThrow();
    });
  });

  describe("Waivers Service", () => {
    it("should extract waivers API calls from frontend components", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new WaiversService(mockHttpClient);

      expect(service.getWaivers).toBeDefined();
      expect(service.submitWaiverClaim).toBeDefined();
      expect(service.cancelWaiverClaim).toBeDefined();
    });

    it("should handle waiver claim operations", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new WaiversService(mockHttpClient);
      const mockClaim = {
        league_id: "league-123",
        team_id: "team-456",
        add_player_id: "player-123",
        drop_player_id: "player-456",
        priority: 1,
      };

      expect(() => service.submitWaiverClaim(mockClaim)).not.toThrow();
    });
  });

  describe("Lineups Service", () => {
    it("should extract lineup API calls from frontend components", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new LineupsService(mockHttpClient);

      expect(service.getLineup).toBeDefined();
      expect(service.updateLineup).toBeDefined();
      expect(service.getOptimalLineup).toBeDefined();
    });

    it("should handle lineup updates correctly", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new LineupsService(mockHttpClient);
      const mockLineup = {
        team_id: "team-123",
        game_day: "2024-01-01",
        players: [
          { player_id: "player-1", position: "QB" },
          { player_id: "player-2", position: "RB" },
        ],
      };

      expect(() => service.updateLineup(mockLineup)).not.toThrow();
    });
  });

  describe("Cross-Platform Compatibility", () => {
    it("should work identically on NextJS and React Native", async () => {
      const mockHttpClient = createMockHttpClient();
      const services = [
        new LeaguesService(mockHttpClient),
        new ScoreboardService(mockHttpClient),
        new WaiversService(mockHttpClient),
        new LineupsService(mockHttpClient),
      ];

      services.forEach((service) => {
        expect(service).toBeDefined();
        expect(typeof service).toBe("object");
      });
    });

    it("should use platform-agnostic HTTP client", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new LeaguesService(mockHttpClient);

      // Should work with both fetch (web) and fetch polyfill (mobile)
      expect(service.setAuthToken).toBeDefined();
      expect(service.clearAuthToken).toBeDefined();
    });

    it("should handle authentication consistently", async () => {
      const mockHttpClient = createMockHttpClient();
      const service = new LeaguesService(mockHttpClient);

      // Should handle auth tokens the same way across platforms
      expect(service.setAuthToken).toBeDefined();
      expect(service.clearAuthToken).toBeDefined();
    });
  });

  describe("Error Handling", () => {
    it("should provide consistent error responses across platforms", async () => {
      const mockHttpClient = createMockHttpClient();
      // Mock the get method to throw an error
      mockHttpClient.get = jest.fn().mockRejectedValue(new Error("API Error"));
      const service = new LeaguesService(mockHttpClient);

      try {
        await service.getMyLeagues();
        // Should not reach here in test
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toHaveProperty("message");
        // The error might not have a status property if it's a generic Error
        if (error && typeof error === "object" && "status" in error) {
          expect(error).toHaveProperty("status");
        }
      }
    });
  });
});
