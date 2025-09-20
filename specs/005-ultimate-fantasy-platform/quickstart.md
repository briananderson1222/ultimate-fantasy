# Ultimate Fantasy Platform - Quickstart Guide

**Date**: 2025-09-19
**Purpose**: Validate implementation through complete user scenarios

## Prerequisites
- Development environment running (API + Web + Mobile)
- Test database with seed data
- Mock sports data provider configured
- Authentication system enabled

## Scenario 1: Complete League Experience (Web)

### Create and Join League
```bash
# 1. User registration and login
curl -X POST /api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "commissioner@test.com", "password": "password123", "name": "Test Commissioner"}'

# 2. Create MLB league
curl -X POST /api/v1/leagues \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test MLB League",
    "sport": "mlb",
    "league_type": "head_to_head",
    "season": "2025",
    "max_teams": 8,
    "scoring_rules": {"hits": 1, "home_runs": 4, "rbis": 1},
    "draft_settings": {"type": "snake", "pick_timer": 60}
  }'

# 3. Join league with invite code
curl -X POST /api/v1/leagues/$LEAGUE_ID/join \
  -H "Authorization: Bearer $USER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"team_name": "Test Team 2"}'
```

**Expected Results**:
- League created with valid UUID
- Commissioner team automatically created
- Invite code generated and functional
- Second user successfully joins
- League status = 'setup', team count = 2

### Draft Process
```bash
# 4. Start draft (commissioner only)
curl -X POST /api/v1/draft/$LEAGUE_ID \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"draft_type": "snake", "pick_timer": 60}'

# 5. Make first pick
curl -X POST /api/v1/draft/$LEAGUE_ID/pick \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player_id": "$MIKE_TROUT_ID"}'

# 6. Second pick (different user)
curl -X POST /api/v1/draft/$LEAGUE_ID/pick \
  -H "Authorization: Bearer $USER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player_id": "$AARON_JUDGE_ID"}'
```

**Expected Results**:
- Draft status changes to 'active'
- Pick timer starts counting down
- Players correctly assigned to teams
- Snake order reverses after round 1
- Draft board updates in real-time

### Lineup Management
```bash
# 7. Set lineup for week 1
curl -X PUT /api/v1/lineups \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "$TEAM_ID",
    "week": 1,
    "players": [
      {"player_id": "$MIKE_TROUT_ID", "position": "OF"},
      {"player_id": "$VLADIMIR_GUERRERO_ID", "position": "1B"},
      {"player_id": "$JOSE_ALTUVE_ID", "position": "2B"}
    ]
  }'

# 8. Get current lineup
curl -X GET "/api/v1/lineups?team_id=$TEAM_ID&week=1" \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN"
```

**Expected Results**:
- Lineup saved with version number
- Position constraints validated
- Players must be on team roster
- Optimistic locking prevents conflicts

## Scenario 2: Trading and Waivers (Web)

### Trade Proposal
```bash
# 9. Propose trade
curl -X POST /api/v1/trades \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "league_id": "$LEAGUE_ID",
    "receiving_team_id": "$TEAM2_ID",
    "proposed_players": ["$MIKE_TROUT_ID"],
    "requested_players": ["$AARON_JUDGE_ID"],
    "message": "Fair trade for similar value players"
  }'

# 10. Accept trade
curl -X PATCH /api/v1/trades/$TRADE_ID \
  -H "Authorization: Bearer $USER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "accept"}'
```

**Expected Results**:
- Trade evaluation score calculated
- Players swapped between teams
- Trade history recorded
- League notifications sent

### Waiver Claims
```bash
# 11. Place waiver bid
curl -X POST /api/v1/waivers/bids \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "league_id": "$LEAGUE_ID",
    "team_id": "$TEAM_ID",
    "player_id": "$FREE_AGENT_ID",
    "bid_amount": 25,
    "drop_player_id": "$BENCH_PLAYER_ID"
  }'

# 12. Process waivers (system job)
curl -X POST /api/v1/admin/waivers/process \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"league_id": "$LEAGUE_ID"}'
```

**Expected Results**:
- Bid placed with priority order
- Budget deducted from team
- Highest bid wins player
- Dropped player becomes free agent

## Scenario 3: Real-time Features (Web + Mobile)

### WebSocket Connection
```javascript
// 13. Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/api/v1/real-time/connect?league_id=' + leagueId);

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};

// 14. Draft pick notification
// Expected: {"type": "draft_pick", "pick_number": 3, "player": {...}, "team": {...}}

// 15. Score update notification
// Expected: {"type": "score_update", "player_id": "...", "points": 12.5, "stats": {...}}
```

### Mobile App Validation
```bash
# 16. Mobile API calls (same endpoints)
# Test with Expo development build or simulator

# Login flow
POST /api/v1/auth/login
# Dashboard data
GET /api/v1/leagues/me
# Player search
GET /api/v1/sports/players?sport=mlb&search=trout
# Lineup setting (touch-optimized)
PUT /api/v1/lineups
```

