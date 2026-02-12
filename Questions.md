# **Consolidated Daily Question Sheets - DirectPay Project**

Answer these 8-10 critical questions at the end of each day to verify understanding.

---

## **DAY 1: Project Setup & Database Design**

**1. Why did we choose PostgreSQL over MongoDB for this payment system? Name 3 specific reasons.**
- [ ] My answer:

**2. Explain what `UUID(as_uuid=True)` means and why we use UUIDs instead of auto-incrementing integers for transaction IDs.**
- [ ] My answer:

**3. Draw the relationship diagram between User, BankAccount, Property, Lease, and Transaction. Label the relationship types (1-to-many, etc.).**
- [ ] My diagram:

**4. Why do we store `account_number_token` (last 4 digits) instead of the full account number?**
- [ ] My answer:

**5. What is Alembic and what happens when you run `alembic upgrade head`?**
- [ ] My answer:

**6. Open a Python shell and write code to:**
   - Create a User object
   - Query all BankAccounts for a specific user_id
- [ ] My code:
```python
# Your answer here
```

**7. Why did we add `index=True` to the email field? When would this index be used?**
- [ ] My answer:

**8. What would happen if you tried to delete a User who has BankAccounts linked to them? How could you configure this differently?**
- [ ] My answer:

---

## **DAY 2: Basic CRUD APIs - Users & Bank Accounts**

**1. Explain each part of this function signature:**
```python
@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
```
- [ ] My answer:

**2. Why do we have separate `UserCreate` and `UserResponse` Pydantic schemas instead of just one?**
- [ ] My answer:

**3. Walk through what happens when someone POSTs to `/api/v1/users/` - list every step from HTTP request to database commit.**
- [ ] My answer:

**4. What's the difference between `db.add()`, `db.commit()`, and `db.refresh()`? Why do we need all three?**
- [ ] My answer:

**5. Add proper error handling to the create_user function for database errors. Show your code.**
- [ ] My code:
```python
# Your answer here
```

**6. Explain the `set_primary_account` endpoint logic. Why do we need to unset other primary accounts first?**
- [ ] My answer:

