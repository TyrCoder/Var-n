# Technical Reference - Order Confirmation Flow API

## Database Schema

### Orders Table - New Columns

```sql
ALTER TABLE orders
ADD COLUMN rider_id INT NULL AFTER seller_id,
ADD COLUMN seller_confirmed_rider BOOLEAN DEFAULT FALSE AFTER rider_id,
ADD COLUMN buyer_approved_rider BOOLEAN DEFAULT FALSE AFTER seller_confirmed_rider,
ADD FOREIGN KEY (rider_id) REFERENCES users(id) ON DELETE SET NULL,
ADD INDEX idx_rider (rider_id);
```

### Column Definitions

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `rider_id` | INT NULL | NULL | ID of the rider assigned to deliver this order |
| `seller_confirmed_rider` | BOOLEAN | FALSE | Seller has approved the assigned rider |
| `buyer_approved_rider` | BOOLEAN | FALSE | Buyer has approved the assigned rider |

---

## API Endpoints

### 1. POST /seller/confirm-order

**Purpose:** Seller confirms an order (pending → confirmed)

**Authentication:** Required (logged in as seller)

**Request:**
```json
{
  "order_id": 123
}
```

**Response - Success (200):**
```json
{
  "success": true,
  "message": "Order confirmed! Waiting for a rider to accept."
}
```

**Response - Errors:**
```json
{
  "success": false,
  "error": "Not logged in"
}
```

**Status Codes:**
- 200: Success
- 400: Missing order_id
- 401: Not logged in
- 403: Not a seller or not owner of products in order
- 500: Server error

**Changes Made:**
- Updates `orders.order_status = 'confirmed'`
- Updates `orders.updated_at = NOW()`

---

### 2. POST /seller/approve-rider-for-delivery

**Purpose:** Seller approves the assigned rider for delivery

**Authentication:** Required (logged in as seller)

**Request:**
```json
{
  "order_id": 123,
  "rider_id": 45
}
```

**Response - Success (200):**
```json
{
  "success": true,
  "message": "Rider approved for delivery!"
}
```

**Status Codes:**
- 200: Success
- 400: Missing parameters
- 401: Not logged in
- 403: Not a seller or not owner
- 500: Server error

**Changes Made:**
- Updates `orders.seller_confirmed_rider = TRUE`
- Updates `orders.updated_at = NOW()`

---

### 3. GET /api/rider-details/<rider_id>

**Purpose:** Get rider details for display in approval modal

**Authentication:** Required (any logged-in user)

**Parameters:**
- `rider_id` (URL path parameter): ID of the rider

**Response - Success (200):**
```json
{
  "success": true,
  "rider": {
    "id": 5,
    "first_name": "Juan",
    "last_name": "Dela Cruz",
    "phone": "+63 917 123 4567",
    "rating": 4.8,
    "profile_image_url": "/static/images/profiles/riders/5.jpg"
  }
}
```

**Response - Not Found (404):**
```json
{
  "success": false,
  "error": "Rider not found"
}
```

**Status Codes:**
- 200: Success
- 401: Not logged in
- 404: Rider not found
- 500: Server error

**Query:**
```sql
SELECT 
  u.id, u.first_name, u.last_name, u.phone,
  r.rating, r.profile_image_url
FROM users u
LEFT JOIN riders r ON u.id = r.user_id
WHERE u.id = %s AND u.role = 'rider'
```

---

### 4. GET /api/order-rider-info/<order_id>

**Purpose:** Get rider ID for an order (used by buyer to fetch rider details)

**Authentication:** Required (must be order buyer)

**Parameters:**
- `order_id` (URL path parameter): ID of the order

**Response - Success (200):**
```json
{
  "success": true,
  "rider_id": 45
}
```

**Response - Errors:**
```json
{
  "success": false,
  "error": "Order not found"
}
```

or

```json
{
  "success": false,
  "error": "No rider assigned"
}
```

**Status Codes:**
- 200: Success
- 401: Not logged in
- 404: Order not found
- 400: No rider assigned
- 500: Server error

---

### 5. POST /api/approve-rider-delivery

**Purpose:** Buyer approves rider for delivery

**Authentication:** Required (logged in as buyer)

**Request Body (JSON):**
```json
{
  "order_id": 123,
  "rider_id": 45
}
```

**Response - Success (200):**
```json
{
  "success": true,
  "message": "Rider approved for delivery!"
}
```

