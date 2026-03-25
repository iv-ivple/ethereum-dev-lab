# Week 6 Database Schema Design

## Tables

### wallets
Stores wallet addresses we're tracking
- id (PRIMARY KEY)
- address (UNIQUE, NOT NULL)
- label (optional nickname)
- created_at

### tokens
Stores ERC-20 token information
- id (PRIMARY KEY)
- address (UNIQUE, NOT NULL)
- symbol
- name
- decimals
- total_supply
- last_updated

### transfers
Stores token transfer events
- id (PRIMARY KEY)
- token_id (FOREIGN KEY → tokens)
- from_address
- to_address
- amount_raw (stored as TEXT to handle big numbers)
- amount_decimal (computed for display)
- block_number
- transaction_hash
- log_index
- timestamp
- gas_used

### blocks
Stores block metadata (optional, for optimization)
- block_number (PRIMARY KEY)
- timestamp
- hash

## Indexes for Performance
- transfers(token_id, block_number)
- transfers(from_address)
- transfers(to_address)
- transfers(transaction_hash)