**7. Test via Swagger UI (http://localhost:8000/docs):**
   - Create a landlord user
   - Create a bank account for them
   - Set it as primary
   - Show the JSON responses
- [ ] My test results:

**8. What HTTP status codes should you return for:**
   - User not found?
   - Duplicate email?
   - Database connection error?
   - Successful creation?
- [ ] My answers:

---

## **DAY 3: Properties & Leases APIs**

**1. Why do we validate that a user has the "landlord" role before letting them create a property?**
- [ ] My answer:

**2. Explain the `calculate_first_payment_date` function logic. Give examples:**
   - Lease starts Feb 5, due day is 1st
   - Lease starts Feb 5, due day is 15th
- [ ] My answer:

**3. Why do we automatically create a PaymentSchedule when creating a Lease?**
- [ ] My answer:

**4. Write a Pydantic validator to ensure `rent_amount` is positive and less than $50,000.**
- [ ] My code:
```python
@validator('rent_amount')
def validate_rent(cls, v):
    # Your answer here
```

**5. Write SQL/SQLAlchemy queries to:**
   - Get all active leases for a property
   - Get all properties owned by a landlord with their lease count
   - Find all payment schedules due in the next 7 days
- [ ] My queries:

**6. Describe the complete flow to create a lease with all required entities. What order must things be created?**
- [ ] My answer:

**7. Test the full integration: Create landlord → property → renter → bank accounts → lease. Did it work? Show any errors.**
- [ ] My result:

**8. What additional fields would you add to the Lease model for a production system? Why?**
- [ ] My answer:

---

## **DAY 4: Payment Initiation & Idempotency ⭐⭐⭐**

**1. What is idempotency? Explain why it's critical for payment systems using a real-world example (user clicking "Pay" twice).**
- [ ] My answer:

**2. Explain how the unique database constraint on `idempotency_key` prevents duplicate payments even with concurrent requests.**
- [ ] My answer:

**3. Walk through the `initiate_payment` function step-by-step. What happens at each stage?**
- [ ] My answer:

**4. Explain this code block - why do we check for existing transaction again inside the except?**
```python
try:
    db.add(db_transaction)
    db.commit()
except IntegrityError:
    db.rollback()
    existing_txn = db.query(Transaction).filter(
        Transaction.idempotency_key == transaction_data.idempotency_key
    ).first()
    if existing_txn:
        return existing_txn
    raise
```
- [ ] My answer:

**5. What is event sourcing? Why did we create a `transaction_events` table? What can we do with it?**
- [ ] My answer:

**6. Test idempotency:**
   - Send the same payment request twice (same idempotency key)
   - Show both responses
   - Are the transaction IDs identical?
- [ ] My test results:

**7. Explain the retry logic for failed payments:**
   - Why limit to 3 retries?
   - What is exponential backoff?
   - Calculate the retry delays (show formula)
- [ ] My answer:

**8. How would you explain idempotency to:**
   - A non-technical product manager?
   - A technical interviewer at Root?
- [ ] My answers:

**9. Write a query to find all transactions that have been retried at least once.**
- [ ] My query:

**10. What happens if:**
   - Server crashes after creating transaction but before commit?
   - Two requests with same idempotency key arrive at exactly the same millisecond?
   - Database becomes unavailable mid-transaction?
- [ ] My answers:

---

## **DAY 5: Transaction State Machine & Async Processing ⭐⭐⭐**

**1. What is Celery? What is Redis? How do they work together in this system?**
- [ ] My answer:

**2. Draw the architecture: API → Transaction Created → Celery Task Queue → Worker → Database Update**
- [ ] My diagram:

**3. Walk through what happens when a payment enters the `process_payment_async` Celery task. List every step.**
- [ ] My answer:

**4. List all valid transaction status transitions. Which transitions are NOT allowed and why?**
- [ ] My state machine diagram:

**5. Why do we simulate different processing times for different payment rails? What are the simulated times?**
- [ ] My answer:
- INSTANT:
- SAME_DAY_ACH:
- STANDARD_ACH:
- WIRE:

**6. Explain the `DatabaseTask` base class pattern. Why do we need `after_return` to close database sessions?**
- [ ] My answer:

**7. Start Celery worker and create a payment with INSTANT rail:**
   - Show Celery logs
   - How long did it take?
   - What status transitions occurred?
- [ ] My results:

**8. Create a payment that fails. Show:**
   - The failure_reason in database
   - Whether retry was triggered
   - The events logged
- [ ] My results:

**9. What happens if:**
   - Celery worker crashes while processing a payment?
   - Two workers pick up the same task?
   - Database is unavailable when task runs?
- [ ] My answers:

**10. How would you scale this system to handle 10x more payments? Name 3 specific changes.**
- [ ] My answer:

---

## **DAY 6: Recurring Payment Scheduler**

**1. What is Celery Beat? How is it different from Celery workers?**
- [ ] My answer:

**2. Explain the cron expression `crontab(hour=9, minute=0)`. Why run at 9 AM instead of midnight?**
- [ ] My answer:

**3. Walk through the `process_due_payments` task:**
   - What SQL query finds due payments?
   - How does it prevent duplicates?
   - What happens if a renter has no primary bank account?
- [ ] My answer:

**4. Explain the idempotency key format: `f"scheduled-{schedule.id}-{today.isoformat()}"`**
   - Why include the schedule ID?
   - Why include the date?
   - What happens if this task runs twice in one day?
- [ ] My answer:

**5. Write a SQL query to find all payment schedules due today.**
- [ ] My query:

**6. Test the scheduled payment flow:**
   - Create a lease with payment due today
   - Manually trigger `process_due_payments`
   - Was the payment created?
   - Show the transaction record
- [ ] My results:

**7. What does `send_payment_reminders` do? Why 3 days before instead of 1 day or 1 week?**
- [ ] My answer:

**8. In production, how would you:**
   - Actually send email/SMS reminders?
   - Ensure scheduled tasks don't get missed if server crashes?
   - Monitor that Celery Beat is running correctly?
- [ ] My answers:

---

## **DAY 7: Payment Reconciliation System ⭐⭐**

**1. What is payment reconciliation? Who uses it and why is it critical for financial systems?**
- [ ] My answer:

**2. Explain the `generate_monthly_report` function:**
   - What does "expected payments" mean?
   - What does "actual payments" mean?
   - How is discrepancy calculated?
- [ ] My answer:

**3. Write out the SQL queries that calculate:**
   - Expected payments for a month
   - Actual completed payments for a month
- [ ] My SQL:

**4. Explain this line: `set(expected_dict.keys()) | set(actual_dict.keys())`**
   - What does the `|` operator do?
   - Why do we need this?
- [ ] My answer:

**5. Test the reconciliation endpoints:**
   - Monthly report for current month - what's the total discrepancy?
   - Failed payments summary - most common failure reason?
   - Payment rail performance - which rail has highest success rate?
- [ ] My results:

**6. How would you use the failed payments data to improve the system? Give 3 specific examples.**
- [ ] My answer:

**7. Write queries to:**
   - Find the most common failure reason
   - Calculate average processing time by payment rail
   - Find all leases with payment discrepancies
- [ ] My queries:

**8. A landlord reports missing rent for February. Walk through how you'd investigate using reconciliation.**
- [ ] My process:

**9. Which queries would benefit from database indexes? Create index statements.**
- [ ] My SQL:

**10. How would you optimize monthly reports for 1 million transactions? Name 3 techniques.**
- [ ] My answer:

---

## **DAY 8: Mock Payment Gateway & Documentation**

**1. What does `MockPaymentGateway` simulate? What would replace it in production?**
- [ ] My answer:

**2. Explain the trade-offs between payment rails:**

| Rail | Speed | Cost | Use Case |
|------|-------|------|----------|
| INSTANT | | | |
| SAME_DAY_ACH | | | |
| STANDARD_ACH | | | |
| WIRE | | | |

- [ ] My table:

**3. Why simulate a 10% failure rate? What failure types are simulated and how are they handled differently?**
- [ ] My answer:

**4. How does this project demonstrate Root's value proposition of "no intermediaries"?**
- [ ] My answer:

**5. Test the payment rails comparison endpoint. Which rail would you recommend for:**
   - Emergency rent payment?
   - Regular monthly rent?
   - Large security deposit?
- [ ] My answers:

**6. Write a comprehensive README section explaining:**
   - What this project does
   - Key technical decisions (PostgreSQL, idempotency, event sourcing)
   - How to run it
- [ ] My README:

**7. Prepare to explain in an interview:**
   - Database schema design (draw it)
   - Idempotency implementation
   - Transaction state machine
   - Reconciliation logic
- [ ] Practice explaining each (time yourself - 2 min each)

**8. What would you add to make this production-ready? List 5 features/improvements.**
- [ ] My list:

---

## **BONUS: Final Integration Questions**

**Answer these after completing all days:**

**1. Walk an interviewer through the complete payment flow from user clicking "Pay" to money transferred. Include every component (API, database, Celery, etc.).**
- [ ] My explanation:

**2. Explain how you would handle these scenarios:**
   - User tries to pay twice in rapid succession
   - Payment stuck in PROCESSING for 24 hours
   - 100 payments failing with "Insufficient Funds"
   - Database replica lag causing stale reads
- [ ] My answers:

**3. Draw the complete architecture diagram including:**
   - API layer
   - Database
   - Celery workers
   - Redis
   - Scheduled tasks
   - External payment gateway (simulated)
- [ ] My diagram:

**4. What SQL queries would you optimize first if this system had 1M transactions/day? Write the index creation statements.**
- [ ] My optimization plan:

**5. If you had 2 more weeks, what features would you add and why?**
- [ ] My roadmap:

---

## **Self-Assessment Rubric**

For each day, rate yourself:

- ⭐⭐⭐ **Mastered:** Could explain to interviewer confidently, understand edge cases
- ⭐⭐ **Understood:** Can explain the concept, might struggle with edge cases  
- ⭐ **Needs Review:** Copied the code, don't fully understand why

**Goal: All days at ⭐⭐⭐ before interview**

If you score ⭐ or ⭐⭐, revisit that day's code and these questions before moving forward.