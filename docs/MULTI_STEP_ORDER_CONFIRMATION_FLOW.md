# Multi-Step Order Confirmation Flow - Implementation Summary

## Overview
This document describes the implementation of a multi-step order confirmation flow that replaces the previous direct order placement modal with a sequential confirmation process.

## Flow Overview

### Step 1: Buyer Confirms Order (Checkout Page)
- **Before**: "Place Order" button directly created the order
- **After**: "Confirm Order" button initiates the confirmation process
- **Action**: Buyer clicks "Confirm Order" on checkout page
- **Result**: Order status set to `pending`, user redirected to order confirmation page with message "Waiting for seller confirmation"

### Step 2: Seller Confirms Order (Seller Dashboard)
- **Display**: Pending orders show "Confirm Order" button
- **Action**: Seller clicks "Confirm Order" button
- **Result**: 
  - Order status changes to `confirmed`
  - Message updates to "Waiting for a rider to accept..."
  - Button disappears, order moves to confirmed section

### Step 3: Rider Accepts Order (External System)
- **Assumption**: Rider app/system accepts orders and updates the order with `rider_id`
- **Status**: Order shows `confirmed` + `rider_id` is set
- **Trigger**: "Approve Rider" button appears on seller dashboard

### Step 4: Seller Approves Rider (Seller Dashboard)
- **Display**: When rider is assigned + order is confirmed, "Approve Rider" button appears
- **Action**: Seller clicks "Approve Rider" button
- **Modal**: Shows rider details:
  - Rider photo (profile image)
  - Rider name
  - Rider phone number
  - Rider rating
  - Verification badge
- **Approve Button**: "Approve for Delivery" button in modal
- **Result**: 
  - Sets `seller_confirmed_rider = TRUE`
  - Buyer sees "Approve Rider" button on order confirmation page

### Step 5: Buyer Approves Rider (Order Confirmation Page)
- **Display**: When seller approved rider, "Approve Rider for Delivery" button appears
- **Action**: Buyer clicks button
- **Modal**: Same as seller view showing rider details
- **Approve Button**: "Approve for Delivery" button
- **Result**: 
  - Sets `buyer_approved_rider = TRUE`
  - Order proceeds to delivery

## Database Changes

### New Columns Added to `orders` Table
```sql
ALTER TABLE orders
ADD COLUMN rider_id INT NULL,
ADD COLUMN seller_confirmed_rider BOOLEAN DEFAULT FALSE,
ADD COLUMN buyer_approved_rider BOOLEAN DEFAULT FALSE,
ADD FOREIGN KEY (rider_id) REFERENCES users(id) ON DELETE SET NULL,
ADD INDEX idx_rider (rider_id);
```

### Column Descriptions
- **rider_id**: ID of the assigned rider (set by external system)
- **seller_confirmed_rider**: Seller has approved the assigned rider
- **buyer_approved_rider**: Buyer has approved the assigned rider

## File Changes

### 1. `templates/pages/checkout.html`
**Changes:**
- Button text changed from "Place Order" to "Confirm Order"
- Button onclick changed from `placeOrder()` to `confirmAndPlaceOrder()`
- Success message updated to indicate order is confirmed, not placed

**New Function:** `confirmAndPlaceOrder()`
- Validates form and cart
- Sends order data to `/api/place-order`
- Shows confirmation message
- Redirects to order confirmation page

### 2. `templates/pages/order_confirmation.html`
**Changes:**
- Added new "Approve Rider for Delivery" button in action buttons section
- Added rider approval modal with rider details display
- Updated order status messages to include rider approval step
- Added logic to show/hide approve button based on order status

**New Functions:**
- `showRiderApprovalModal(riderId, orderId)`: Displays rider details in modal
- `closeRiderModal()`: Closes the modal
- `approveDelivery()`: Sends approval to backend
- `handleApproveRiderClick()`: Fetches rider info and shows modal
- Updated `updateOrderStatus()`: Checks for rider assignment and shows button

**New Modal:**
- Shows rider photo, name, phone, rating
- Displays verification badge
- "Approve for Delivery" button triggers `/api/approve-rider-delivery`

### 3. `templates/pages/SellerDashboard.html`
**Changes:**
- Updated order action buttons logic:
  - Pending orders: Show "Confirm Order" button
  - Confirmed orders with assigned rider: Show "Approve Rider" button
  - Other states: Show "Update" button
- Added rider details modal (similar to buyer view)

**New Functions:**
- `confirmOrder(orderId)`: Confirms order from pending state
- `approveRiderForDelivery(riderId, orderId)`: Shows rider modal and approval flow
- `completeRiderApproval(orderId, riderId)`: Sends approval to backend

**Updated Query:**
- Seller orders query now includes `rider_id`, `seller_confirmed_rider`, `buyer_approved_rider` fields

### 4. `app.py` - Backend Endpoints

**Database Changes:**
- Updated `init_db()` to create orders table with new columns

