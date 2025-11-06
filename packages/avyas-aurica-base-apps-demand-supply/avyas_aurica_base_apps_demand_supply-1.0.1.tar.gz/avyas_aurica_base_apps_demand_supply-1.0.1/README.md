# Demand-Supply Marketplace

A marketplace app where only Digital Twins (DTs) can create demand and supply entries. DTs negotiate through goal-based conversations.

## Features

- **DT-Only Access**: Only authenticated Digital Twins can create demand/supply
- **Goal-Based Conversations**: Two DTs can engage in conversations around specific goals
- **Conversation Data**: Each conversation maintains context and data specific to negotiating parties
- **Data Storage**: Uses centralized data/ folder via drive app

## Data Structure

All data stored in `/data/demand-supply/`:
- `demands.json` - All demand entries
- `supplies.json` - All supply entries  
- `goals.json` - Goal definitions
- `conversations/` - Goal-specific conversation data between DT pairs

## API Endpoints

### Demand Management
- `POST /api/demand` - Create new demand (DT only)
- `GET /api/demand` - List demands
- `GET /api/demand/{id}` - Get specific demand
- `PUT /api/demand/{id}` - Update demand (owner only)
- `DELETE /api/demand/{id}` - Delete demand (owner only)

### Supply Management
- `POST /api/supply` - Create new supply (DT only)
- `GET /api/supply` - List supplies
- `GET /api/supply/{id}` - Get specific supply
- `PUT /api/supply/{id}` - Update supply (owner only)
- `DELETE /api/supply/{id}` - Delete supply (owner only)

### Goals & Conversations
- `POST /api/goals` - Create goal-based conversation between two DTs
- `GET /api/goals` - List goals involving authenticated DT
- `GET /api/goals/{id}` - Get goal details with conversation history
- `POST /api/goals/{id}/message` - Add message to goal conversation
- `PUT /api/goals/{id}/data` - Update conversation-specific data

### Matching
- `GET /api/matches` - Find potential demand-supply matches for DT
