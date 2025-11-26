# Rider Individual Transactions Implementation

## Overview
Fixed the issue where riders were sharing transaction records. Now each rider has their own individual transaction record for each order they complete.

## What Was Changed

### 1. Database Schema - New `rider_transactions` Table
**Location**: `app.py` line ~422

Created new table to track individual rider earnings per delivery:

```sql
CREATE TABLE IF NOT EXISTS rider_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rider_id INT NOT NULL,
    order_id INT NOT NULL,
    shipment_id INT NOT NULL,
    earning_amount DECIMAL(10,2) NOT NULL,
    commission_rate DECIMAL(5,2) DEFAULT 15.00,
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,
    INDEX idx_rider (rider_id),
    INDEX idx_order (order_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
)
```

**Benefits:**
- Each rider has separate, unique transaction records
- Tracks earning amount and commission rate per transaction
- Supports status tracking (pending → completed → cancelled)
- Indexed for fast lookups by rider, order, or date

---

### 2. Delivery Completion - Create Individual Transactions
**Function**: `api_rider_update_delivery_status()` 
**Location**: `app.py` line ~8800

**What it does now:**
When a rider marks a delivery as "delivered":

1. ✅ Retrieves order details (order_id, total_amount)
2. ✅ Calculates earning (15% of order total)
3. ✅ Creates individual rider transaction record with:
   - rider_id (which rider earned it)
   - order_id (which order it's from)
   - shipment_id (delivery reference)
   - earning_amount (calculated 15%)
   - commission_rate (15%)
   - status (completed)
   - completed_at (timestamp)
4. ✅ Updates order status to 'delivered'
5. ✅ Updates rider's profile:
   - Increments total_deliveries
   - Adds earning_amount to riders.earnings

**Code Example:**
```python
# Calculate rider earning (15% commission)
earning_amount = order['total_amount'] * 0.15

# Create individual rider transaction record
cursor.execute('''
    INSERT INTO rider_transactions (
        rider_id, order_id, shipment_id, earning_amount, 
        commission_rate, status, completed_at
    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
''', (rider_db_id, order['id'], shipment_id, earning_amount, 15.00, 'completed'))

# Update rider's profile earnings
cursor.execute('''
    UPDATE riders
    SET total_deliveries = total_deliveries + 1,
        earnings = earnings + %s
    WHERE id = %s
''', (earning_amount, rider_db_id))
```

---

### 3. Earnings Endpoint - Query Individual Transactions
**Function**: `api_rider_earnings()`
**Location**: `app.py` line ~8470

**Changed from:**
- Querying shipments table and calculating earnings on-the-fly
- Risk of counting same order multiple times if multiple riders were assigned

**Changed to:**
- Querying `rider_transactions` table directly
- Each rider's transactions are isolated
- Much faster and more accurate

**Earnings Calculated:**
```python
# Today's earnings
SELECT SUM(earning_amount) FROM rider_transactions 
WHERE rider_id = ? AND status = 'completed' 
AND DATE(completed_at) = CURDATE()

# Weekly earnings (last 7 days)
SELECT SUM(earning_amount) FROM rider_transactions 
WHERE rider_id = ? AND status = 'completed' 
AND completed_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)

# Monthly earnings (current month)
SELECT SUM(earning_amount) FROM rider_transactions 
WHERE rider_id = ? AND status = 'completed' 
AND YEAR(completed_at) = YEAR(CURDATE())
AND MONTH(completed_at) = MONTH(CURDATE())
```

---

### 4. Delivery History - Show Individual Transactions
**Function**: `api_rider_delivery_history()`
**Location**: `app.py` line ~8415

**Now includes:**
- `transaction_id` - unique transaction ID for each delivery
- `earning_amount` - exact amount rider earned for this delivery
- `commission_rate` - commission percentage (15%)
- `completed_at` - when the transaction was completed

**SQL Query:**
```sql
JOIN rider_transactions rt ON rt.shipment_id = s.id AND rt.rider_id = ?
WHERE rt.status = 'completed'
ORDER BY rt.completed_at DESC
```

---

## How It Works - Workflow

### Scenario: Rider Completes a Delivery

**Step 1: Rider Accepts Order**
- Status: `assigned_to_rider` → `picked_up`
- No transaction created yet (just status update)

**Step 2: Rider Marks as In Transit**
- Status: `picked_up` → `in_transit`
- No transaction created yet (just status update)

**Step 3: Rider Marks as Out for Delivery**
- Status: `in_transit` → `out_for_delivery`
- No transaction created yet (just status update)

**Step 4: Rider Marks as Delivered** ⭐ **TRANSACTION CREATED HERE**
- Status: `out_for_delivery` → `delivered`
- ✅ Individual transaction record created in `rider_transactions`
- ✅ earning_amount calculated (15% of order total)
- ✅ status set to 'completed'
- ✅ completed_at set to current timestamp
- ✅ rider.total_deliveries incremented
- ✅ rider.earnings updated

---

## Data Flow Example

**Scenario:** Order total = ₱1,000

```
Order #TEST-001 | Amount: ₱1,000
  ↓
Rider 1 accepts order (picked_up)
  ↓
Rider 1 in transit (in_transit)
  ↓
Rider 1 out for delivery (out_for_delivery)
  ↓
Rider 1 marks DELIVERED ✅
  ↓
INDIVIDUAL TRANSACTION CREATED:
  {
    rider_id: 5,
    order_id: 123,
    shipment_id: 456,
    earning_amount: 150.00,  ← ₱1,000 × 15%
    commission_rate: 15.00,
    status: 'completed',
    completed_at: 2025-11-26 14:30:00
  }
  ↓
Rider 1's Profile Updated:
  - total_deliveries: 15 → 16
  - earnings: 2,100.00 → 2,250.00

Rider 2's Profile: UNTOUCHED (different rider!)
Rider 3's Profile: UNTOUCHED (different rider!)
```

---

## Benefits

✅ **Individual Tracking**: Each rider's earnings are separate and isolated
✅ **Accurate Reporting**: No cross-contamination between riders
✅ **Easy Auditing**: Each transaction has rider_id, order_id, and timestamp
✅ **Flexible Status**: Can mark transactions as pending/completed/cancelled
✅ **Performance**: Indexed queries for fast lookups
✅ **Historical Data**: All transactions permanently recorded
✅ **Commission Tracking**: Records the commission rate used (allows future changes)

---

## Testing

### Test Case 1: Single Rider, Single Order
1. Create order (amount: ₱500)
2. Assign to Rider A
3. Rider A completes delivery
4. **Expected**: One transaction in `rider_transactions` with earning_amount = 75.00
5. **Verify**: Rider A earnings show ₱75.00

### Test Case 2: Multiple Riders, One Order Each
1. Create Order #1 (amount: ₱500) → Rider A → earns ₱75.00
2. Create Order #2 (amount: ₱800) → Rider B → earns ₱120.00
3. Both riders complete deliveries
4. **Expected**: Two separate transactions
5. **Verify**: 
   - Rider A earnings: ₱75.00 (only their transactions)
   - Rider B earnings: ₱120.00 (only their transactions)

### Test Case 3: Same Rider, Multiple Orders
1. Order #1: ₱500 → Rider A → ₱75.00
2. Order #2: ₱600 → Rider A → ₱90.00
3. Order #3: ₱700 → Rider A → ₱105.00
4. All completed
5. **Expected**: Three transactions all with rider_id = Rider A
6. **Verify**: Rider A earnings = ₱270.00 (sum of all three)

---

## Migration Notes

- ✅ Table created on app startup (if not exists)
- ✅ No data loss (new table only)
- ✅ Backward compatible (old shipments still queryable)
- ✅ All new deliveries will use new system
- ✅ Old delivered orders won't have transactions (only new ones)

**Optional**: To backfill old transactions:
```python
# Insert transactions for all previously delivered orders
INSERT INTO rider_transactions (rider_id, order_id, shipment_id, earning_amount, status, completed_at)
SELECT r.id, o.id, s.id, (o.total_amount * 0.15), 'completed', s.delivered_at
FROM orders o
JOIN shipments s ON s.order_id = o.id
JOIN riders r ON s.rider_id = r.id
WHERE s.status = 'delivered' 
AND s.delivered_at IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM rider_transactions rt WHERE rt.shipment_id = s.id)
```

---

## Files Modified

1. **app.py**
   - Line ~422: Added `rider_transactions` table creation
   - Line ~8415: Updated `api_rider_delivery_history()` function
   - Line ~8470: Updated `api_rider_earnings()` function
   - Line ~8800: Updated `api_rider_update_delivery_status()` function

## Summary

Each rider now has **individual, isolated transaction records** for each delivery. When a rider completes a delivery, a unique transaction is created with:
- Their rider ID
- Order and shipment details
- Exact earning amount
- Completion timestamp

This ensures rider transactions are never shared or mixed up, providing accurate earning tracking per rider.