**New Endpoints Added:**

#### `/seller/confirm-order` (POST)
- Confirms order from pending to confirmed status
- Checks seller ownership
- Updates order status to 'confirmed'

#### `/seller/approve-rider-for-delivery` (POST)
- Seller approves assigned rider
- Sets `seller_confirmed_rider = TRUE`
- Validates seller ownership

#### `/api/rider-details/<rider_id>` (GET)
- Returns rider details for modal display
- Returns: first_name, last_name, phone, rating, profile_image_url
- Used by both buyer and seller modals

#### `/api/order-rider-info/<order_id>` (GET)
- Gets rider ID for an order
- Verifies buyer ownership
- Returns: rider_id

#### `/api/approve-rider-delivery` (POST)
- Buyer approves rider for delivery
- Sets `buyer_approved_rider = TRUE`
- Validates buyer ownership

**Updated Endpoints:**

#### `/seller/orders` (GET)
- Query updated to include:
  - rider_id
  - seller_confirmed_rider
  - buyer_approved_rider

#### `/api/order-status/<order_id>` (GET)
- Query updated to include:
  - rider_id
  - seller_confirmed_rider
  - buyer_approved_rider
- Used by order confirmation page for status updates

## UI Behavior Timeline

```
1. CHECKOUT PAGE
   ↓
   Button: "Confirm Order"
   ↓
2. ORDER CONFIRMATION PAGE (Status: pending → confirmed)
   Status Message: "Seller has confirmed your order! Waiting for a rider to accept..."
   ↓
   [Rider accepts order in rider app - rider_id is set]
   ↓
3. SELLER DASHBOARD (Status: confirmed)
   Button: "Approve Rider" (visible when rider_id is set)
   ↓
   [Seller clicks "Approve Rider"]
   Modal: Shows rider details
   ↓
   [Seller clicks "Approve for Delivery"]
   seller_confirmed_rider = TRUE
   ↓
4. ORDER CONFIRMATION PAGE (Status: still confirmed)
   Button: "Approve Rider for Delivery" (now visible)
   ↓
   [Buyer clicks "Approve Rider for Delivery"]
   Modal: Shows rider details
   ↓
   [Buyer clicks "Approve for Delivery"]
   buyer_approved_rider = TRUE
   ↓
5. ORDER DELIVERY PROCEEDS
```

## Status Transitions

| Current Status | Trigger | New Status |
|---|---|---|
| pending | Seller confirms | confirmed |
| confirmed + rider_id | Seller approves | confirmed (seller_confirmed_rider=TRUE) |
| confirmed + seller_confirmed | Buyer approves | confirmed (buyer_approved_rider=TRUE) |
| confirmed + buyer_approved | Manual or auto transition | processing/shipped/delivered |

## Testing Checklist

- [ ] Checkout page shows "Confirm Order" button
- [ ] Click confirms order and redirects to confirmation page
- [ ] Seller dashboard shows pending orders with "Confirm Order" button
- [ ] Seller can confirm order
- [ ] Order status updates in seller dashboard
- [ ] When rider_id is assigned, "Approve Rider" button appears on seller dashboard
- [ ] Seller can click "Approve Rider" and see modal with rider details
- [ ] Seller can approve rider from modal
- [ ] Buyer sees "Approve Rider for Delivery" button on order confirmation page
- [ ] Buyer can click button and see modal with rider details
- [ ] Buyer can approve rider from modal
- [ ] Status updates propagate to both seller and buyer views in real-time

## API Response Examples

### GET /api/rider-details/5
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

### POST /seller/confirm-order
```json
{
  "success": true,
  "message": "Order confirmed! Waiting for a rider to accept."
}
```

### POST /api/approve-rider-delivery
```json
{
  "success": true,
  "message": "Rider approved for delivery!"
}
```

## Notes

1. **Rider Assignment**: The system assumes riders accept orders through a separate rider app/interface. The order's `rider_id` is updated when a rider accepts.

2. **Polling**: Order confirmation page polls `/api/order-status` every 30 seconds to check for updates (rider assignment, etc.)

3. **Error Handling**: All endpoints include proper error handling with appropriate HTTP status codes (401 for unauthorized, 403 for forbidden, 404 for not found, 400 for bad requests)

4. **Security**: All endpoints verify user ownership of orders before allowing modifications

5. **Database Indexes**: Added index on `rider_id` for faster queries

## Migration Steps

1. Run the SQL migration script to add new columns:
   ```bash
   mysql -u root -p varon < migrations/add_order_confirmation_columns.sql
   ```

2. No code changes needed if using new initialization (existing databases need migration)

3. Restart Flask app to load new endpoints

## Future Enhancements

- Email notifications at each step
- SMS notifications for important updates
- Real-time WebSocket updates instead of polling
- Automatic rider assignment based on proximity
- Customer feedback at each step
- Admin dashboard to monitor approval flow metrics
