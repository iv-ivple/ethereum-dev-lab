# Web3 Learning Journey

## About
This repository documents my journey learning Web3 development with Python.

## Environment
- Python 3.10+
- web3.py
- Ubuntu Linux

## Weekly Progress

### Week 1: Environment Setup & Git
- ✅ Installed Python 3.10+ and web3.py
- ✅ Set up Git and GitHub
- ✅ Created first repository
- ✅ Learned basic Git commands

## Resources
- [web3.py Documentation](https://web3py.readthedocs.io/)
- [Git Documentation](https://git-scm.com/doc)

## Goals
- Master Web3 development
- Build decentralized applications
- Contribute to blockchain ecosystem

----------------------------------------------------------------

## Week 2: RPC Basics

### What I Learned
- JSON-RPC protocol: How to communicate with Ethereum nodes using HTTP requests
- Block structure: Understanding block numbers, hashes, timestamps, and transactions
- Wei vs Ether: 1 ETH = 1,000,000,000,000,000,000 Wei (10^18)
- RPC rate limits: Free tier typically allows 100-300 requests per second

### Scripts Created

#### get_latest_block.py
Fetches and displays information about the latest block on Ethereum mainnet.

**Usage:**
```bash
python3 scripts/get_latest_block.py
```

#### get_eth_balance.py
Checks ETH balance for any Ethereum address.

**Usage:**
```bash
# With example addresses
python3 scripts/get_eth_balance.py

# With specific address
python3 scripts/get_eth_balance.py 0xYOUR_ADDRESS_HERE
```

### Key Concepts

**JSON-RPC**: A lightweight remote procedure call protocol using JSON for data encoding.

**Block Numbers vs Block Hashes**:
- Block number: Sequential integer (e.g., 18500000)
- Block hash: Unique 32-byte identifier (e.g., 0xabc123...)

**Wei Conversions**:
- 1 Wei = smallest unit
- 1 Gwei = 1,000,000,000 Wei (10^9)
- 1 Ether = 1,000,000,000,000,000,000 Wei (10^18)

**RPC Rate Limits**:
- Free tier: ~100-300 requests/second
- Implement rate limiting in production
- Cache frequently accessed data

----------------------------------------------------------------

----------------------------------------------------------------

## Week 3: Wallets & Private Keys

### What I Learned
- **Private Key Cryptography**: How ECDSA (Elliptic Curve Digital Signature Algorithm) creates key pairs
- **HD Wallets (BIP39/BIP44)**: One mnemonic phrase can generate infinite addresses deterministically
- **Derivation Paths**: Standard Ethereum path is m/44'/60'/0'/0/X (BIP44 standard)
- **Message Signing**: Prove wallet ownership without sending transactions (EIP-191)
- **Transaction Signing**: Understanding nonce management and gas estimation
- **Security Best Practices**: Never commit private keys, use .env files, validate inputs

### Scripts Created

#### generate_wallet.py
Generates new Ethereum wallets with private keys, public keys, and addresses.

**Usage:**
```bash
python3 scripts/generate_wallet.py
```

#### generate_hd_wallet.py
Creates HD wallets using BIP39 mnemonic phrases with multiple derived accounts.

**Usage:**
```bash
python3 scripts/generate_hd_wallet.py
```

#### explore_derivation_paths.py
Demonstrates how different BIP44 derivation paths create different addresses from the same seed.

**Usage:**
```bash
python3 scripts/explore_derivation_paths.py
```

#### sign_message.py
Sign and verify messages using Ethereum private keys (EIP-191 standard).

**Usage:**
```bash
python3 scripts/sign_message.py
```

#### sign_transaction.py
Sign transactions offline with proper nonce management (doesn't broadcast to network).

**Usage:**
```bash
python3 scripts/sign_transaction.py
```

#### estimate_gas.py
Estimate gas costs for transactions at different priority levels.

**Usage:**
```bash
python3 scripts/estimate_gas.py
```

#### wallet_manager.py (Week 3 Deliverable)
Comprehensive wallet management tool with all Week 3 features and security best practices.

**Features:**
- Generate random wallets
- Generate HD wallets with mnemonics
- Import from private key or mnemonic
- Sign and verify messages
- Check balances and nonces
- Secure input handling (hidden private keys)

**Usage:**
```bash
python3 scripts/wallet_manager.py
```

### Key Concepts

**Private Key → Public Key → Address Flow**:
```
Private Key (256 bits)
    ↓ (ECDSA)
Public Key (512 bits)
    ↓ (Keccak-256)
Address (160 bits / 20 bytes)
```

**BIP44 Derivation Path Structure**: m/44'/60'/0'/0/0
- 44' = Purpose (BIP44)
- 60' = Coin Type (Ethereum)
- 0' = Account index
- 0 = Chain (0=external, 1=change)
- 0 = Address index

**Message Signing vs Transaction Signing**:
- **Message signing**: Prove ownership without gas costs
- **Transaction signing**: Authorizes state changes on blockchain

**Nonce Management**:
- Sequential number for each transaction from an address
- Prevents replay attacks
- Must increment without gaps
- Current nonce = transaction count

**Gas Price Strategies**:
- Slow: ~80% of average (10+ minutes)
- Average: Current network rate (3-5 minutes)
- Fast: ~120% of average (1-2 minutes)
- Instant: ~150% of average (~30 seconds)

### Security Practices Implemented
✅ `.gitignore` prevents committing sensitive files
✅ `.env` for storing configuration (never committed)
✅ Hidden input for private keys using `getpass`
✅ Clear warnings about test-only usage
✅ Input validation for addresses and keys
✅ Secure random number generation for key creation

### Resources Used
- [BIP39 Specification](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [BIP44 Specification](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)
- [EIP-191: Signed Data Standard](https://eips.ethereum.org/EIPS/eip-191)
- [eth-account Documentation](https://eth-account.readthedocs.io/)

----------------------------------------------------------------

----------------------------------------------------------------

## Week 4: ERC-20 Token Interaction

### What I Learned
- **ABIs (Application Binary Interface)**: The contract's "instruction manual" that defines functions, parameters, and return types
- **Function Selectors**: First 4 bytes of `keccak256(functionSignature)` used to identify contract functions
- **Contract Instances**: Python objects representing smart contracts with their address and ABI
- **Token Decimals**: ERC-20 balances are stored as integers; decimals define the conversion (e.g., USDC=6, DAI=18)
- **Read-Only Functions**: `view`/`constant` functions don't modify state and don't cost gas
- **Return Value Decoding**: How web3.py automatically decodes contract responses based on ABI
- **ERC-20 Standard**: All compliant tokens share the same interface (name, symbol, decimals, balanceOf, totalSupply)

### Scripts Created

#### explore_abi.py
Explains ABI structure and demonstrates function selectors.

**Usage:**
```bash
python3 scripts/week4/explore_abi.py
```

#### connect_to_token.py
Connects to popular ERC-20 tokens and fetches basic metadata.

**Usage:**
```bash
python3 scripts/week4/connect_to_token.py
```

#### check_balance.py
Checks ERC-20 token balances for Ethereum addresses.

**Usage:**
```bash
python3 scripts/week4/check_balance.py [ADDRESS]
```

#### token_metadata.py
Fetches comprehensive metadata for popular ERC-20 tokens.

**Usage:**
```bash
python3 scripts/week4/token_metadata.py
```

#### erc20_balance_checker.py (Week 4 Deliverable)
Comprehensive ERC-20 balance checker that works with any token address.

**Features:**
- Works with any ERC-20 token (by address or popular token name)
- Fetches complete token metadata (name, symbol, decimals, total supply)
- Checks balances for one or multiple addresses
- User-friendly output with proper formatting
- Error handling and address validation
- Supports token name shortcuts (USDC, DAI, WETH, UNI, LINK)

**Usage:**
```bash
# With examples
python3 scripts/erc20_balance_checker.py --examples

# Check USDC balance
python3 scripts/erc20_balance_checker.py USDC 0xYOUR_ADDRESS

# Check multiple balances
python3 scripts/erc20_balance_checker.py DAI 0xADDRESS1 0xADDRESS2

# Use full token address
python3 scripts/erc20_balance_checker.py 0xTOKEN_ADDRESS 0xWALLET_ADDRESS
```

### Key Concepts

**ABI Structure**:
```json
{
  "name": "balanceOf",
  "type": "function",
  "inputs": [{"name": "_owner", "type": "address"}],
  "outputs": [{"name": "balance", "type": "uint256"}],
  "constant": true
}
```

**Function Selector Calculation**:
- `balanceOf(address)` → `keccak256("balanceOf(address)")[:4]` → `0x70a08231`
- Used to identify which function to call in the contract
- First 4 bytes of the function signature hash

**Creating Contract Instances**:
```python
contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI)
balance = contract.functions.balanceOf(address).call()
```

**Token Decimal Conversion**:
```python
raw_balance = 1000000  # From contract
decimals = 6  # USDC has 6 decimals
actual_balance = raw_balance / (10 ** decimals)  # 1.0 USDC
```

**ERC-20 Standard Functions**:
- `name()` → Returns token name (e.g., "USD Coin")
- `symbol()` → Returns token symbol (e.g., "USDC")
- `decimals()` → Returns decimal places (e.g., 6)
- `totalSupply()` → Returns total token supply
- `balanceOf(address)` → Returns balance for an address

**Popular ERC-20 Tokens**:
- **USDC** (USD Coin): 6 decimals, stablecoin backed by Circle
- **DAI**: 18 decimals, decentralized stablecoin by MakerDAO
- **WETH** (Wrapped Ether): 18 decimals, ERC-20 wrapper for ETH
- **UNI** (Uniswap): 18 decimals, DEX governance token
- **LINK** (Chainlink): 18 decimals, oracle network token

**Read vs Write Operations**:
- **Read (call)**: Free, returns data, doesn't change state
  - Example: `balanceOf()`, `totalSupply()`
- **Write (transaction)**: Costs gas, changes state, requires signing
  - Example: `transfer()`, `approve()` (covered in Week 5)

### Resources Used
- [ERC-20 Token Standard](https://eips.ethereum.org/EIPS/eip-20)
- [web3.py Contract Documentation](https://web3py.readthedocs.io/en/stable/contracts.html)
- [Ethereum ABI Specification](https://docs.soliditylang.org/en/latest/abi-spec.html)
- [Etherscan Token Tracker](https://etherscan.io/tokens)

----------------------------------------------------------------

## Week 5: Transaction History & Events

### What I Learned
- **Event Logs**: How Ethereum logs work and their structure
- **Topics vs Data**: Indexed parameters in topics, non-indexed in data
- **Transfer Event**: Standard ERC-20 Transfer(address,address,uint256) event
- **Event Filtering**: Using eth_getLogs with topic filters
- **Pagination**: Handling RPC limits by fetching in chunks
- **Block Ranges**: Managing large historical queries
- **Transaction Receipts**: Extracting gas costs and event logs

### Scripts Created

#### explore_events.py - understanding event logs & topics
#### fetch_transaction_history.py - fetch events
#### parse_receipts.py - understanding transaction receipts
#### filter_transfer_events.py - filter logs event signature
#### paginated_event_fetcher.py - RCP block range limits, pagination, rate limiting
#### token_transfer_history.py - fetch all transfer events and generate CSV with number of information

### Key Concepts

**Transfer Event Structure**:
```
Event: Transfer(address indexed from, address indexed to, uint256 value)
Signature: 0xddf252ad...
Topic[0]: Event signature
Topic[1]: from address (indexed)
Topic[2]: to address (indexed)
Data: amount (non-indexed)
```

[Continue with other key concepts...]
```

---

## **Key Concepts Summary**

### Event Logs
Events are stored in the blockchain's transaction receipts as logs. Each log contains:
- **address**: The contract that emitted the event
- **topics**: Array of indexed parameters (max 4, first is event signature)
- **data**: Non-indexed parameters (ABI encoded)

### Topics Explained
```
topics[0] = keccak256("Transfer(address,address,uint256)")
topics[1] = from address (32 bytes, padded)
topics[2] = to address (32 bytes, padded)
data = amount (32 bytes, uint256)

-------------------------------------------------------------------

-------------------------------------------------------------------

## Week 6: Database Fundamentals

### What I Learned
- **SQL Basics**: CREATE, INSERT, SELECT, UPDATE, DELETE operations
- **Schema Design**: Proper table structure, relationships, and foreign keys
- **Indexes**: Improving query performance with strategic indexing
- **SQLAlchemy ORM**: Object-relational mapping for Pythonic database access
- **Normalization**: Organizing data to reduce redundancy
- **SQL Injection Prevention**: Using parameterized queries and ORM
- **Database Integration**: Storing blockchain data for efficient querying

### Scripts Created

#### Database Setup & Schema
- `create_schema.py` - Creates database schema with proper structure
- `models.py` - SQLAlchemy ORM models for all tables
- `db_helper.py` - Helper functions for common database operations

#### Data Integration
- `store_transfers.py` - Fetches blockchain events and stores in database
- `query_transfers.py` - Query and analyze stored transfer data

#### Week 6 Deliverable
- `setup_database.py` - Complete database setup script with sample data

### Key Concepts

**Database Schema Design**:
```
wallets → tracks wallet addresses
tokens → stores ERC-20 token metadata
transfers → records all transfer events (FK to tokens)
blocks → caches block information

-------------------------------------------------------------------


## Week 7: Testing Basics

### What I Learned
- **pytest Framework**: Writing unit and integration tests
- **Mocking**: Using unittest.mock to simulate RPC calls
- **Test Coverage**: Measuring and improving code coverage
- **Fixtures**: Reusable test data and setup
- **Parametrization**: Testing multiple inputs efficiently
- **CI/CD**: Automated testing with GitHub Actions

### Test Suite
- 50+ unit tests covering Weeks 2-6
- Achieved 75% code coverage
- Mocked all external dependencies
- Automated testing pipeline

### Key Concepts

**Test-Driven Development (TDD)**:
Write tests first → Write code → Refactor

**Mocking External Dependencies**:
```python
@patch('web3.Web3.HTTPProvider')
def test_with_mock(mock_provider):
    # Test without real RPC calls
```

**Fixtures for Reusability**:
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}
```

**Coverage Analysis**:
- Green (80-100%): Well tested
- Yellow (50-80%): Needs improvement
- Red (0-50%): Urgent attention needed

--------------------------------------------------------

## Week 8-10: Flask Wallet Watcher API

### What I Built
A production-ready REST API that monitors Ethereum wallets, tracks transactions, and sends balance alerts.

### Features
- ✅ Wallet registration and monitoring
- ✅ Transaction history tracking
- ✅ Balance alert system
- ✅ API key authentication
- ✅ Rate limiting
- ✅ Background worker for continuous monitoring
- ✅ Deployed to production

### Tech Stack
- Flask (web framework)
- SQLAlchemy (database ORM)
- APScheduler (background jobs)
- Web3.py (Ethereum interaction)
- PostgreSQL (production database)
- Render (hosting platform)

### Documentation
- [API Documentation](./README_API.md) - Complete API reference
- [Deployment Guide](./DEPLOYMENT.md) - How to deploy

### Live API
🔗 https://wallet-watcher-api.onrender.com/

### Test It Out
```bash
# Create an API key first, then:
curl -H "X-API-Key: YOUR_KEY" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"address": "0xYOUR_WALLET", "label": "Test"}' \
  https://your-app.onrender.com/api/v1/wallets
```

-----------------------------------------------------------------------------

# Docker Deployment Guide

## Quick Start

### Development
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Architecture
```
┌─────────────────┐
│   Flask API     │ :5000
│  (Gunicorn)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PostgreSQL    │ :5432
│   (Database)    │
└─────────────────┘
```

## Environment Variables

Required:
- `RPC_URL`: Ethereum RPC endpoint
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: PostgreSQL connection string

## Volumes

- `postgres_data`: Database persistence
- `./logs`: Application logs

## Health Checks

- API: `http://localhost:5000/api/v1/health`
- Database: `pg_isready` check every 10s

## Troubleshooting

### Container won't start
```bash
docker-compose logs api
docker-compose ps
```

### Database connection failed
```bash
docker-compose exec db psql -U walletuser -d walletwatcher
```

### Reset everything
```bash
docker-compose down -v
docker system prune -a
```
-----------------------------------------------------------------------------

# Web3 Telegram Bot

A Telegram bot for interacting with Ethereum blockchain - check balances, gas prices, token prices, and track wallets.

## Features

✅ Check ETH balances
✅ Get current gas prices
✅ Fetch token prices from DEXs
✅ Track multiple wallets
✅ Inline keyboards for quick actions
✅ Rate limiting and error handling

## Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show all available commands
- `/balance <address>` - Check ETH balance
- `/gas` - Get current gas prices
- `/price <token>` - Get token price (ETH, BTC, USDC, etc.)
- `/track <address> [label]` - Add wallet to tracking
- `/mywallets` - Show all tracked wallets
- `/untrack <address>` - Stop tracking wallet

## Setup

### Prerequisites

- Python 3.10+
- Telegram account
- Ethereum RPC endpoint (Infura/Alchemy)

### Installation

1. Clone repository:
```bash
git clone <your-repo>
cd telegram-web3-bot
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your values
```

5. Run the bot:
```bash
python bot.py
```

## Configuration

Required environment variables in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
RPC_URL=your_ethereum_rpc_url
ADMIN_USER_ID=your_telegram_user_id
```

## Project Structure
telegram-web3-bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not committed)
├── handlers/
│   ├── basic.py          # Basic commands (/start, /help)
│   ├── blockchain.py     # Blockchain commands
│   └── callbacks.py      # Inline keyboard handlers
├── utils/
│   ├── web3_helper.py    # Web3 utilities
│   ├── validators.py     # Input validation
│   ├── database.py       # Database management
│   └── rate_limiter.py   # Rate limiting
├── data/
│   └── bot_data.db       # SQLite database
└── tests/
└── test_bot.py       # Unit tests

## Development

Run tests:
```bash
pytest tests/
```

Check code style:
```bash
flake8 .
black .
```

## Security

- Bot token is stored in environment variables
- Input validation on all user inputs
- Rate limiting to prevent abuse
- SQL injection prevention with parameterized queries

## License

MIT

## Contact

Iv Ple - @ivivple

-----------------------------------------------------------------------------
----------------------------------------------------------------

## Weeks 16-18: Advanced Telegram Bot Analytics

### What I Learned
- **The Graph Protocol**: Querying blockchain data efficiently using GraphQL instead of RPC calls
- **GraphQL Caching**: Implementing intelligent cache strategies with different TTLs based on data volatility
- **Hybrid Data Fetching**: Combining RPC and Subgraph queries for optimal speed and accuracy
- **Chart Generation**: Using matplotlib to create professional OHLC (Open, High, Low, Close) price charts
- **Data Visualization**: Building activity charts with cumulative balance tracking and daily volume
- **Query Optimization**: Reducing API calls by 80% through strategic caching (token info: 24h, historical: 6h, current price: 1min)
- **Interactive UX**: Implementing inline keyboards for dynamic user interactions and data exploration

### Features Built

#### Token Analytics with Charts (`/analytics` command)
Generate comprehensive token analysis with auto-generated matplotlib charts:
- OHLC price history with customizable timeframes (7-365 days)
- Volume analysis with color-coded bars (green=price up, red=price down)
- Top traders identification and buy/sell volume breakdown
- Interactive buttons for deeper exploration (Refresh, More Days, All Traders, Volume Detail)

**Usage:**
```bash
/analytics 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 7
```

#### Wallet Activity Reports (`/wallet_report` command)
Complete wallet analysis with visualization:
- Transfer history using hybrid RPC/Subgraph approach
- Cumulative balance chart showing net changes over time
- Daily transfer volume visualization (received vs sent)
- Top counterparties identification (senders and receivers)
- CSV export for offline analysis

**Usage:**
```bash
/wallet_report 0x742d35Cc6634C0532925a3b844Bc454e4438f44e 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 30
```

### New Modules Created

#### analytics/token_analytics.py
Token data fetching and analysis:
- `get_token_info()` - Fetch symbol, name, decimals
- `get_price_history()` - Historical OHLC data with DataFrame output
- `get_token_volume_24h()` - 24-hour trading volume calculation
- `get_top_traders()` - Aggregate swaps by trader with buy/sell breakdown

#### analytics/transfers_analytics.py
Intelligent transfer tracking:
- `get_transfers_hybrid()` - Smart strategy: RPC for <10k blocks, Subgraph for larger ranges
- `get_transfer_summary()` - Complete wallet analysis with statistics
- `analyze_transfers()` - Calculate received, sent, net change, and unique counterparties

#### utils/graph_helper.py
GraphQL client with production features:
- Query caching with MD5 hashing and GZIP compression
- Automatic retry with exponential backoff (max 3 attempts)
- Rate limiting per provider (configurable requests/second)
- Health checks and connection pooling
- Query deduplication and statistics tracking

#### utils/cache_helper.py
File-based caching system:
- TTL-based expiration (configurable per query type)
- Size limits with automatic cleanup (oldest-first removal)
- Compression for storage efficiency
- Cache hit rate tracking (achieved 85% average hit rate)

#### handlers/analytics_commands.py & analytics_callbacks.py
User interface handlers:
- Chart generation with matplotlib (100 DPI, professional styling)
- Progress messages during data fetching
- Interactive button callbacks for dynamic updates
- CSV export functionality
- Error handling with user-friendly messages

### Key Concepts

**GraphQL Query Strategy**:
```graphql
{
  tokenDayDatas(first: 7, orderBy: date, where: {token: "0x..."}) {
    date
    priceUSD
    volumeUSD
    open
    high
    low
    close
  }
}
```

**Hybrid Transfer Fetching**:
- ≤10k blocks: RPC only (eth_getLogs with Transfer event signature)
- >10k blocks: Subgraph (historical) + RPC (recent 1000 blocks)
- Merge and deduplicate using tx_hash + log_index as unique key

**Caching Hierarchy**:
| Data Type | TTL | Reason |
|-----------|-----|--------|
| Token Info | 24 hours | Rarely changes |
| Historical Price | 6 hours | Immutable once created |
| Current Price | 1 minute | Volatile |
| Volume Data | 5 minutes | Moderate updates |

**Chart Generation Flow**:
1. Fetch data via GraphQL (cached if available)
2. Transform to pandas DataFrame
3. Create matplotlib figure with subplots
4. Style with professional color scheme (#2962FF blue, #4CAF50 green)
5. Auto-format axes (K/M notation, date formatting)
6. Save to /tmp as PNG (100 DPI)
7. Send via Telegram
8. Clean up temporary file

### Technical Challenges Solved

**Subgraph Endpoint Deprecation**:
- Issue: The Graph deprecated hosted service endpoints mid-development
- Solution: Migrated to Gateway API with API key authentication
- Impact: Had to update all queries and handle rate limiting differently

**Python Indentation Debugging**:
- Issue: Duplicate `class TokenAnalytics:` declarations causing syntax errors
- Solution: Systematic debugging using `grep -n` to find duplicate declarations
- Learning: Python's indentation sensitivity requires careful copy-paste validation

**Messaging Wrong Bot**:
- Issue: Bot running but not responding to commands
- Solution: Verified TELEGRAM_BOT_TOKEN matches the bot being messaged
- Learning: Always confirm bot identity via @BotFather before extensive debugging

**RPC vs Subgraph Trade-offs**:
- RPC: Real-time, accurate, but slow for large ranges and rate-limited
- Subgraph: Fast, indexed, but 1-2 blocks behind and requires API key
- Solution: Hybrid approach with intelligent strategy selection based on block range

### Performance Metrics

**Query Performance** (with caching):
- Token Info: 500ms → 50ms (10x faster)
- Price History: 800ms → 100ms (8x faster)
- Volume Data: 600ms → 80ms (7.5x faster)
- Top Traders: 1000ms → 150ms (6.7x faster)

**API Call Reduction**:
- Before: ~1000 API calls/hour
- After: ~200 API calls/hour (80% reduction)

**Cache Hit Rates**:
- Token Info: 95%
- Historical Data: 85%
- Volume Data: 70%

### Security Practices

✅ API keys stored in environment variables
✅ Input validation on all addresses (checksumming)
✅ Rate limiting to prevent API abuse
✅ No sensitive data in error messages
✅ Automatic cleanup of temporary chart files
✅ SQL injection prevention with parameterized queries

### Documentation Created

- **README_UPDATED.md** - Complete feature overview and setup guide
- **docs/GRAPHQL_QUERIES.md** - All 7 GraphQL queries documented with examples
- **docs/ARCHITECTURE.md** - System architecture with ASCII diagrams
- **docs/SETUP_GUIDE.md** - Detailed deployment instructions
- **docs/EXAMPLES.md** - Visual examples of bot outputs

### Tech Stack Additions
```
+ matplotlib 3.8.0      # Chart generation
+ pandas 2.2.0          # Data manipulation  
+ numpy 1.26.0          # Numerical operations
+ The Graph Protocol    # Blockchain indexing
```

### Project Repository

📦 [GitHub Release v2.1.0](https://github.com/iv-ivple/web3-telegram-bot)
- 23 files changed, 5261 insertions, 225 deletions
- Complete analytics suite with professional visualizations
- Production-ready with caching, error handling, and rate limiting

### Resources Used
- [The Graph Documentation](https://thegraph.com/docs/)
- [matplotlib Documentation](https://matplotlib.org/stable/contents.html)
- [Uniswap V3 Subgraph](https://github.com/Uniswap/v3-subgraph)
- [python-telegram-bot](https://docs.python-telegram-bot.org/)

----------------------------------------------------------------
