# Data Model

This document provides a detailed overview of the database schema for the Ultimate Fantasy Platform, based on the SQLAlchemy models in `backend/src/models`.

## Table of Contents

1.  [User](#user)
2.  [UserPreference](#userpreference)
3.  [League](#league)
4.  [LeagueBranding](#leaguebranding)
5.  [Team](#team)
6.  [Player](#player)
7.  [Roster](#roster)
8.  [Lineup](#lineup)
9.  [Schedule](#schedule)
10. [Score](#score)
11. [Waiver](#waiver)
12. [Transaction](#transaction)
13. [Rule](#rule)
14. [Preset](#preset)
15. [Notification](#notification)
16. [Waitlist](#waitlist)

---

### User

Stores user account information.

**Source:** `backend/src/models/user.py`

| Column        | Type      | Constraints                   | Description                                      |
| :------------ | :-------- | :---------------------------- | :----------------------------------------------- |
| `user_id`     | `UUID`    | **Primary Key**, `default:uuid4` | Unique identifier for the user.                  |
| `email`       | `String`  | `nullable:false`, `unique`      | User's email address.                            |
| `display_name`| `String`  | `nullable:false`                | User's chosen display name.                      |
| `cognito_sub` | `String`  | `nullable:false`, `unique`      | User's subject identifier from AWS Cognito.      |
| `created_at`  | `DateTime`| `default:now`                   | Timestamp of when the user was created.          |
| `updated_at`  | `DateTime`| `default:now`, `onupdate:now`   | Timestamp of the last update to the user record. |

### UserPreference

Stores individual user preferences for the application UI.

**Source:** `backend/src/models/user_preference.py`

| Column      | Type     | Constraints                      | Description                                           |
| :---------- | :------- | :------------------------------- | :---------------------------------------------------- |
| `user_id`   | `UUID`   | **Primary Key**, **Foreign Key (users)** | Links to the `User` this preference belongs to.       |
| `theme`     | `String` | `nullable:false`, `default:'light'` | The UI theme (e.g., 'light', 'dark').                 |
| `density`   | `String` | `nullable:false`, `default:'comfortable'` | The UI density (e.g., 'comfortable', 'compact').      |
| `locale`    | `String` | `nullable:false`, `default:'en-US'` | The user's preferred locale (e.g., 'en-US').          |
| `layouts`   | `JSON`   | `nullable:true`                  | User-defined custom layouts for different pages.      |
| `created_at`| `DateTime`| `default:now`                    | Timestamp of when the preference was created.         |
| `updated_at`| `DateTime`| `default:now`, `onupdate:now`    | Timestamp of the last update to the preference.       |

### League

Represents a single fantasy league.

**Source:** `backend/src/models/league.py`

| Column          | Type     | Constraints                      | Description                                      |
| :-------------- | :------- | :------------------------------- | :----------------------------------------------- |
| `league_id`     | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the league.                |
| `name`          | `String` | `nullable:false`                 | The name of the league.                          |
| `sport`         | `String` | `nullable:false`                 | The sport this league is for (e.g., 'football'). |
| `league_type`   | `String` | `nullable:false`                 | The type of league (e.g., 'head_to_head').     |
| `season`        | `String` | `nullable:false`                 | The season this league is for (e.g., '2025').    |
| `commissioner_id`| `UUID`   | **Foreign Key (users)**, `nullable:true` | The `user_id` of the league's commissioner.      |
| `created_at`    | `DateTime`| `default:now`                    | Timestamp of when the league was created.        |
| `updated_at`    | `DateTime`| `default:now`, `onupdate:now`    | Timestamp of the last update to the league.      |

### LeagueBranding

Stores custom branding for a league.

**Source:** `backend/src/models/league_branding.py`

| Column     | Type     | Constraints                      | Description                                      |
| :--------- | :------- | :------------------------------- | :----------------------------------------------- |
| `league_id`| `UUID`   | **Primary Key**, **Foreign Key (leagues)** | Links to the `League` this branding belongs to.  |
| `theme`    | `JSON`   | `nullable:true`                  | A map of CSS variables for custom theming.       |
| `name`     | `String` | `nullable:true`                  | A custom name for the league, overriding `League.name`. |
| `logo_url` | `String` | `nullable:true`                  | URL for a custom league logo.                    |
| `created_at`| `DateTime`| `default:now`                    | Timestamp of when the branding was created.      |
| `updated_at`| `DateTime`| `default:now`, `onupdate:now`    | Timestamp of the last update to the branding.    |

### Team

Represents a team within a league, managed by a user.

**Source:** `backend/src/models/team.py`

| Column      | Type     | Constraints                      | Description                                      |
| :---------- | :------- | :------------------------------- | :----------------------------------------------- |
| `team_id`   | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the team.                  |
| `league_id` | `UUID`   | **Foreign Key (leagues)**, `nullable:false` | The league this team belongs to.                 |
| `user_id`   | `UUID`   | **Foreign Key (users)**, `nullable:false` | The user who owns this team.                     |
| `team_name` | `String` | `nullable:false`                 | The name of the team.                            |
| `created_at`| `DateTime`| `default:now`                    | Timestamp of when the team was created.          |
| `updated_at`| `DateTime`| `default:now`, `onupdate:now`    | Timestamp of the last update to the team.        |

### Player

Stores information about a single sports player.

**Source:** `backend/src/models/player.py`

| Column      | Type     | Constraints                      | Description                                      |
| :---------- | :------- | :------------------------------- | :----------------------------------------------- |
| `player_id` | `UUID`   | **Primary Key**, `default:uuid4` | Internal unique identifier for the player.       |
| `external_id`| `String` | `nullable:false`                 | The player's ID from an external stats provider. |
| `full_name` | `String` | `nullable:false`                 | The player's full name.                          |
| `sport`     | `String` | `nullable:false`                 | The sport the player plays.                      |
| `position`  | `String` | `nullable:false`                 | The player's primary position (e.g., 'QB', 'PG'). |

### Roster

Links a player to a team, indicating ownership.

**Source:** `backend/src/models/roster.py`

| Column             | Type       | Constraints                      | Description                                      |
| :----------------- | :--------- | :------------------------------- | :----------------------------------------------- |
| `roster_id`        | `UUID`     | **Primary Key**, `default:uuid4` | Unique identifier for the roster entry.          |
| `team_id`          | `UUID`     | **Foreign Key (teams)**, `nullable:false` | The team that owns the player.                   |
| `player_id`        | `UUID`     | **Foreign Key (players)**, `nullable:false` | The player on the roster.                        |
| `acquisition_date` | `DateTime` | `nullable:false`                 | When the player was added to the roster.         |
| `acquisition_method`| `String`   | `nullable:false`                 | How the player was acquired (e.g., 'draft').   |

### Lineup

Represents a team's lineup for a specific game day.

**Source:** `backend/src/models/lineup.py`

| Column      | Type     | Constraints                      | Description                                      |
| :---------- | :------- | :------------------------------- | :----------------------------------------------- |
| `lineup_id` | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the lineup.                |
| `team_id`   | `UUID`   | **Foreign Key (teams)**, `nullable:false` | The team this lineup belongs to.                 |
| `game_day`  | `Date`   | `nullable:false`                 | The date for which this lineup is valid.         |
| `players`   | `JSON`   | `nullable:false`                 | An array of objects, each with `player_id` and `position`. |
| `version`   | `Integer`| `nullable:false`, `default:1`    | A version number, incremented on updates.        |

### Schedule

Defines matchups between teams in a league.

**Source:** `backend/src/models/schedule.py`

| Column         | Type     | Constraints                      | Description                                      |
| :------------- | :------- | :------------------------------- | :----------------------------------------------- |
| `schedule_id`  | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the scheduled game.        |
| `league_id`    | `UUID`   | **Foreign Key (leagues)**, `nullable:false` | The league where the game takes place.           |
| `game_day`     | `Date`   | `nullable:false`                 | The date of the game.                            |
| `home_team_id` | `UUID`   | **Foreign Key (teams)**, `nullable:false` | The home team.                                   |
| `away_team_id` | `UUID`   | **Foreign Key (teams)**, `nullable:false` | The away team.                                   |

### Score

Stores player performance stats for a specific game day.

**Source:** `backend/src/models/score.py`

| Column      | Type     | Constraints                      | Description                                      |
| :---------- | :------- | :------------------------------- | :----------------------------------------------- |
| `score_id`  | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the score record.          |
| `player_id` | `UUID`   | **Foreign Key (players)**, `nullable:false` | The player who achieved the stats.               |
| `game_day`  | `Date`   | `nullable:false`                 | The date the stats were recorded.                |
| `stats`     | `JSON`   | `nullable:false`                 | A dictionary of performance statistics (e.g., `{'points': 25}`). |

### Waiver

Represents a waiver wire bid placed by a team for a player.

**Source:** `backend/src/models/waiver.py`

| Column      | Type     | Constraints                      | Description                                      |
| :---------- | :------- | :------------------------------- | :----------------------------------------------- |
| `waiver_id` | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the waiver bid.            |
| `league_id` | `UUID`   | **Foreign Key (leagues)**, `nullable:false` | The league where the bid was placed.             |
| `player_id` | `UUID`   | **Foreign Key (players)**, `nullable:false` | The player being bid on.                         |
| `team_id`   | `UUID`   | **Foreign Key (teams)**, `nullable:false` | The team that placed the bid.                    |
| `bid`       | `Integer`| `nullable:false`                 | The bid amount.                                  |
| `status`    | `String` | `nullable:false`, `default:'pending'` | The status of the bid (e.g., 'pending', 'won'). |

### Transaction

Logs roster changes like adding, dropping, or trading players.

**Source:** `backend/src/models/transaction.py`

| Column             | Type       | Constraints                      | Description                                      |
| :----------------- | :--------- | :------------------------------- | :----------------------------------------------- |
| `transaction_id`   | `UUID`     | **Primary Key**, `default:uuid4` | Unique identifier for the transaction.           |
| `league_id`        | `UUID`     | **Foreign Key (leagues)**, `nullable:false` | The league where the transaction occurred.       |
| `team_id`          | `UUID`     | **Foreign Key (teams)**, `nullable:false` | The team involved in the transaction.            |
| `player_id`        | `UUID`     | **Foreign Key (players)**, `nullable:false` | The player involved in the transaction.          |
| `transaction_type` | `String`   | `nullable:false`                 | The type of transaction (e.g., 'add', 'drop'). |
| `timestamp`        | `DateTime` | `nullable:false`                 | When the transaction occurred.                   |

### Rule

Stores a specific rule or setting for a league.

**Source:** `backend/src/models/rule.py`

| Column      | Type     | Constraints                      | Description                                      |
| :---------- | :------- | :------------------------------- | :----------------------------------------------- |
| `rule_id`   | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the rule.                  |
| `league_id` | `UUID`   | **Foreign Key (leagues)**, `nullable:false` | The league this rule applies to.                 |
| `name`      | `String` | `nullable:false`                 | The name of the rule (e.g., 'max_roster_size').  |
| `value`     | `JSON`   | `nullable:false`                 | The value of the rule (e.g., `{'size': 15}`).   |

### Preset

Stores a predefined set of rules for a given sport and league type.

**Source:** `backend/src/models/preset.py`

| Column        | Type     | Constraints                      | Description                                      |
| :------------ | :------- | :------------------------------- | :----------------------------------------------- |
| `preset_id`   | `UUID`   | **Primary Key**, `default:uuid4` | Unique identifier for the preset.                |
| `sport`       | `String` | `nullable:false`                 | The sport this preset is for.                    |
| `league_type` | `String` | `nullable:false`                 | The league type this preset is for.              |
| `name`        | `String` | `nullable:false`                 | The name of the preset (e.g., 'Standard NFL'). |
| `rules`       | `JSON`   | `nullable:false`                 | A dictionary of rules included in this preset.   |

### Notification

Represents a notification to be shown to a user.

**Source:** `backend/src/models/notification.py`

| Column          | Type      | Constraints                      | Description                                      |
| :-------------- | :-------- | :------------------------------- | :----------------------------------------------- |
| `notification_id`| `UUID`    | **Primary Key**, `default:uuid4` | Unique identifier for the notification.          |
| `user_id`       | `UUID`    | **Foreign Key (users)**, `nullable:false` | The user who will receive the notification.      |
| `message`       | `String`  | `nullable:false`                 | The content of the notification message.         |
| `is_read`       | `Boolean` | `nullable:false`, `default:false` | Whether the user has read the notification.      |
| `created_at`    | `DateTime`| `default:now`                    | Timestamp of when the notification was created.  |

### Waitlist

Stores email addresses of users who have joined the waitlist.

**Source:** `backend/src/models/waitlist.py`

| Column     | Type       | Constraints                   | Description                                      |
| :--------- | :--------- | :---------------------------- | :----------------------------------------------- |
| `id`       | `UUID`     | **Primary Key**, `default:uuid4` | Unique identifier for the waitlist entry.        |
| `email`    | `String`   | `nullable:false`, `unique`      | The user's email address.                        |
| `created_at`| `DateTime` | `nullable:false`, `default:now` | Timestamp of when the user joined the waitlist.  |