**Expected Results**:
- Mobile authentication works
- Touch interactions smooth (60fps)
- Offline lineup changes sync when online
- Push notifications delivered
- Feature parity with web app

## Scenario 4: AI and Analytics (Web)

### AI Recommendations
```bash
# 17. Get lineup recommendations
curl -X GET "/api/v1/analytics/recommendations?team_id=$TEAM_ID&type=lineup&week=1" \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN"

# 18. Get waiver recommendations
curl -X GET "/api/v1/analytics/recommendations?team_id=$TEAM_ID&type=waiver" \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN"
```

**Expected Results**:
- Recommendations based on matchups
- Confidence scores provided
- Reasoning explained clearly
- Performance impact estimated

### Performance Analytics
```bash
# 19. Get team insights
curl -X GET "/api/v1/analytics/insights?team_id=$TEAM_ID&timeframe=season" \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN"

# 20. Get league analytics
curl -X GET "/api/v1/analytics/insights?league_id=$LEAGUE_ID&timeframe=week" \
  -H "Authorization: Bearer $COMMISSIONER_TOKEN"
```

**Expected Results**:
- Overall performance grade
- Strengths and weaknesses identified
- Comparison to league average
- Actionable improvement suggestions

## Scenario 5: Professional Theme Validation (Web)

### Theme Switching
```javascript
// 21. Test dark mode toggle
document.documentElement.setAttribute('data-theme', 'dark');
// Verify fantasy sports color palette applied
// Check accessibility contrast ratios

// 22. Test responsive design
// Resize window to mobile breakpoints
// Verify touch targets 44px minimum
// Test card layouts adapt properly
```

### Component Validation
```javascript
// 23. Player card component
// Verify stats display correctly
// Check injury status indicators
// Validate projection data

// 24. Draft board component
// Test real-time pick updates
// Verify timer countdown
// Check player availability status
```

## Performance Validation

### API Response Times
```bash
# 25. Measure response times
time curl -X GET "/api/v1/sports/players?sport=mlb&limit=50" \
  -H "Authorization: Bearer $TOKEN"
# Expected: < 300ms

time curl -X POST /api/v1/lineups \
  -H "Authorization: Bearer $TOKEN" \
  -d '...'
# Expected: < 600ms
```

### Concurrent User Test
```bash
# 26. Load testing with Apache Bench
ab -n 1000 -c 100 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/leagues/me
# Expected: No failures, < 1s average response
```

### Mobile Performance
```bash
# 27. Bundle size check
expo export --platform=ios
# Expected: < 100MB total bundle

# 28. React Native performance
# Use Flipper performance profiler
# Expected: 60fps during navigation/animations
```

## Validation Checklist

### ✅ Sports Data Integration
- [ ] Real player data loads correctly
- [ ] Injury status updates appear
- [ ] Team affiliations accurate
- [ ] Statistics display properly

### ✅ Advanced Fantasy Features
- [ ] Draft system works end-to-end
- [ ] Trade evaluation calculates
- [ ] Waiver processing functional
- [ ] Scoring system accurate

### ✅ Mobile Feature Parity
- [ ] All web features available
- [ ] Touch interactions optimized
- [ ] Offline capability works
- [ ] Push notifications deliver

### ✅ Real-time & Social
- [ ] WebSocket connections stable
- [ ] Live updates < 2s latency
- [ ] Chat functionality works
- [ ] Notifications targeted correctly

### ✅ AI & Analytics
- [ ] Recommendations generate
- [ ] Insights provide value
- [ ] Performance metrics accurate
- [ ] AI responses coherent

### ✅ Performance & Scale
- [ ] API responses < 300/600ms
- [ ] 1000+ concurrent users supported
- [ ] Mobile performance 60fps
- [ ] Error handling graceful

### ✅ Professional Theming
- [ ] Fantasy sports visual identity
- [ ] Dark mode optimized
- [ ] Responsive design works
- [ ] Accessibility compliant

## Troubleshooting

### Common Issues
1. **WebSocket connections fail**: Check CORS settings and proxy configuration
2. **Mobile build errors**: Verify Expo SDK version compatibility
3. **Slow API responses**: Check database indexing and query optimization
4. **Authentication failures**: Validate JWT token expiration and refresh logic
5. **Real-time updates delayed**: Monitor Redis connection and message queue

### Debug Commands
```bash
# Check API health
curl -X GET /api/v1/health

# Monitor WebSocket connections
wscat -c ws://localhost:8000/api/v1/real-time/connect

# Database query performance
psql -d ultimate_fantasy -c "EXPLAIN ANALYZE SELECT ..."

# Mobile debugging
expo start --tunnel
```

This quickstart validates all major features and provides concrete success criteria for the Ultimate Fantasy Platform implementation.