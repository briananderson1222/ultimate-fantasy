# Quickstart

This document provides a set of scenarios to test the core functionality of the Ultimate Fantasy Platform.

## Scenario 1: Create and Join a League

1.  **Given** a user is authenticated
2.  **When** the user sends a `POST` request to `/leagues` with a valid league configuration
3.  **Then** a new league is created and the user is assigned as the commissioner.
4.  **And** an invite link is returned.
5.  **When** another authenticated user accesses the invite link
6.  **Then** the user is added to the league as a manager.

## Scenario 2: Set a Lineup

1.  **Given** a manager is in a league
2.  **When** the manager sends a `PUT` request to `/lineups` with a valid lineup for the current game day
3.  **Then** the lineup is saved and validated against the league's rules.

## Scenario 3: Score a Game

1.  **Given** a game has been played
2.  **When** the stats for the game are ingested
3.  **Then** the scores for the players in the game are calculated and the scoreboard is updated.

## Scenario 4: Waiver Claim

1.  **Given** a player is on waivers
2.  **When** a manager places a bid for the player by sending a `POST` request to `/waivers/bids`
3.  **Then** the bid is recorded.
4.  **When** the waiver period ends
5.  **Then** the player is awarded to the manager with the highest bid.
