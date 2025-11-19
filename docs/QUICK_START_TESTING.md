# Quick Start - Testing Order Management System

## 🚀 Quick Test (5 minutes)

### Test 1: Place an Order
```
1. Open: http://localhost:5000/index
2. Login as buyer
3. Click product → Add to Cart
4. Cart → Checkout
5. Fill shipping info + Select payment → Place Order
6. ✅ See order confirmation with PROGRESS TRACKER
```

### Test 2: Seller Updates Status
```
1. Open NEW tab: http://localhost:5000/seller-dashboard (as seller)
2. Left sidebar → Orders
3. Click "All Orders" filter
4. Find your order from Test 1
5. Click [Update] button
6. Select "Confirmed" → Save
7. Watch confirmation page update automatically (within 30 seconds)
```

### Test 3: Check Buyer Dashboard
```
1. Go back to buyer tab
2. Go to "My Orders" section
3. ✅ See your order with updated status badge
4. Click "View Details" → See progress bar with new position
```

---

## 📋 Status Progression

```
START → ⏳ PENDING ──(seller clicks)──→ ✔️ CONFIRMED
           │                                 │
           └─────────(buyer sees)───────────┘
           
CONFIRMED → 🔄 PROCESSING ──(seller)──→ 📦 SHIPPED
           │                               │
           └─────────(buyer sees)────────┘

SHIPPED → ✅ DELIVERED (Final Status)
           │
           └─────────(buyer sees)────────→ Show green checkmark
```

---

## 🔍 What Happens Behind the Scenes

### When Buyer Places Order:
```sql
INSERT INTO orders (order_status='pending', created_at=NOW(), ...)
INSERT INTO order_items (order_id, product_id, ...)
INSERT INTO shipments (order_id='pending', ...)
```

### When Seller Updates Status:
```sql
UPDATE orders SET order_status='confirmed', updated_at=NOW() WHERE id=...
-- Buyer's page polls every 30 seconds and gets new status
```

### When Buyer Views Order:
```
JavaScript: setInterval(updateOrderStatus, 30000)
Fetches: GET /api/order-status/{order_id}
Updates: Progress bar moves to new step
Shows: Status message updates
```

---

## 🎨 Visual Status Flow

### Order Confirmation Page (Buyer)
```
Order #: ORD-1731945632-8573

📦 Order Status
─────────────────────────────────────────
⏳ → ✔️ → 🔄 → 📦 → ✅
PENDING  CONFIRMED  PROCESSING  SHIPPED  DELIVERED

⏳ Your order has been received. 
  Waiting for seller confirmation...
```

### My Orders List (Buyer)
```
[⏳ PENDING]   Order #ORD-123  Nov 18  2 items  ₱1,497
[✔️ CONFIRMED] Order #ORD-456  Nov 17  1 item   ₱599
[✅ DELIVERED] Order #ORD-789  Nov 16  3 items  ₱2,299
```

### Seller Orders (Seller Dashboard)
```
Filters: [All] [⏳ Pending] [✔️ Confirmed] [🔄 Processing] [📦 Shipped]

Order #1 | Customer: John Doe | 2 items | ₱1,497 | ⏳ Pending
[View] [Update]

Order #2 | Customer: Jane Smith | 1 item | ₱599 | ✔️ Confirmed  
[View] [Update]
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Status not updating | Wait 30 seconds, page polls automatically |
| Can't see order | Seller must own product in order |
| Update button missing | Order must exist and have valid status |
| Progress bar empty | Order must be in database with order_id |
| Status dropdown empty | Invalid order_id or permission issue |

---

## 📡 API Testing

### Get Order Status
```bash
curl -X GET http://localhost:5000/api/order-status/1 \
  -H "Cookie: session=..." 
```

### Get User Orders
```bash
curl -X GET http://localhost:5000/api/user-orders-detailed \
  -H "Cookie: session=..."
```

### Update Order Status
```bash
curl -X POST http://localhost:5000/seller/update-order-status \
  -d "order_id=1&new_status=confirmed" \
  -H "Cookie: session=..."
```

---

## 🎯 Success Criteria

✅ **Test 1 Passed:** Order created with PENDING status
✅ **Test 2 Passed:** Seller can change order status
✅ **Test 3 Passed:** Buyer sees real-time status updates
✅ **Test 4 Passed:** Progress bar moves through stages
✅ **Test 5 Passed:** My Orders shows correct status badges

---

## 🚨 Important Notes

1. **Orders are Multi-Tenant**: Sellers only see their orders
2. **Status Updates are Instant**: Database updates immediately
3. **Buyer Polling is 30 seconds**: Auto-refresh on buyer's page
4. **Timestamp Tracking**: Each update logs the time
5. **No Manual Refresh Needed**: Page auto-updates live

---

## 📊 Database Check

### See All Orders
```sql
SELECT id, order_number, order_status, user_id, seller_id, 
       created_at, updated_at FROM orders ORDER BY created_at DESC;
```

### See Order Items
```sql
SELECT * FROM order_items WHERE order_id = 1;
```

### See Status Timeline
```sql
SELECT id, order_number, order_status, updated_at 
FROM orders WHERE order_id = 1;
```

---

## 🎬 Demo Video Steps

1. Open browser dev tools (F12)
2. Go to Console tab
3. Place order → Watch network requests
4. See POST /api/place-order ✅
5. See GET /api/order-status polling every 30s ✅
6. Update status → See response in network ✅
7. Buyer page updates automatically ✅

---

## 💡 Key Features Implemented

| Feature | Location | Status |
|---------|----------|--------|
| Order Creation | /checkout | ✅ Working |
| Seller Dashboard Orders | /seller-dashboard | ✅ Working |
| Real-time Tracking | order_confirmation | ✅ Working |
| Status Updates | /seller/update-order-status | ✅ Working |
| Buyer Dashboard | indexLoggedIn.html | ✅ Working |
| Progress Visualization | Progress bar | ✅ Working |
| Email Notifications | - | 🔜 Future |
| SMS Alerts | - | 🔜 Future |

---

## 📞 Support

For issues or questions:
1. Check console for errors (F12)
2. Verify seller owns product in order
3. Check database for order_status values
4. Verify session cookies are set
5. Check order timestamps in database
