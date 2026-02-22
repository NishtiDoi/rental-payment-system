-- ============================================================================
-- RECONCILIATION SETUP SCRIPT
-- Simulates external bank statement data with intentional discrepancies
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CREATE BANK_STATEMENTS TABLE (External data from bank CSV)
-- ============================================================================

DROP TABLE IF EXISTS bank_statements CASCADE;

CREATE TABLE bank_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_ref VARCHAR NOT NULL UNIQUE,  -- Matches our idempotency_key
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR NOT NULL,  -- 'completed', 'pending', 'failed'
    processed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bank_stmt_ref ON bank_statements(transaction_ref);
CREATE INDEX idx_bank_stmt_processed ON bank_statements(processed_at);

-- ============================================================================
-- 2. SEED BANK_STATEMENTS WITH CLEAN DATA + INTENTIONAL ERRORS
-- ============================================================================

-- Get the 500 most "stable" completed transactions (not the most recent 100)
WITH clean_transactions AS (
    SELECT 
        idempotency_key,
        amount,
        status,
        completed_at,
        ROW_NUMBER() OVER (ORDER BY completed_at DESC) as recency_rank
    FROM transactions 
    WHERE status = 'COMPLETED' 
      AND completed_at IS NOT NULL
    ORDER BY completed_at DESC
    LIMIT 600  -- Get 600, then exclude the first 100
),
filtered_clean AS (
    SELECT * FROM clean_transactions 
    WHERE recency_rank > 100  -- Skip the 100 most recent (The "Float")
    LIMIT 500
)
INSERT INTO bank_statements (transaction_ref, amount, status, processed_at)
SELECT 
    idempotency_key,
    amount,
    status,
    completed_at
FROM filtered_clean;

-- ============================================================================
-- 3. Error Type 1: AMOUNT_MISMATCH
-- Insert 1 record where bank amount is $0.01 less
-- ============================================================================

WITH mismatch_transaction AS (
    SELECT 
        idempotency_key,
        amount,
        status,
        completed_at
    FROM transactions 
    WHERE status = 'COMPLETED'
      AND idempotency_key NOT IN (SELECT transaction_ref FROM bank_statements)
    LIMIT 1
)
INSERT INTO bank_statements (transaction_ref, amount, status, processed_at)
SELECT 
    idempotency_key,
    amount - 0.01,  -- Bank shows $0.01 less
    status,
    completed_at
FROM mismatch_transaction;

-- ============================================================================
-- 4. Error Type 2: GHOST_CHARGE
-- Insert 1 record that does NOT exist in transactions table
-- ============================================================================

INSERT INTO bank_statements (transaction_ref, amount, status, processed_at)
VALUES (
    'GHOST_CHARGE_2026_' || TO_CHAR(NOW(), 'MMDD'),  -- Unique fake reference
    250.75,
    'completed',
    NOW() - INTERVAL '2 days'
);

COMMIT;

-- ============================================================================
-- RECONCILIATION VERIFICATION
-- ============================================================================

SELECT COUNT(*) as total_bank_statements FROM bank_statements;
SELECT COUNT(*) as total_clean_matches FROM bank_statements 
  WHERE transaction_ref IN (SELECT idempotency_key FROM transactions);

