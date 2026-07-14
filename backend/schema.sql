-- ============================================================
-- The Hunger Project - Ghana | Fleet Management System
-- Schema Updates v2.0 -> v2.1
-- Append this to schema.sql (and run once against the live DB;
-- every statement is idempotent, so it is safe if some objects
-- already exist there).
-- Date: 14 July 2026
-- ============================================================

-- NOTE ON BALANCE ADJUSTMENTS: no schema change is required for the new
-- 'adjustment' transaction type. fuel_transactions.transaction_type is an
-- unconstrained VARCHAR(20) and total_cost is NUMERIC(12,2), which accepts
-- the signed amounts adjustments use. The comment on the column should
-- simply be read as: 'purchase', 'topup', 'transfer', 'adjustment'.

-- NOTE ON TRIP DISTANCE: trips.distance is a GENERATED ALWAYS ... STORED
-- column, so PostgreSQL computes it automatically. The application must
-- never write to it (main.py v2.1 respects this).

-- ── Objects the application uses that are missing from schema.sql v2.0 ──
-- (Your live database already has these from earlier upgrade sessions;
-- they are included here so schema.sql alone can rebuild the system.)

-- Audit log (append-only record of all data mutations)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    action VARCHAR(50) NOT NULL,          -- CREATE, UPDATE, DELETE, DEACTIVATE, TOPUP, BALANCE_ADJUST
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);

-- Driver categories and service types (managed under Settings)
CREATE TABLE IF NOT EXISTS driver_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS service_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Columns added after v2.0
ALTER TABLE fuel_cards ADD COLUMN IF NOT EXISTS initial_balance NUMERIC(12,2) DEFAULT 0;
ALTER TABLE vehicles   ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE drivers    ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE drivers    ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES driver_categories(id);
ALTER TABLE drivers    ADD COLUMN IF NOT EXISTS service_type VARCHAR(100);

-- For cards created before initial_balance existed, seed it from the
-- current balance minus the net of all ledgered transactions, so
-- Recalculate reproduces today's balance instead of zeroing it.
UPDATE fuel_cards fc
SET initial_balance = fc.current_balance
    - COALESCE((SELECT SUM(CASE
            WHEN t.transaction_type = 'topup' THEN t.total_cost
            WHEN t.transaction_type = 'adjustment' THEN t.total_cost
            WHEN t.transaction_type IN ('purchase','transfer') THEN -t.total_cost
            ELSE 0 END)
        FROM fuel_transactions t WHERE t.fuel_card_id = fc.id), 0)
    - COALESCE((SELECT SUM(t.total_cost)
        FROM fuel_transactions t
        WHERE t.transfer_to_card_id = fc.id AND t.transaction_type = 'transfer'), 0)
WHERE COALESCE(fc.initial_balance, 0) = 0;

-- ── New performance indexes (statement and fuel card report queries) ──
CREATE INDEX IF NOT EXISTS idx_fuel_tx_card_type ON fuel_transactions (fuel_card_id, transaction_type);
CREATE INDEX IF NOT EXISTS idx_fuel_tx_transfer_to ON fuel_transactions (transfer_to_card_id);
