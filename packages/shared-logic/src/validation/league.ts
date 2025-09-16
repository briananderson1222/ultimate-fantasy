import { z } from 'zod';

// League settings validation schemas
export const DraftSettingsSchema = z.object({
  draft_type: z.enum(['snake', 'auction', 'linear']),
  draft_order: z.array(z.string()).optional(),
  seconds_per_pick: z.number().min(10).max(300).default(90),
  randomize_order: z.boolean().default(true),
  reversal_round: z.number().min(1).optional(),
  nomination_timer: z.number().min(10).max(120).default(30) // for auction
});

export const ScoringSettingsSchema = z.object({
  scoring_type: z.enum(['standard', 'ppr', 'half_ppr', 'super_flex', 'idp', 'best_ball']),
  pass_td: z.number().default(4),
  pass_yd: z.number().default(0.04), // 1 point per 25 yards
  pass_int: z.number().default(-2),
  rush_yd: z.number().default(0.1), // 1 point per 10 yards
  rush_td: z.number().default(6),
  rec: z.number().default(0), // PPR value
  rec_yd: z.number().default(0.1), // 1 point per 10 yards
  rec_td: z.number().default(6),
  fumble: z.number().default(-2),
  bonus_rec_yd: z.number().default(0), // Bonus for 100+ yards
  bonus_rush_yd: z.number().default(0), // Bonus for 100+ yards
  bonus_pass_yd: z.number().default(0) // Bonus for 300+ yards
});

export const RosterSettingsSchema = z.object({
  roster_positions: z.array(z.enum([
    'QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPER_FLEX', 'K', 'DEF', 'D/ST',
    'DL', 'LB', 'DB', 'IDP_FLEX', 'BN'
  ])),
  total_roster_spots: z.number().min(10).max(30).default(16),
  bench_spots: z.number().min(4).max(10).default(6),
  ir_spots: z.number().min(0).max(5).default(1),
  taxi_spots: z.number().min(0).max(5).default(0) // For dynasty
});

export const PlayoffSettingsSchema = z.object({
  playoff_teams: z.number().min(2).max(12).default(6),
  playoff_weeks: z.array(z.number()).default([15, 16, 17]),
  playoff_type: z.enum(['standard', 'bracket', 'toilet']).default('standard'),
  playoff_seed_type: z.enum(['record', 'points_for', 'head_to_head']).default('record'),
  consolation_bracket: z.boolean().default(true)
});

export const WaiverSettingsSchema = z.object({
  waiver_type: z.enum(['rolling_list', 'faab', 'continuous', 'none']),
  waiver_day_of_week: z.number().min(0).max(6).default(3), // Wednesday
  waiver_hour: z.number().min(0).max(23).default(10), // 10 AM
  waiver_clear_days: z.number().min(1).max(3).default(2),
  faab_budget: z.number().min(0).max(1000).default(100),
  minimum_bid: z.number().min(0).max(10).default(0),
  waiver_budget_type: z.enum(['season_long', 'weekly_reset']).default('season_long')
});

export const TradeSettingsSchema = z.object({
  trade_deadline: z.number().min(1).max(18).default(10), // Week number
  trade_review_days: z.number().min(0).max(3).default(1),
  trade_review_type: z.enum(['none', 'league_vote', 'commissioner']).default('league_vote'),
  votes_to_veto: z.number().min(1).max(12).default(4),
  allow_trading_draft_picks: z.boolean().default(false), // For dynasty
  max_keepers: z.number().min(0).max(10).default(0) // For keeper leagues
});

// Main league validation schema
export const LeagueSettingsSchema = z.object({
  draft: DraftSettingsSchema.optional(),
  scoring: ScoringSettingsSchema,
  roster: RosterSettingsSchema,
  playoff: PlayoffSettingsSchema.optional(),
  waiver: WaiverSettingsSchema.optional(),
  trade: TradeSettingsSchema.optional()
});

export const LeagueSchema = z.object({
  league_id: z.string().optional(), // Optional for creation
  name: z.string().min(1).max(50, 'League name must be 50 characters or less'),
  description: z.string().max(500, 'Description must be 500 characters or less').optional(),
  avatar: z.string().url().optional(),
  season: z.string().regex(/^\d{4}$/, 'Season must be a 4-digit year'),
  season_type: z.enum(['regular', 'playoff', 'dynasty', 'keeper']).default('regular'),
  sport: z.enum(['nfl', 'nba', 'mlb', 'nhl']).default('nfl'),
  status: z.enum(['pre_draft', 'drafting', 'active', 'complete', 'archived']).default('pre_draft'),
  total_rosters: z.number().min(2).max(20, 'League must have between 2 and 20 teams'),
  settings: LeagueSettingsSchema,
  commissioner_id: z.string().optional(),
  created_at: z.date().optional(),
  updated_at: z.date().optional(),
  draft_id: z.string().optional(),
  previous_league_id: z.string().optional(), // For dynasty/keeper continuation
  public: z.boolean().default(false),
  password: z.string().min(4).max(20).optional(), // For password-protected leagues
  entry_fee: z.number().min(0).max(1000).default(0),
  payout_structure: z.array(z.object({
    position: z.number(),
    amount: z.number(),
    percentage: z.number().min(0).max(100).optional()
  })).optional()
});

// League creation specific schema (stricter requirements)
export const CreateLeagueSchema = LeagueSchema.extend({
  name: z.string().min(3, 'League name must be at least 3 characters').max(50),
  total_rosters: z.number().min(4, 'League must have at least 4 teams').max(20),
  settings: LeagueSettingsSchema.required()
});

