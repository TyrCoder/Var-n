# Rider Transactions - Data Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RIDER DASHBOARD (Frontend)                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
                    ┌───────────────────────────┐
                    │   Mark as DELIVERED       │
                    │   (User Action)           │
                    └───────────────────────────┘
                                    │
                                    ↓
                    ┌───────────────────────────┐
                    │  /api/rider/               │
                    │  update-delivery-status   │
                    │  (POST)                   │
                    └───────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       Backend Processing                             │
├─────────────────────────────────────────────────────────────────────┤
│  1. Get rider info from session (user_id → rider_id)               │
│  2. Verify shipment exists & seller confirmed                       │
│  3. Update shipment status to 'delivered'                          │
│  4. Get order details (order_id, total_amount)                     │
│  5. Calculate earning = total_amount × 0.15                        │
│  6. Create individual transaction:                                  │
│     INSERT INTO rider_transactions {                                │
│       rider_id, order_id, shipment_id, earning_amount,             │
│       commission_rate, status='completed', completed_at=NOW()      │
│     }                                                                │
│  7. Update order status to 'delivered'                             │
│  8. Update rider profile:                                           │
│     - total_deliveries += 1                                         │
│     - earnings += earning_amount                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABASE UPDATES                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  shipments table:                                                   │
│  ├─ status: 'delivered'                                            │
│  ├─ delivered_at: NOW()                                            │
│  └─ rider_id: [assigned rider]                                    │
│                                                                      │
│  orders table:                                                      │
│  └─ order_status: 'delivered'                                      │
│                                                                      │
│  riders table:                                                      │
│  ├─ total_deliveries: +1                                           │
│  └─ earnings: +[earning_amount]                                    │
│                                                                      │
│  ★ rider_transactions table (NEW):                                 │
│  ├─ id: [auto]                                                     │
│  ├─ rider_id: [RIDER'S ID]                                        │
│  ├─ order_id: [order id]                                          │
│  ├─ shipment_id: [shipment id]                                    │
│  ├─ earning_amount: [calculated 15%]                              │
│  ├─ commission_rate: 15.00                                         │
│  ├─ status: 'completed'                                            │
│  ├─ completed_at: NOW()                                            │
│  └─ created_at: NOW()                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  Response to Frontend                                │
├─────────────────────────────────────────────────────────────────────┤
│  {                                                                   │
│    "success": true,                                                 │
│    "message": "Delivery status updated to delivered"               │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
                    ┌───────────────────────────┐
                    │  Dashboard Refreshes      │
                    │  Earnings Updated ✓       │
                    └───────────────────────────┘
```

---

## Query Flow - Getting Rider Earnings

```
Rider Dashboard → Earnings Section
        │
        ↓
  /api/rider/earnings (GET)
        │
        ├─→ Get rider_id from session
        │
        ├─→ Query rider_transactions table:
        │    SELECT SUM(earning_amount)
        │    FROM rider_transactions
        │    WHERE rider_id = [CURRENT_RIDER]
        │    AND status = 'completed'
        │    AND completed_at >= [DATE_RANGE]
        │
        ├─→ Calculate breakdowns:
        │    - base_fare = total × 0.70
        │    - tips = total × 0.20
        │    - bonuses = total × 0.10
        │
        └─→ Return earnings data
              {
                "today_earnings": 150.00,
                "weekly_earnings": 1050.00,
                "monthly_earnings": 5250.00,
                "breakdown": {
                  "base_fare": 735.00,
                  "tips": 210.00,
                  "bonuses": 105.00
                }
              }
```

---

## Multiple Riders - Isolation Guarantee

```
Scenario: 3 riders, 3 orders, same time

Order #1 (₱500)        Order #2 (₱800)        Order #3 (₱600)
     │                      │                      │
     ↓                      ↓                      ↓
  Rider A              Rider B                Rider C
     │                      │                      │
     └──────────────────────┴──────────────────────┘
              All marked DELIVERED
                    │
                    ↓
        ┌───────────────────────────┐
        │  3 INDIVIDUAL ENTRIES in  │
        │  rider_transactions       │
        └───────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┐
        ↓           ↓           ↓           ↓
    Transaction  Transaction  Transaction
    ────────────────────────────────────────────
    rider_id: 1  rider_id: 2  rider_id: 3
    order_id: 1  order_id: 2  order_id: 3
    earning: 75  earning: 120  earning: 90
    ────────────────────────────────────────────
    
    Rider A Earnings: ₱75.00
    Rider B Earnings: ₱120.00
    Rider C Earnings: ₱90.00
    
    ✅ COMPLETELY ISOLATED - No mixing!
```

---

## Transaction Lifecycle

```
┌──────────────────┐
│  Order Created   │
│  (To Pay)        │
└────────┬─────────┘
         │ (Status: pending)
         │
         ↓
┌──────────────────┐
│ Seller Confirms  │
│ & Assigns Rider  │
└────────┬─────────┘
         │ (Status: pending)
         │
         ↓
┌──────────────────┐
│  Rider Accepts   │
│  Order           │
└────────┬─────────┘
         │ (Status: picked_up)
         │
         ↓
┌──────────────────┐
│ Rider In Transit │
└────────┬─────────┘
         │ (Status: in_transit)
         │
         ↓
┌──────────────────┐
│ Rider Out for    │
│ Delivery         │
└────────┬─────────┘
         │ (Status: out_for_delivery)
         │
         ↓
┌──────────────────────────────────────┐
│  Rider Marks DELIVERED ⭐            │
│                                      │
│  ✅ RIDER TRANSACTION CREATED HERE:  │
│  ────────────────────────────────    │
│  - rider_id: [assigned rider]       │
│  - order_id: [this order]           │
│  - earning_amount: [15% calc]       │
│  - status: 'completed'              │
│  - completed_at: NOW()              │
│                                      │
│  ✅ ORDER STATUS: delivered          │
│  ✅ RIDER PROFILE UPDATED:          │
│     - total_deliveries += 1         │
│     - earnings += earning_amount    │
└──────────────────────────────────────┘
         │ (Status: delivered)
         │
         ↓
┌──────────────────┐
│ Order Complete   │
│ (Completed)      │
└──────────────────┘
```

---

## Data Isolation Example

```
BEFORE (Problem):
──────────────────
rider_id | order_id | earning
    1    |    1    |  75.00
    1    |    2    | 120.00
    2    |    3    |  90.00
    1    |    4    | 100.00
    2    |    5    |  60.00

Rider A earnings: ₱75 + ₱120 + ₱100 = ₱295 ✓
Rider B earnings: ₱90 + ₱60 = ₱150 ✓

AFTER (Fixed):
──────────────
rider_transactions table:
id | rider_id | order_id | earning
 1 |    1     |    1     |  75.00  ← Rider 1's transaction
 2 |    1     |    2     | 120.00  ← Rider 1's transaction
 3 |    2     |    3     |  90.00  ← Rider 2's transaction
 4 |    1     |    4     | 100.00  ← Rider 1's transaction
 5 |    2     |    5     |  60.00  ← Rider 2's transaction

When Rider 1 queries earnings:
  SELECT SUM(earning_amount)
  FROM rider_transactions
  WHERE rider_id = 1
  Result: ₱295 ✓

When Rider 2 queries earnings:
  SELECT SUM(earning_amount)
  FROM rider_transactions
  WHERE rider_id = 2
  Result: ₱150 ✓

✅ ISOLATED - Each rider sees only their own transactions!
```

---

## API Endpoints Using rider_transactions

### 1. Mark Delivery as Completed
```
POST /api/rider/update-delivery-status
Body: {
  shipment_id: 123,
  status: 'delivered'
}

Action: Creates rider_transactions entry + Updates orders + Updates riders
```

### 2. Get Rider Earnings
```
GET /api/rider/earnings

Returns:
{
  today_earnings: 75.00,
  weekly_earnings: 525.00,
  monthly_earnings: 2625.00,
  breakdown: { base_fare, tips, bonuses }
}

Source: SUM(earning_amount) FROM rider_transactions WHERE rider_id = ? ...
```

### 3. Get Rider Delivery History
```
GET /api/rider/delivery-history

Returns array of completed deliveries with:
{
  order_number: "ORD-001",
  customer_name: "John Doe",
  transaction_id: 123,
  earning_amount: 75.00,
  commission_rate: 15.00,
  completed_at: "2025-11-26 14:30:00",
  ...
}

Source: JOIN rider_transactions WHERE rider_id = ? AND status = 'completed'
```

---

## Key Guarantees

✅ **One Transaction Per Delivery**: Only 1 entry created per delivery completion
✅ **Rider Isolation**: Each rider_id sees only their own transactions
✅ **Accurate Calculations**: earning_amount stored (not calculated from orders)
✅ **Complete History**: All transactions permanently recorded
✅ **Indexed Performance**: Fast lookups by rider_id, order_id, or date
✅ **Audit Trail**: transaction_id + timestamps for verification

---

## Database Indexes for Performance

```
rider_transactions table indexes:
├─ PRIMARY KEY (id)                    ← Fast lookup by transaction
├─ INDEX idx_rider (rider_id)          ← Fast lookup by rider
├─ INDEX idx_order (order_id)          ← Fast lookup by order
├─ INDEX idx_status (status)           ← Fast lookup by status
└─ INDEX idx_created (created_at)      ← Fast date range queries

Example fast queries:
  WHERE rider_id = 1 AND status = 'completed'
  WHERE completed_at BETWEEN date1 AND date2
  WHERE order_id = 100
```

---

## Status: COMPLETE ✅

All rider transactions are now:
- ✅ Individual per rider
- ✅ Isolated from other riders
- ✅ Permanently recorded
- ✅ Indexed for performance
- ✅ Queryable by earnings endpoints

**Result**: Each rider has complete, separate earning history!
