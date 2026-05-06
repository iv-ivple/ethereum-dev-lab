-- Wallets being monitored
CREATE TABLE IF NOT EXISTS wallets (
    id          SERIAL PRIMARY KEY,
    address     VARCHAR(42) UNIQUE NOT NULL,
    label       TEXT,                           -- optional human-readable name
    active      BOOLEAN DEFAULT TRUE,
    added_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Snapshot of each wallet's Aave position, stored every poll cycle
CREATE TABLE IF NOT EXISTS position_snapshots (
    id                      SERIAL PRIMARY KEY,
    wallet_id               INT REFERENCES wallets(id) ON DELETE CASCADE,
    health_factor           NUMERIC(30, 18) NOT NULL,
    total_collateral_usd    NUMERIC(30, 6),
    total_debt_usd          NUMERIC(30, 6),
    available_borrows_usd   NUMERIC(30, 6),
    ltv                     NUMERIC(10, 4),
    liquidation_threshold   NUMERIC(10, 4),
    recorded_at             TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast time-series queries per wallet
CREATE INDEX IF NOT EXISTS idx_snapshots_wallet_time
    ON position_snapshots(wallet_id, recorded_at DESC);

-- Alert log — prevents duplicate Discord notifications
CREATE TABLE IF NOT EXISTS alerts (
    id              SERIAL PRIMARY KEY,
    wallet_id       INT REFERENCES wallets(id) ON DELETE CASCADE,
    alert_type      VARCHAR(20) NOT NULL,       -- 'WARNING' or 'CRITICAL'
    health_factor   NUMERIC(30, 18),
    message         TEXT,
    sent_at         TIMESTAMPTZ DEFAULT NOW()
);

-- One alert per wallet per type per hour (dedup window)
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_dedup
    ON alerts(wallet_id, alert_type, date_trunc('hour', sent_at AT TIME ZONE 'UTC'));
