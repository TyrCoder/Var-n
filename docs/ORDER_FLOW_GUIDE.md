# Order Management & Tracking System - Complete Flow Guide

## Overview
This document explains the complete order flow from customer checkout to order delivery, with real-time status tracking.

---

## 1. Customer Checkout Flow

### Checkout Process
1. **Customer adds products to cart** → Browse products → Click "Add to Cart"
2. **Customer proceeds to checkout** → Cart icon → Click "Checkout"
3. **Checkout page** (`/checkout`)
   - Validates cart items against current database prices and stock
   - Customer enters shipping information
   - Customer selects payment method (COD, GCash, PayMaya, Card)
   - Customer reviews order summary

### Place Order
- **Endpoint**: `POST /api/place-order`
- **Creates**:
  - Order record with `order_status = 'pending'`
  - Order items linked to products
  - Shipping address
  - Transaction record
  - Shipment record
  - Activity log entry

**Order Status at Creation**: `pending`

---

## 2. Seller Order Management

### Seller Dashboard - Orders Page
- **Location**: Seller Dashboard → Sidebar → "Orders"
- **Access**: `GET /seller/orders`

### Available Features
1. **Order Viewing**
   - View all orders for seller's products
   - See customer name, order total, item count
   - Date/time order was placed

2. **Order Filtering** (5 Status Filters)
   - All Orders
   - Pending (⏳) - Not yet confirmed
   - Confirmed (✔️) - Ready to process
   - Processing (🔄) - Being prepared
   - Shipped (📦) - On the way

3. **Order Status Update**
   - Click "Update" button on any order
   - Select new status from dropdown
   - Status options: pending → confirmed → processing → shipped → delivered
   - Change applies immediately to database

### Update Status Endpoint
- **Endpoint**: `POST /seller/update-order-status`
- **Parameters**: 
  - `order_id`: The order to update
  - `new_status`: New status value
- **Validation**: 
  - Seller must own the product in the order
  - Status must be a valid enum value
  - Updates `order_status` and `updated_at` timestamp

---

## 3. Customer Order Tracking

### After Checkout
**Customer sees**:
1. Order confirmation page (`/order-confirmation/{order_number}`)
2. Order number and summary
3. **Live Order Status Tracker** with visual progress bar

### Order Status Progress Timeline
```
⏳ Pending → ✔️ Confirmed → 🔄 Processing → 📦 Shipped → ✅ Delivered
```

### Real-Time Updates
- Progress bar updates every **30 seconds**
- Automatically reflects seller's status changes
- Shows appropriate message for each status:
  - "Seller will update your order status soon..."
  - "Seller has confirmed your order!"
  - "Order is being prepared for shipment..."
  - "Your order has been shipped!"
  - "Your order has been delivered!"

### My Orders Section
- **Location**: Buyer Dashboard → Navigation → "My Orders"
- **Shows**:
  - All customer's orders
  - Order number and date
  - Order status with emoji badge
  - Store name
  - Item count
  - Total amount
  - "View Details" link to confirmation page

### Status Indicators
| Status | Icon | Background | Meaning |
|--------|------|-----------|---------|
| Pending | ⏳ | Yellow | Awaiting seller confirmation |
| Confirmed | ✔️ | Blue | Seller confirmed, preparing |
| Processing | 🔄 | Orange | Being packaged/prepared |
| Shipped | 📦 | Purple | On the way to customer |
| Delivered | ✅ | Green | Successfully delivered |
| Cancelled | ❌ | Red | Order was cancelled |
| Returned | ↩️ | Purple | Order was returned |

---

## 4. API Endpoints Summary

### For Sellers
- **GET `/seller/orders`** - Fetch all seller's orders with details
- **POST `/seller/update-order-status`** - Update order status

### For Buyers
- **GET `/api/order-status/{order_id}`** - Get order details and current status
- **GET `/api/user-orders-detailed`** - Get all user's orders with status info

### For Checkout
- **POST `/api/validate-cart`** - Validate cart items and get current prices
- **POST `/api/place-order`** - Create new order

---

## 5. Order Status Flow Diagram

```
Customer Checkout
        ↓
    ORDER CREATED (pending)
        ↓
    [Seller Dashboard]
        ↓
Seller Updates Status
        ↓
confirmed → processing → shipped → delivered
        ↓
    [Buyer Dashboard]
        ↓
Customer Sees Progress
        ↓
Real-time notifications every 30 seconds
        ↓
Order Delivered (Green checkmark)
```

---

## 6. Database Tables Involved

### Orders Table
- `id`: Order ID
- `order_number`: Unique order reference (ORD-{timestamp}-{random})
- `user_id`: Customer ID
- `seller_id`: Seller ID
- `order_status`: Current status (enum: pending, confirmed, processing, shipped, delivered, cancelled, returned)
- `total_amount`: Order total
- `created_at`: Order placed time
- `updated_at`: Last status update time
- `payment_method`: Payment type (COD, GCash, PayMaya, Card)

### Order Items Table
- `order_id`: Link to order
- `product_id`: Product ordered
- `product_name`: Name snapshot
- `quantity`: Amount ordered
- `unit_price`: Price at purchase time
- `size`: Selected size (if applicable)
- `color`: Selected color (if applicable)

---

## 7. Key Features

✅ **Multi-Seller Support** - Each seller only sees their orders
✅ **Real-Time Updates** - Buyers see status changes immediately
✅ **Status Progression** - Logical order progression (can't skip steps)
✅ **Timestamp Tracking** - Track when each update happened
✅ **Security** - Seller ownership verification on all updates
✅ **User-Friendly** - Clear status indicators and messages
✅ **Mobile Responsive** - Works on all devices

---

## 8. Testing the Flow

### Test Scenario 1: Place Order
1. Login as buyer
2. Add product to cart
3. Go to checkout
4. Enter shipping info
5. Select payment method
6. Click "Place Order"
7. See order confirmation with progress tracker

### Test Scenario 2: Update Status
1. Login as seller
2. Go to Orders page
3. Click filter (e.g., "Pending")
4. Click "Update" on an order
5. Select new status
6. Confirm change

### Test Scenario 3: Check Real-Time Update
1. Open buyer's order confirmation page
2. Open seller's Orders page in another tab
3. Update status in seller tab
4. Watch buyer tab update automatically (within 30 seconds)

---

## 9. Troubleshooting

**Problem**: Order not appearing in seller's list
- **Solution**: Verify seller_id matches product's seller_id

**Problem**: Status update fails
- **Solution**: Check that new status is valid enum value

**Problem**: Buyer not seeing status updates
- **Solution**: Check browser console for errors, verify order exists

**Problem**: Real-time updates not showing
- **Solution**: Page polls every 30 seconds, refresh manually if needed

---

## 10. Future Enhancements

Possible improvements:
- [ ] Email notifications when status changes
- [ ] SMS notifications for shipment
- [ ] Estimated delivery date calculation
- [ ] Tracking number integration
- [ ] Return request workflow
- [ ] Rating & review system post-delivery
- [ ] Bulk status updates
- [ ] Order export (CSV, PDF)
