-- ============================================================================
-- RECONCILIATION QUERY
-- Finds discrepancies between internal transactions and external bank statements
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
        COALESCE(t.completed_at::date, bs.processed_at::date) as transaction_date,
        
        -- Determine reconciliation status
        CASE 
            WHEN t.idempotency_key IS NULL THEN 'UNEXPECTED_BANK_CHARGE'
            WHEN bs.transaction_ref IS NULL THEN 'MISSING_IN_BANK'
            WHEN t.amount != bs.amount THEN 'AMOUNT_MISMATCH'
            WHEN t.status::varchar != bs.status THEN 'STATUS_MISMATCH'
            ELSE 'MATCH'
        END as recon_status,
        
        -- Calculate the difference for investigation
        ABS(COALESCE(t.amount, 0) - COALESCE(bs.amount, 0)) as amount_difference,
        
        -- Timestamps for investigation
        t.completed_at as internal_completed_at,
        bs.processed_at as bank_processed_at
    
    FROM transactions t
    FULL OUTER JOIN bank_statements bs 
        ON t.idempotency_key = bs.transaction_ref
)
SELECT 
    transaction_ref,
    internal_txn_id,
    bank_stmt_id,
    internal_amount,
    bank_amount,
    amount_difference,
    internal_status,
    bank_status,
    transaction_date,
    recon_status,
    internal_completed_at,
    bank_processed_at,
    
    -- Human-readable error message
    CASE 
        WHEN recon_status = 'UNEXPECTED_BANK_CHARGE' 
            THEN 'Bank charged $' || bank_amount::text || ' but we have no record of this transaction'
        WHEN recon_status = 'MISSING_IN_BANK' 
            THEN 'We sent $' || internal_amount::text || ' on ' || internal_completed_at::date::text || ' but bank has not confirmed receipt'
        WHEN recon_status = 'AMOUNT_MISMATCH' 
            THEN 'Amount mismatch: We recorded $' || internal_amount::text || ' but bank shows $' || bank_amount::text || ' (diff: $' || amount_difference::text || ')'
        WHEN recon_status = 'STATUS_MISMATCH' 
            THEN 'Status mismatch: We have ' || internal_status || ' but bank shows ' || bank_status
        ELSE 'No discrepancy detected'
    END as error_description
    
FROM reconciliation
WHERE recon_status != 'MATCH'  -- Only show discrepancies
ORDER BY 
    CASE 
        WHEN recon_status = 'UNEXPECTED_BANK_CHARGE' THEN 1
        WHEN recon_status = 'MISSING_IN_BANK' THEN 2
        WHEN recon_status = 'AMOUNT_MISMATCH' THEN 3
        WHEN recon_status = 'STATUS_MISMATCH' THEN 4
        ELSE 5
    END,
    amount_difference DESC;

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================

SELECT 
    'Total Transactions in System' as metric,
    COUNT(*)::text as value
FROM transactions
UNION ALL
SELECT 
    'Total Bank Statements' as metric,
    COUNT(*)::text as value
FROM bank_statements
UNION ALL
SELECT 
    'Perfect Matches' as metric,
    COUNT(*)::text as value
FROM (
    SELECT t.idempotency_key
    FROM transactions t
    INNER JOIN bank_statements bs ON t.idempotency_key = bs.transaction_ref
    WHERE t.amount = bs.amount AND t.status::varchar = bs.status
) matches
UNION ALL
SELECT 
    'Discrepancies Found' as metric,
    COUNT(*)::text as value
FROM (
    WITH reconciliation AS (
        SELECT 
            CASE 
                WHEN t.idempotency_key IS NULL THEN 'UNEXPECTED_BANK_CHARGE'
                WHEN bs.transaction_ref IS NULL THEN 'MISSING_IN_BANK'
                WHEN t.amount != bs.amount THEN 'AMOUNT_MISMATCH'
                WHEN t.status::varchar != bs.status THEN 'STATUS_MISMATCH'
                ELSE 'MATCH'
            END as recon_status
        FROM transactions t
        FULL OUTER JOIN bank_statements bs 
            ON t.idempotency_key = bs.transaction_ref
    )
    SELECT * FROM reconciliation WHERE recon_status != 'MATCH'
) discrepancies
UNION ALL
SELECT 
    'Unmatched (In Bank, Not in System)' as metric,
    COUNT(*)::text as value
FROM bank_statements bs
WHERE bs.transaction_ref NOT IN (SELECT idempotency_key FROM transactions)
UNION ALL
SELECT 
    'Float (In System, Not yet in Bank)' as metric,
    COUNT(*)::text as value
FROM transactions t
WHERE t.idempotency_key NOT IN (SELECT transaction_ref FROM bank_statements)
  AND t.status::varchar = 'COMPLETED'
ORDER BY metric;
