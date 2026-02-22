-- Phase 1: Seed dummy data for rental payment system
-- 1,000 users, 700 properties, 2,500 leases, 10,000 transactions

BEGIN;

-- 1. EXTENSION: Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. CLEANUP: TRUNCATE with CASCADE to handle foreign keys
TRUNCATE users, properties, bank_accounts, leases, payment_schedules, transactions, transaction_events CASCADE;

-- ============================================================================
-- 3. CREATE USERS (200 landlords + 800 renters = 1,000 total)
-- ============================================================================
INSERT INTO users (id, email, full_name, role, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'landlord_' || i::text || '@example.com',
    'Landlord ' || i::text,
    'LANDLORD'::userrole,  -- UPPERCASE enum value
    NOW() - (random() * 365 * INTERVAL '1 day'),
    NOW()
FROM generate_series(1, 200) AS i;

INSERT INTO users (id, email, full_name, role, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'renter_' || i::text || '@example.com',
    'Renter ' || i::text,
    'RENTER'::userrole,  -- UPPERCASE enum value
    NOW() - (random() * 365 * INTERVAL '1 day'),
    NOW()
FROM generate_series(1, 800) AS i;

-- ============================================================================
-- 4. CREATE BANK ACCOUNTS (1-2 per user)
-- ============================================================================
INSERT INTO bank_accounts (id, user_id, account_number_token, routing_number, bank_name, is_verified, is_primary, created_at)
SELECT 
    gen_random_uuid(),
    u.id,
    LPAD(FLOOR(RANDOM() * 9999)::text, 4, '0'),
    LPAD(FLOOR(RANDOM() * 999999999)::text, 9, '0'),
    CASE FLOOR(RANDOM() * 4)::INT
        WHEN 0 THEN 'Bank of America'
        WHEN 1 THEN 'Wells Fargo'
        WHEN 2 THEN 'Chase Bank'
        ELSE 'US Bank'
    END,
    TRUE,
    TRUE,
    NOW() - (random() * 180 * INTERVAL '1 day')
FROM users u
ORDER BY RANDOM()
LIMIT 900;

-- ============================================================================
-- 5. CREATE PROPERTIES (~700 = landlords * 3-4 per landlord)
-- ============================================================================
WITH landlords AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) as landlord_seq FROM users WHERE role = 'LANDLORD'
)
INSERT INTO properties (id, landlord_id, address, city, state, zip_code, monthly_rent, created_at)
SELECT 
    gen_random_uuid(),
    landlord.id,
    'Property ' || landlord.landlord_seq::text || '-' || prop_seq::text,
    'New York',
    'NY',
    '10001',
    (800 + RANDOM() * 2200)::NUMERIC(10,2),
    NOW() - (random() * 730 * INTERVAL '1 day')
FROM landlords landlord
CROSS JOIN generate_series(1, (RANDOM() * 2 + 3)::INT) prop_seq;

