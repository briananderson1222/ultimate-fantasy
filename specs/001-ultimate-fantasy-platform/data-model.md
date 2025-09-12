# Data Model

This document defines the key entities for the Ultimate Fantasy Platform.

## League
- **league_id**: UUID (Primary Key)
- **name**: String
- **sport**: String
- **league_type**: String
- **season**: String
- **rules_preset**: JSONB
- **ux_mode**: String
- **commissioner_id**: UUID (Foreign Key to User)
- **created_at**: Timestamp
- **updated_at**: Timestamp

## User
- **user_id**: UUID (Primary Key)
- **email**: String (Unique)
- **display_name**: String
- **cognito_sub**: String (Unique)
- **created_at**: Timestamp
- **updated_at**: Timestamp

## Team
- **team_id**: UUID (Primary Key)
- **league_id**: UUID (Foreign Key to League)
- **user_id**: UUID (Foreign Key to User)
- **team_name**: String
- **created_at**: Timestamp
- **updated_at**: Timestamp

## Player
- **player_id**: UUID (Primary Key)
- **external_id**: String (from stats provider)
- **full_name**: String
- **sport**: String
- **position**: String

## Roster
- **roster_id**: UUID (Primary Key)
- **team_id**: UUID (Foreign Key to Team)
- **player_id**: UUID (Foreign Key to Player)
- **acquisition_date**: Timestamp
- **acquisition_method**: String (e.g., draft, waiver)

## Lineup
- **lineup_id**: UUID (Primary Key)
- **team_id**: UUID (Foreign Key to Team)
- **game_day**: Date
- **players**: JSONB (Array of player_id and position)
- **version**: Integer

## Schedule
- **schedule_id**: UUID (Primary Key)
- **league_id**: UUID (Foreign Key to League)
- **game_day**: Date
- **home_team_id**: UUID (Foreign Key to Team)
- **away_team_id**: UUID (Foreign Key to Team)

## Score
- **score_id**: UUID (Primary Key)
- **player_id**: UUID (Foreign Key to Player)
- **game_day**: Date
- **stats**: JSONB

## Waiver
- **waiver_id**: UUID (Primary Key)
- **league_id**: UUID (Foreign Key to League)
- **player_id**: UUID (Foreign Key to Player)
- **team_id**: UUID (Foreign Key to Team)
- **bid**: Integer
- **status**: String (e.g., pending, won, lost)

## Transaction
- **transaction_id**: UUID (Primary Key)
- **league_id**: UUID (Foreign Key to League)
- **team_id**: UUID (Foreign Key to Team)
- **player_id**: UUID (Foreign Key to Player)
- **transaction_type**: String (e.g., add, drop, trade)
- **timestamp**: Timestamp

## Notification
- **notification_id**: UUID (Primary Key)
- **user_id**: UUID (Foreign Key to User)
- **message**: String
- **is_read**: Boolean
- **created_at**: Timestamp

## Rule
- **rule_id**: UUID (Primary Key)
- **league_id**: UUID (Foreign Key to League)
- **name**: String
- **value**: JSONB

## Preset
- **preset_id**: UUID (Primary Key)
- **sport**: String
- **league_type**: String
- **name**: String
- **rules**: JSONB
