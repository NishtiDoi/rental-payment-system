-- ============================================================================
-- FOCUSED DISCREPANCY REPORT
-- Shows ONLY the intentional errors we seeded
-- ============================================================================

WITH reconciliation AS (
    SELECT 
        COALESCE(t.idempotency_key, bs.transaction_ref) as transaction_ref,
        t.id as internal_txn_id,
        bs.id as bank_stmt_id,
        COALESCE(t.amount, 0.00) as internal_amount,
        COALESCE(bs.amount, 0.00) as bank_amount,
        t.status::varchar as internal_status,
        COALESCE(bs.status, 'MISSING') as bank_status,
        
        CASE 
            WHEN t.idempotency_key IS NULL THEN 'UNEXPECTED_BANK_CHARGE'
            WHEN bs.transaction_ref IS NULL THEN 'MISSING_IN_BANK'
            WHEN t.amount != bs.amount THEN 'AMOUNT_MISMATCH'
            WHEN t.status::varchar != bs.status THEN 'STATUS_MISMATCH'
            ELSE 'MATCH'
        END as recon_status,
        
        ABS(COALESCE(t.amount, 0) - COALESCE(bs.amount, 0)) as amount_difference,
        t.completed_at as internal_completed_at,
        bs.processed_at as bank_processed_at
    
    FROM transactions t
    FULL OUTER JOIN bank_statements bs 
        ON t.idempotency_key = bs.transaction_ref
)
SELECT 
    transaction_ref,
    internal_amount,
    bank_amount,
    amount_difference,
    recon_status,
    CASE 
        WHEN recon_status = 'UNEXPECTED_BANK_CHARGE' 
            THEN '🚨 GHOST CHARGE: Bank charged us $' || bank_amount::text || ' but we have NO RECORD'
        WHEN recon_status = 'AMOUNT_MISMATCH' 
            THEN '⚠️  AMOUNT MISMATCH: We recorded $' || internal_amount::text || ' but bank shows $' || bank_amount::text
        WHEN recon_status = 'MISSING_IN_BANK' 
            THEN '⏳ FLOAT: We sent $' || internal_amount::text || ' but bank hasn''t confirmed yet'
        ELSE 'N/A'
    END as action_required
    
FROM reconciliation
WHERE recon_status IN ('UNEXPECTED_BANK_CHARGE', 'AMOUNT_MISMATCH')  -- Only the critical errors
ORDER BY recon_status DESC, amount_difference DESC;

-- ============================================================================
-- ERROR TYPE BREAKDOWN
-- ============================================================================

\echo ''
\echo '════════════════════════════════════════════════════════════════════════'
\echo 'RECONCILIATION SUMMARY'
\echo '════════════════════════════════════════════════════════════════════════'

WITH error_breakdown AS (
    SELECT 
        CASE 
            WHEN t.idempotency_key IS NULL THEN 'UNEXPECTED_BANK_CHARGE (Ghost Charge)'
            WHEN bs.transaction_ref IS NULL THEN 'MISSING_IN_BANK (Float - Pending Bank Confirmation)'
            WHEN t.amount != bs.amount THEN 'AMOUNT_MISMATCH (Penny Pinching / Rounding Errors)'
            WHEN t.status::varchar != bs.status THEN 'STATUS_MISMATCH (Processing State Difference)'
            ELSE 'MATCH (No Issues)'
        END as error_type,
        COUNT(*) as count,
        ROUND(SUM(COALESCE(t.amount, bs.amount))::numeric, 2) as total_amount_affected
    FROM transactions t
    FULL OUTER JOIN bank_statements bs 
        ON t.idempotency_key = bs.transaction_ref
    GROUP BY error_type
)
SELECT 
    error_type as "Error Type",
    count as "Count",
    total_amount_affected as "Total Amount Affected"
FROM error_breakdown
WHERE error_type != 'MATCH (No Issues)'
ORDER BY count DESC;