-- ============================================================================
-- 6. CREATE LEASES (2,500 total, 3-4 per property)
-- ============================================================================
WITH renters AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as renter_seq FROM users WHERE role = 'RENTER'
)
INSERT INTO leases (id, property_id, renter_id, start_date, end_date, rent_amount, due_day_of_month, status, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    p.id,
    r.id,
    (NOW() - (random() * 500 * INTERVAL '1 day'))::DATE as start_date,
    (NOW() + (random() * 180 * INTERVAL '1 day'))::DATE as end_date,
    p.monthly_rent,
    (FLOOR(RANDOM() * 28) + 1)::INT,
    'ACTIVE'::leasestatus,  -- UPPERCASE enum
    NOW() - INTERVAL '1 year',
    NOW()
FROM properties p
CROSS JOIN LATERAL (
    SELECT id FROM renters ORDER BY renter_seq LIMIT (RANDOM() * 2 + 2)::INT
) r
LIMIT 2500;  -- Cap at 2,500 leases

-- ============================================================================
-- 7. CREATE PAYMENT SCHEDULES (1 per lease)
-- ============================================================================
INSERT INTO payment_schedules (id, lease_id, next_due_date, amount, status, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    id,
    (NOW() + INTERVAL '1 month')::DATE,
    rent_amount,
    'ACTIVE'::schedulestatus,  -- UPPERCASE enum
    NOW() - INTERVAL '1 year',
    NOW()
FROM leases;

-- ============================================================================
-- 8. CREATE TRANSACTIONS (10,000 total)
-- ============================================================================
WITH valid_leases AS (
    SELECT 
        l.id as lease_id,
        l.renter_id,
        l.rent_amount,
        l.start_date,
        p.landlord_id,
        ba_renter.id as renter_account_id,
        ba_landlord.id as landlord_account_id,
        ROW_NUMBER() OVER (ORDER BY l.id) as lease_num,
        FLOOR(((ROW_NUMBER() OVER (ORDER BY l.id) - 1) * 10000.0 / COUNT(*) OVER ())) as max_txn_per_lease
    FROM leases l
    JOIN properties p ON l.property_id = p.id
    JOIN bank_accounts ba_renter ON l.renter_id = ba_renter.user_id AND ba_renter.is_primary = TRUE
    JOIN bank_accounts ba_landlord ON p.landlord_id = ba_landlord.user_id AND ba_landlord.is_primary = TRUE
)
INSERT INTO transactions (
    id, idempotency_key, lease_id, payer_account_id, payee_account_id,
    amount, status, payment_rail_type, 
    initiated_at, processing_at, completed_at, failed_at,
    retry_count, details, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'IDEMP_' || vl.lease_id::text || '_' || txn_seq::text,
    vl.lease_id,
    vl.renter_account_id,
    vl.landlord_account_id,
    vl.rent_amount,
    CASE FLOOR(RANDOM() * 10)::INT
        WHEN 0 THEN 'PENDING'::transactionstatus
        WHEN 1 THEN 'PENDING'::transactionstatus
        WHEN 2 THEN 'FAILED'::transactionstatus
        ELSE 'COMPLETED'::transactionstatus
    END,
    CASE FLOOR(RANDOM() * 10)::INT
        WHEN 0 THEN 'INSTANT'::paymentrailtype
        WHEN 1 THEN 'SAME_DAY_ACH'::paymentrailtype
        WHEN 2 THEN 'SAME_DAY_ACH'::paymentrailtype
        WHEN 3 THEN 'WIRE'::paymentrailtype
        ELSE 'STANDARD_ACH'::paymentrailtype
    END,
    vl.start_date + (txn_seq * INTERVAL '1 month'),
    vl.start_date + (txn_seq * INTERVAL '1 month') + INTERVAL '1 day',
    vl.start_date + (txn_seq * INTERVAL '1 month') + INTERVAL '2 days',
    CASE WHEN FLOOR(RANDOM() * 100)::INT = 1 THEN vl.start_date + (txn_seq * INTERVAL '1 month') + INTERVAL '1 day' ELSE NULL END,
    0,
    '{"source": "api", "retry": false}',
    NOW(),
    NOW()
FROM valid_leases vl
CROSS JOIN generate_series(1, 5) txn_seq
LIMIT 10000;

-- ============================================================================
-- 9. CREATE TRANSACTION EVENTS (sample audit trail)
-- ============================================================================
INSERT INTO transaction_events (id, transaction_id, event_type, previous_status, new_status, details, timestamp)
SELECT 
    gen_random_uuid(),
    t.id,
    'status_change',
    'PENDING'::transactionstatus,
    t.status,
    '{"reason": "processing"}',
    t.initiated_at
FROM transactions t
LIMIT 5000;

COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT '✅ Seed data inserted successfully!' as status;

SELECT 
    'Users' as table_name, COUNT(*) as row_count FROM users
UNION ALL SELECT 'Bank Accounts', COUNT(*) FROM bank_accounts
UNION ALL SELECT 'Properties', COUNT(*) FROM properties
UNION ALL SELECT 'Leases', COUNT(*) FROM leases
UNION ALL SELECT 'Payment Schedules', COUNT(*) FROM payment_schedules
UNION ALL SELECT 'Transactions', COUNT(*) FROM transactions
UNION ALL SELECT 'Transaction Events', COUNT(*) FROM transaction_events
ORDER BY row_count DESC;