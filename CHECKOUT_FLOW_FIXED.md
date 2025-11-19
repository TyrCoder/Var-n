# Checkout Flow - Complete Fix & Guide

## Error Fixed ✅
**"Unable to validate cart items. Please try again."**

This error was caused by:
1. **Incorrect SQL query** - Looking for `stock_quantity` and `image_url` directly in `products` table
2. **Wrong column references** - Using `business_name` instead of `store_name` for seller
3. **Missing `archive_status` column** - Required for filtering active products

---

## Changes Made

### 1. Fixed SQL Query in `/api/validate-cart` (app.py)
**Before:**
```sql
SELECT p.id, p.name, p.price, p.image_url, p.stock_quantity, p.is_active, 
       s.business_name as seller_name, s.id as seller_id
FROM products p
JOIN sellers s ON p.seller_id = s.id
WHERE p.id = %s AND p.is_active = 1
```

**After:**
```sql
SELECT p.id, p.name, p.price, p.is_active,
       pi.image_url,
       i.stock_quantity,
       s.store_name as seller_name, s.id as seller_id
FROM products p
LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
LEFT JOIN inventory i ON p.id = i.product_id
JOIN sellers s ON p.seller_id = s.id
WHERE p.id = %s AND p.is_active = 1
```

**Why:**
- Images are in `product_images` table (LEFT JOIN to get primary image)
- Stock is in `inventory` table (LEFT JOIN for optional match)
- Seller uses `store_name` field (not `business_name`)

### 2. Added `archive_status` Column
Added to `products` table schema:
```sql
archive_status VARCHAR(50) DEFAULT 'active'
```

### 3. Improved Error Logging (checkout.html)
- Added console logging at each validation step 📤 📥
- Better fallback mechanism if validation fails
- No more silent failures

---

## Complete Checkout Flow

### 1. User Adds Items to Cart
```javascript
// Items stored in localStorage
cart = [
  {
    id: 1,
    name: "Product Name",
    price: 500,
    quantity: 2,
    size: "M",
    color: "Black"
  }
]
```

### 2. User Goes to Checkout
```
/checkout route → checkout.html loads
```

### 3. Cart Validation Happens Automatically
```
📤 POST /api/validate-cart
├─ Sends items to backend
├─ Backend checks database for:
│  ├─ Product exists
│  ├─ Product is active (is_active = 1)
│  ├─ Gets current price
│  ├─ Gets product image (primary only)
│  └─ Checks inventory stock
└─ Returns validated items with database info
```

**Expected Response:**
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "name": "AIRism Cotton Crew Neck T-Shirt",
      "price": 1599,
      "quantity": 1,
      "image_url": "/static/images/products/1_1762873464835_goods_474244.avif",
      "seller_id": 1,
      "seller_name": "MNL",
      "stock_available": 50,
      "size": "M",
      "color": "Black"
    }
  ]
}
```

### 4. Order Summary Displays
Shows:
- Product details with images
- Quantities
- Individual prices
- Subtotal
- Shipping fee (₱100)
- **Total**

### 5. User Fills Checkout Form
- First Name
- Last Name
- Email
- Phone
- Address
- Barangay
- City
- Province
- Postal Code
- Country (default: Philippines)
- Special Notes (optional)

### 6. User Selects Payment Method
- Cash on Delivery (COD)
- GCash
- PayMaya
- Credit/Debit Card

### 7. User Clicks "Place Order"
```
📤 POST /api/place-order
├─ Validates form data
├─ Creates address record
├─ Creates order record
├─ Creates order items
├─ Updates inventory (reduces stock)
├─ Creates transaction record
├─ Creates shipment record
├─ Logs activity
└─ Returns order confirmation
```

**Expected Response:**
```json
{
  "success": true,
  "order_number": "ORD-1762873464-1234",
  "message": "Order placed successfully"
}
```

### 8. Order Confirmation Page
Displays:
- ✅ Success message
- Order number
- Items ordered
- Total amount
- Shipping address
- Payment method info
- Action buttons:
  - "Track Order"
  - "Continue Shopping"

### 9. Cart Cleared
```javascript
localStorage.removeItem('varon_cart');
```

---

## Database Schema (Key Tables)

### `products`
```
id, name, price, is_active, archive_status, seller_id, category_id, ...
```
- `is_active = 1` → Product is active/approved
- `archive_status = 'active'` → Product not archived

### `product_images`
```
id, product_id, image_url, is_primary (1 = main image)
```

### `inventory`
```
id, product_id, stock_quantity, reserved_quantity
```

### `orders`
```
id, order_number, user_id, seller_id, shipping_address_id,
subtotal, shipping_fee, total_amount, payment_method, order_status, ...
```

### `order_items`
```
id, order_id, product_id, quantity, unit_price, size, color, ...
```

### `addresses`
```
id, user_id, full_name, phone, street_address, barangay, 
city, province, postal_code, country, address_type, ...
```

---

## Testing Checkout Flow

### Step 1: Add Product to Cart
1. Browse products
2. Select size & color
3. Click "Add to Cart"
4. Verify item in cart (cart icon shows count)

### Step 2: Go to Checkout
1. Click "Cart" button
2. Click "Checkout"
3. Observe console for validation logs 📤 📥

### Step 3: Verify Cart Validation
Open browser console (F12) and look for:
```
📤 Sending cart for validation: [...]
📥 Validation response status: 200
📥 Validation response data: {...}
✅ Cart validated successfully: [...]
```

### Step 4: Fill Checkout Form
- Complete all required fields
- Verify address is correct
- Select payment method

### Step 5: Place Order
- Click "Place Order"
- Verify in console:
  ```
  ✅ Order placed successfully
  Redirecting to confirmation...
  ```

### Step 6: Verify Order in Database
```sql
-- Check order was created
SELECT * FROM orders WHERE order_number = 'ORD-...';

