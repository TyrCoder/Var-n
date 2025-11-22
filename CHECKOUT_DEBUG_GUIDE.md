# Checkout Flow Debug Guide
# ========================

## Issue Identified:
The cart was not being cleared from the **database** after checkout, only from localStorage.
This caused orders to appear to not process because the cart remained populated in the database.

## Fix Applied:
Added database cart clearing in checkout.html after successful order placement.

## How to Test:
1. Open browser console (F12)
2. Add items to cart as a buyer
3. Go to checkout page
4. Fill in shipping information
5. Click "Place Order"
6. Watch the console logs for the following sequence:

### Expected Console Output:
```
🛒 Place Order clicked
📦 Validated cart: [array of items]
🏠 Selected address ID: [number or null]
💳 Selected payment method: cod
📤 Sending order data: {shipping, payment_method, items, etc}
📥 Order response status: 200
📥 Order response data: {success: true, order_number: "ORD-..."}
✅ Order placed successfully! Order number: ORD-...
Cart cleared from database: {success: true}
```

### If There's an Error:
Look for these patterns:
- ❌ Error placing order: [error message]
- 📥 Order response data: {success: false, message: "..."}
- ❌ Failed to validate cart: [error]

## Common Issues & Solutions:

### Issue: "Your cart is empty"
**Cause**: Cart not loaded from database
**Check**: Look at network tab for `/api/cart/get` response
**Solution**: Ensure user is logged in and has items in cart table

### Issue: "Please select a shipping address"
**Cause**: Neither saved address selected nor manual form filled
**Check**: Console log shows `selectedAddressId: null` and form display is 'none'
**Solution**: Either select saved address or fill manual form

### Issue: Order created but cart not cleared
**Cause**: `/api/cart/clear` endpoint failing
**Check**: Network tab for `/api/cart/clear` request/response
**Solution**: Check database connection and user_id in session

### Issue: Redirect happens but cart still has items
**Cause**: Race condition - redirect before cart clear completes
**Solution**: Already fixed - cart clear is async and doesn't block redirect

## Database Queries to Check:

### Check if cart was cleared:
```sql
SELECT * FROM cart WHERE user_id = [your_user_id];
```
Should be empty after checkout.

### Check if order was created:
```sql
SELECT * FROM orders WHERE user_id = [your_user_id] ORDER BY created_at DESC LIMIT 1;
```
Should show your latest order.

### Check order items:
```sql
SELECT oi.*, p.name FROM order_items oi
JOIN orders o ON oi.order_id = o.id
LEFT JOIN products p ON oi.product_id = p.id
WHERE o.user_id = [your_user_id]
ORDER BY o.created_at DESC;
```
Should show items from your order.

## Files Modified:
- templates/pages/checkout.html
  - Added database cart clearing after order success
  - Added comprehensive console logging throughout placeOrder()
  - Added logging to cart validation
  - Added logging to order submission

## What to Monitor:
1. Browser console for debug logs
2. Network tab for API calls:
   - /api/cart/get
   - /api/validate-cart
   - /api/place-order
   - /api/cart/clear
3. Server console for backend errors
4. Database for actual data changes