**Status Codes:**
- 200: Success
- 400: Missing parameters
- 401: Not logged in
- 404: Order not found
- 500: Server error

**Changes Made:**
- Updates `orders.buyer_approved_rider = TRUE`
- Updates `orders.updated_at = NOW()`

---

## Updated Endpoints

### GET /api/order-status/<order_id>

**Changes:**
- Added `rider_id`, `seller_confirmed_rider`, `buyer_approved_rider` to response

**New Response Fields:**
```json
{
  "success": true,
  "order": {
    "id": 1,
    "order_number": "ORD-1234567890-1234",
    "status": "confirmed",
    "status_label": "Confirmed",
    "status_emoji": "✔️",
    "progress_step": 2,
    "created_at": "2025-11-24T10:30:00",
    "updated_at": "2025-11-24T10:35:00",
    "total_amount": 1500.00,
    "payment_method": "cod",
    "customer_name": "Juan Dela Cruz",
    "rider_id": 45,
    "seller_confirmed_rider": true,
    "buyer_approved_rider": false
  },
  "items": [...],
  "timeline": {...}
}
```

### GET /seller/orders

**Changes:**
- Added `rider_id`, `seller_confirmed_rider`, `buyer_approved_rider` to SELECT

**New Query Fields:**
```sql
SELECT
  ...
  o.rider_id,
  o.seller_confirmed_rider,
  o.buyer_approved_rider,
  ...
```

---

## Frontend Integration Points

### Checkout Page (`checkout.html`)

**Function:** `confirmAndPlaceOrder()`
```javascript
async function confirmAndPlaceOrder() {
  // 1. Validate form
  // 2. Get cart items
  // 3. Calculate totals
  // 4. POST to /api/place-order
  // 5. On success: Clear cart, show alert, redirect to /order-confirmation/{order_number}
}
```

### Order Confirmation Page (`order_confirmation.html`)

**Function:** `updateOrderStatus()`
```javascript
async function updateOrderStatus() {
  // 1. GET /api/order-status/{order_id}
  // 2. Update progress timeline
  // 3. Check if rider_id exists and seller_confirmed_rider = true
  // 4. If true: Show "Approve Rider for Delivery" button
}
```

**Function:** `showRiderApprovalModal(riderId, orderId)`
```javascript
async function showRiderApprovalModal(riderId, orderId) {
  // 1. GET /api/rider-details/{riderId}
  // 2. Display modal with rider info
  // 3. Set global vars: currentRiderId, currentOrderIdForRider
}
```

**Function:** `approveDelivery()`
```javascript
async function approveDelivery() {
  // 1. POST /api/approve-rider-delivery with currentOrderIdForRider and currentRiderId
  // 2. Show success message
  // 3. Close modal
  // 4. Refresh order status
}
```

### Seller Dashboard (`SellerDashboard.html`)

**Function:** `confirmOrder(orderId)`
```javascript
async function confirmOrder(orderId) {
  // 1. GET confirmation from user
  // 2. POST /seller/confirm-order with order_id
  // 3. Reload orders list
}
```

**Function:** `approveRiderForDelivery(orderId, riderId)`
```javascript
async function approveRiderForDelivery(orderId, riderId) {
  // 1. GET /api/rider-details/{riderId}
  // 2. Create and display modal with rider details
  // 3. Set onclick for modal button to call completeRiderApproval()
}
```

**Function:** `completeRiderApproval(orderId, riderId)`
```javascript
async function completeRiderApproval(orderId, riderId) {
  // 1. POST /seller/approve-rider-for-delivery
  // 2. Reload orders list
}
```

---

## State Diagram

```
┌─────────┐
│ PENDING │ (Order created, waiting for seller)
└────┬────┘
     │ (Seller clicks "Confirm Order")
     ↓
┌─────────────────────────────┐
│ CONFIRMED                   │
│ seller_confirmed_rider: F   │ (Order confirmed, waiting for rider)
│ buyer_approved_rider: F     │
└────┬────────────────────────┘
     │ (Rider assigns self - rider_id set by rider app)
     ├─ [polling detects rider_id]
     ├─ "Approve Rider" button appears on seller dashboard
     │
     │ (Seller clicks "Approve Rider")
     ↓
┌─────────────────────────────┐
│ CONFIRMED                   │
│ seller_confirmed_rider: T   │ (Seller approved, waiting for buyer)
│ buyer_approved_rider: F     │
└────┬────────────────────────┘
     │ [polling detects seller_confirmed_rider = T]
     ├─ "Approve Rider for Delivery" button appears on buyer page
     │
     │ (Buyer clicks "Approve Rider for Delivery")
     ↓
┌─────────────────────────────┐
│ CONFIRMED                   │
│ seller_confirmed_rider: T   │ (Both approved, ready for delivery)
│ buyer_approved_rider: T     │
└────┬────────────────────────┘
     │ (Manual status update or automatic)
     ↓
┌──────────────┐
│ PROCESSING   │ (Being prepared)
└────┬─────────┘
     ↓
┌──────────┐
│ SHIPPED  │ (In transit)
└────┬─────┘
     ↓
┌─────────────┐
│ DELIVERED   │ (Complete)
└─────────────┘
```