// League update schema (all fields optional except ID)
export const UpdateLeagueSchema = LeagueSchema.partial().extend({
  league_id: z.string().min(1, 'League ID is required for updates')
});

// League search/filter schema
export const LeagueFilterSchema = z.object({
  name: z.string().optional(),
  season: z.string().optional(),
  status: z.array(z.enum(['pre_draft', 'drafting', 'active', 'complete', 'archived'])).optional(),
  total_rosters: z.object({
    min: z.number().optional(),
    max: z.number().optional()
  }).optional(),
  scoring_type: z.array(z.enum(['standard', 'ppr', 'half_ppr', 'super_flex', 'idp', 'best_ball'])).optional(),
  draft_type: z.array(z.enum(['snake', 'auction', 'linear'])).optional(),
  public: z.boolean().optional(),
  has_entry_fee: z.boolean().optional(),
  created_after: z.date().optional(),
  created_before: z.date().optional()
});

// League join request schema
export const JoinLeagueSchema = z.object({
  league_id: z.string().min(1, 'League ID is required'),
  password: z.string().optional(),
  team_name: z.string().min(1).max(30, 'Team name must be 30 characters or less').optional(),
  user_id: z.string().min(1, 'User ID is required')
});

// TypeScript types
export type DraftSettings = z.infer<typeof DraftSettingsSchema>;
export type ScoringSettings = z.infer<typeof ScoringSettingsSchema>;
export type RosterSettings = z.infer<typeof RosterSettingsSchema>;
export type PlayoffSettings = z.infer<typeof PlayoffSettingsSchema>;
export type WaiverSettings = z.infer<typeof WaiverSettingsSchema>;
export type TradeSettings = z.infer<typeof TradeSettingsSchema>;
export type LeagueSettings = z.infer<typeof LeagueSettingsSchema>;
export type League = z.infer<typeof LeagueSchema>;
export type CreateLeague = z.infer<typeof CreateLeagueSchema>;
export type UpdateLeague = z.infer<typeof UpdateLeagueSchema>;
export type LeagueFilter = z.infer<typeof LeagueFilterSchema>;
export type JoinLeague = z.infer<typeof JoinLeagueSchema>;

// Validation functions
export const leagueValidation = {
  // Validate league data
  validateLeague: (data: unknown): League => {
    return LeagueSchema.parse(data);
  },

  // Validate league creation data
  validateCreateLeague: (data: unknown): CreateLeague => {
    return CreateLeagueSchema.parse(data);
  },

  // Validate league update data
  validateUpdateLeague: (data: unknown): UpdateLeague => {
    return UpdateLeagueSchema.parse(data);
  },

  // Validate league filter data
  validateLeagueFilter: (data: unknown): LeagueFilter => {
    return LeagueFilterSchema.parse(data);
  },

  // Validate join league request
  validateJoinLeague: (data: unknown): JoinLeague => {
    return JoinLeagueSchema.parse(data);
  },

  // Custom validation functions
  isValidRosterConfiguration: (settings: RosterSettings): boolean => {
    const totalPositions = settings.roster_positions.length;
    const benchSpots = settings.bench_spots;
    const totalSpots = totalPositions + benchSpots;

    return totalSpots <= settings.total_roster_spots;
  },

  isValidPlayoffConfiguration: (settings: PlayoffSettings, totalTeams: number): boolean => {
    return settings.playoff_teams <= totalTeams && settings.playoff_teams >= 2;
  },

  isValidDraftConfiguration: (draft: DraftSettings, totalTeams: number): boolean => {
    if (draft.draft_order && draft.draft_order.length !== totalTeams) {
      return false;
    }
    return true;
  },

  isValidPayoutStructure: (payouts: League['payout_structure'], entryFee: number, totalTeams: number): boolean => {
    if (!payouts || entryFee === 0) return true;

    const totalPayout = payouts.reduce((sum, payout) => sum + payout.amount, 0);
    const totalPrizePool = entryFee * totalTeams;

    // Allow for small rounding differences
    return Math.abs(totalPayout - totalPrizePool) < 0.01;
  },

  // Get default settings for league type
  getDefaultSettings: (
    leagueType: 'standard' | 'ppr' | 'dynasty' | 'superflex' = 'standard'
  ): LeagueSettings => {
    const baseSettings: LeagueSettings = {
      scoring: {
        scoring_type: 'standard',
        pass_td: 4,
        pass_yd: 0.04,
        pass_int: -2,
        rush_yd: 0.1,
        rush_td: 6,
        rec: 0,
        rec_yd: 0.1,
        rec_td: 6,
        fumble: -2,
        bonus_rec_yd: 0,
        bonus_rush_yd: 0,
        bonus_pass_yd: 0
      },
      roster: {
        roster_positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'D/ST', 'K'],
        total_roster_spots: 16,
        bench_spots: 6,
        ir_spots: 1,
        taxi_spots: 0
      }
    };

    // Modify based on league type
    switch (leagueType) {
      case 'ppr':
        baseSettings.scoring.scoring_type = 'ppr';
        baseSettings.scoring.rec = 1;
        break;
      case 'dynasty':
        baseSettings.roster.taxi_spots = 3;
        baseSettings.roster.total_roster_spots = 25;
        baseSettings.roster.bench_spots = 13;
        break;
      case 'superflex':
        baseSettings.scoring.scoring_type = 'super_flex';
        baseSettings.roster.roster_positions = ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'SUPER_FLEX', 'D/ST', 'K'];
        break;
    }

    return baseSettings;
  }
};