-- Check order items
SELECT * FROM order_items WHERE order_id = <id>;

-- Check inventory was updated
SELECT * FROM inventory WHERE product_id = <id>;
```

---

## Common Issues & Fixes

### Issue: "Unable to validate cart items"
**Solution:**
1. Check if products exist in database: `SELECT * FROM products;`
2. Check if products have `is_active = 1`: `SELECT * FROM products WHERE is_active = 0;`
3. Check if inventory exists: `SELECT * FROM inventory WHERE product_id = <id>;`
4. Check if product images exist: `SELECT * FROM product_images WHERE product_id = <id>;`
5. Open browser console to see specific error

### Issue: Empty Cart on Checkout
**Solution:**
1. Check `localStorage` for `varon_cart` key
2. Verify cart structure in console: `JSON.parse(localStorage.getItem('varon_cart'))`
3. Add a test product and try again

### Issue: "Database connection failed"
**Solution:**
1. Verify MySQL is running
2. Check connection string in `app.py`
3. Verify user/password credentials
4. Check database exists: `SHOW DATABASES;`

### Issue: Inventory Not Updating
**Solution:**
1. Verify `inventory` table has stock: `SELECT * FROM inventory;`
2. Check `UPDATE` query is not failing
3. Verify product_id matches between orders and inventory

---

## Console Logging Guide

### ✅ Success Logs
```
✅ Cart validated successfully: [items]
✅ Order placed successfully
```

### 📤 Request Logs
```
📤 Sending cart for validation: [items]
📤 POST /api/place-order
```

### 📥 Response Logs
```
📥 Validation response status: 200
📥 Validation response data: {...}
```

### ❌ Error Logs
```
❌ Failed to validate cart: [error]
❌ Error validating cart: [error]
❌ Failed to place order: [error]
```

### ⚠️ Warning Logs
```
⚠️ Falling back to localStorage cart
```

---

## API Endpoints Reference

### `POST /api/validate-cart`
Validates cart items against database
- **Request:** `{ items: [{id, quantity, size, color}, ...] }`
- **Response:** `{ success: true, items: [...] }`
- **Status:** 200 (success), 400 (empty), 401 (not logged in), 500 (error)

### `POST /api/place-order`
Creates order in database
- **Request:** 
  ```json
  {
    "shipping": { firstName, lastName, phone, address, city, ... },
    "payment_method": "cod",
    "items": [...],
    "subtotal": 1599,
    "shipping_fee": 100,
    "total": 1699
  }
  ```
- **Response:** `{ success: true, order_number: "ORD-..." }`
- **Status:** 200 (success), 400 (validation), 401 (not logged in), 500 (error)

---

## Complete Checkout Checklist

- ✅ Products have `is_active = 1`
- ✅ Products have images in `product_images` table
- ✅ Products have inventory in `inventory` table
- ✅ Seller has correct `store_name` (not `business_name`)
- ✅ Cart validation working (check console logs)
- ✅ Order submission working
- ✅ Database updated with order data
- ✅ Inventory decreased after order
- ✅ User redirected to confirmation page
- ✅ Cart cleared from localStorage

**All fixed! ✅ Your checkout flow should now work perfectly.**