---

## Error Handling

### Common Error Scenarios

**Scenario 1: Seller not owner of order**
```json
{
  "success": false,
  "error": "Order not found or you do not have permission"
}
```
Status: 403

**Scenario 2: Missing required parameter**
```json
{
  "success": false,
  "error": "Missing order_id or rider_id"
}
```
Status: 400

**Scenario 3: Rider not found**
```json
{
  "success": false,
  "error": "Rider not found"
}
```
Status: 404

**Scenario 4: User not logged in**
```json
{
  "success": false,
  "error": "Not logged in"
}
```
Status: 401

---

## Database Queries

### Get orders with rider info
```sql
SELECT 
  o.id, o.order_number, o.order_status,
  o.rider_id, o.seller_confirmed_rider, o.buyer_approved_rider,
  u.first_name as rider_first_name, u.last_name as rider_last_name
FROM orders o
LEFT JOIN users u ON o.rider_id = u.id
WHERE o.id = ? AND o.user_id = ?
```

### Find orders awaiting seller approval
```sql
SELECT * FROM orders
WHERE order_status = 'confirmed'
AND rider_id IS NOT NULL
AND seller_confirmed_rider = FALSE
```

### Find orders awaiting buyer approval
```sql
SELECT * FROM orders
WHERE order_status = 'confirmed'
AND seller_confirmed_rider = TRUE
AND buyer_approved_rider = FALSE
```

---

## Performance Considerations

1. **Indexes Added:**
   - `idx_rider (rider_id)` - For quick lookup of orders by rider

2. **Polling Interval:** 30 seconds on buyer's order confirmation page
   - Reduces server load vs. checking every few seconds
   - Adequate for non-real-time updates

3. **Query Optimization:**
   - LEFT JOIN with riders table for potential expansion
   - DISTINCT clause only when necessary (seller orders query)

---

## Security Considerations

1. **Ownership Verification:** All endpoints verify user owns the order before allowing updates

2. **Role Checking:** Seller endpoints verify user is a seller before proceeding

3. **SQL Injection:** All queries use parameterized queries (%s placeholder)

4. **Session Management:** All endpoints require `session.get('logged_in')`

5. **Data Validation:** All inputs validated before database operations

---

## Testing Utilities

### SQL Test Queries

```sql
-- Check order state
SELECT id, order_number, order_status, rider_id, seller_confirmed_rider, buyer_approved_rider
FROM orders
WHERE id = 1;

-- Simulate rider assignment
UPDATE orders
SET rider_id = 5, updated_at = NOW()
WHERE id = 1;

-- Check rider exists
SELECT id, first_name, last_name, phone FROM users WHERE id = 5 AND role = 'rider';

-- Reset order for retesting
UPDATE orders
SET 
  seller_confirmed_rider = FALSE,
  buyer_approved_rider = FALSE,
  rider_id = NULL,
  order_status = 'pending',
  updated_at = NOW()
WHERE id = 1;
```

---

## Debugging Tips

1. **Check Browser Console** for JavaScript errors
2. **Check Network Tab** in DevTools to see API responses
3. **Check Server Logs** for any 500 errors
4. **Verify Session** with `print(session)` in backend
5. **Test Endpoints Directly** with curl or Postman
6. **Check Database** manually to verify data updates

---

## Related Documentation

- `MULTI_STEP_ORDER_CONFIRMATION_FLOW.md` - High-level overview
- `ORDER_CONFIRMATION_QUICK_GUIDE.md` - Quick start guide
- Code comments in `checkout.html`, `order_confirmation.html`, `SellerDashboard.html`
- Flask route docstrings in `app.py`
